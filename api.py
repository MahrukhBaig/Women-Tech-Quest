"""FastAPI Backend Application wrapping the billdecoder core library."""

import json
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from billdecoder.config import settings
from billdecoder.image_prep import validate_image_bytes
from billdecoder.llm_client import GeminiClient, get_llm_client
from billdecoder.models import Level1Bill, Level2AnswersResponse
from billdecoder.pipeline import FALLBACK_L2_ANSWER, PipelineTracker, process_bill
from billdecoder.postprocessing import sanitize_no_pii
from billdecoder.prompts import build_level2_prompt

logger = logging.getLogger("billdecoder.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app = FastAPI(
    title="WTQ Utility Bill Decoder",
    description="AI-powered assistant for decoding Pakistani electricity bills",
    version="1.0.0",
)

# Strict CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows local dev and static UI
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to every response."""
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# In-memory per-IP request tracking for rate limiting (e.g. 30 requests/minute per client IP)
client_request_history: Dict[str, List[float]] = {}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    import time
    now = time.time()
    history = client_request_history.get(client_ip, [])
    # Keep last 60 seconds
    history = [t for t in history if now - t < 60.0]
    if len(history) >= 40:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please slow down."},
        )
    history.append(now)
    client_request_history[client_ip] = history
    return await call_next(request)


@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint exposing system status and allowed model ID."""
    return {
        "status": "healthy",
        "model_provider": settings.model_provider,
        "model_name": settings.model_name,
        "version": "1.0.0",
    }


class QuestionItem(BaseModel):
    question_id: str
    question: str


class AskQuestionRequest(BaseModel):
    bill_id: str
    question: str
    level1: Optional[Dict[str, Any]] = None
    stats: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, Any]]] = None


@app.post("/api/ask")
async def ask_question_endpoint(req: AskQuestionRequest):
    """Answer an ad-hoc customer question about a decoded bill using Gemini 3.5 Flash-Lite."""
    client = get_llm_client()
    stats = req.stats or {}
    l1_json = json.dumps(req.level1 or {}, indent=2)
    hist_json = json.dumps(req.history or [], indent=2)
    prompt = build_level2_prompt(
        bill_id=req.bill_id,
        questions=[{"question_id": "custom", "question": req.question}],
        level1_json_str=l1_json,
        history_json_str=hist_json,
        stats=stats,
    )
    try:
        resp_text = client.generate_structured(
            prompt=prompt,
            image=None,
            image_bytes=b"",
            response_schema=Level2AnswersResponse,
            force_no_cache=True,
        )
        data = json.loads(resp_text)
        parsed = Level2AnswersResponse.model_validate(data)
        answer = parsed.answers[0].answer if parsed.answers else "This could not be determined from the bill."
        return {"question": req.question, "answer": sanitize_no_pii(answer)}
    except Exception as ex:
        logger.warning("Custom question call failed: %s", ex)
        return {"question": req.question, "answer": "This could not be determined from the bill."}


@app.post("/api/decode")
async def decode_bill_endpoint(
    file: UploadFile = File(...),
    questions_json: Optional[str] = Form(None),
):
    """Secure bill upload and decoding endpoint:
    - Enforces 15 MB file size limit
    - Validates magic bytes (PNG/JPG only)
    - Processes with gemini-3.5-flash-lite
    - Cleans up all temp files immediately in finally block
    - Returns structured Level 1 JSON, calculator stats, and answers.
    """
    # 1. Read and validate content size
    max_bytes = settings.max_upload_bytes
    contents = bytearray()
    while chunk := await file.read(1024 * 64):
        contents.extend(chunk)
        if len(contents) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Uploaded file exceeds {max_bytes // (1024 * 1024)} MB limit.",
            )

    raw_bytes = bytes(contents)
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 2. Validate magic bytes
    try:
        detected_ext = validate_image_bytes(raw_bytes, max_size_bytes=max_bytes)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    # Derive bill_id securely (strip path traversal characters)
    original_filename = file.filename or f"bill_{uuid.uuid4().hex[:8]}"
    clean_name = Path(original_filename).stem
    # Remove any non-alphanumeric/underscore characters
    safe_bill_id = "".join(c for c in clean_name if c.isalnum() or c in ("-", "_")) or "bill"

    # 3. Parse optional questions list
    questions_list: List[Dict[str, str]] = []
    if questions_json:
        try:
            parsed_q = json.loads(questions_json)
            if isinstance(parsed_q, list):
                for item in parsed_q:
                    if isinstance(item, dict) and "question_id" in item and "question" in item:
                        questions_list.append({
                            "question_id": str(item["question_id"]),
                            "question": str(item["question"]),
                        })
        except Exception:
            logger.warning("Could not parse questions_json payload.")

    # Default questions if none provided
    if not questions_list:
        questions_list = [
            {"question_id": "Q1", "question": "Is this a net-metered (solar) connection or a standard connection? How did you tell?"},
            {"question_id": "Q2", "question": "How much of my bill is taxes?"},
            {"question_id": "Q3", "question": "How many months in my history went above 200 units?"},
            {"question_id": "Q4", "question": "What is the single largest charge on my bill?"},
            {"question_id": "Q5", "question": "When is the due date for this bill and how much should I pay?"},
        ]

    # 4. Execute pipeline with temporary file
    temp_dir = Path(tempfile.gettempdir())
    temp_file = temp_dir / f"wtq_{uuid.uuid4().hex}.{detected_ext}"

    try:
        temp_file.write_bytes(raw_bytes)
        client = get_llm_client()
        tracker = PipelineTracker()

        result = process_bill(
            image_input=raw_bytes,
            bill_id=safe_bill_id,
            questions=questions_list,
            client=client,
            tracker=tracker,
            force_no_cache=True,
        )

        qa_list = [
            {
                "question_id": q["question_id"],
                "question": q["question"],
                "answer": result["answers"].get(q["question_id"], FALLBACK_L2_ANSWER),
            }
            for q in questions_list
        ]

        return {
            "bill_id": safe_bill_id,
            "level1": result["level1_bill"].model_dump(),
            "level1_json_str": result["level1_json_str"],
            "stats": result["stats"],
            "history": [r.model_dump() for r in result["history"]],
            "answers": result["answers"],
            "qa_list": qa_list,
            "warnings": tracker.warnings,
            "fallbacks": tracker.fallbacks,
        }

    except Exception as ex:
        logger.error("Error processing bill %s: %s", safe_bill_id, ex, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the bill. Please ensure the image is a clear utility bill.",
        )
    finally:
        # Guarantee removal of uploaded file
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass


# Mount sample bills directory for easy UI testing
train_bills_dir = Path(__file__).resolve().parent / "train" / "bills"
if train_bills_dir.is_dir():
    app.mount("/sample-bills", StaticFiles(directory=str(train_bills_dir), check_dir=False), name="samples")

# Mount static directory for frontend
static_dir = Path(__file__).resolve().parent / "static"
if not static_dir.is_dir() and Path("static").is_dir():
    static_dir = Path("static").resolve()

if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_dir), check_dir=False), name="static")


@app.get("/")
async def serve_index():
    for candidate in [
        static_dir / "index.html",
        Path(__file__).resolve().parent / "static" / "index.html",
        Path("static/index.html").resolve(),
    ]:
        if candidate.is_file():
            return FileResponse(candidate)
    return {"message": "WTQ Utility Bill Decoder API"}


