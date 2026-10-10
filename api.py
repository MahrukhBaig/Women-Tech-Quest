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
from billdecoder.models import Level1Bill
from billdecoder.pipeline import PipelineTracker, process_bill
from billdecoder.postprocessing import sanitize_no_pii

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
    level1_data: Optional[Dict[str, Any]] = None


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
            {"question_id": "Q1", "question": "How much of my bill is taxes?"},
            {"question_id": "Q2", "question": "How many months in my history went above 200 units?"},
            {"question_id": "Q3", "question": "What is the single largest charge on my bill?"},
            {"question_id": "Q4", "question": "When is the due date and what amount is payable?"},
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

        return {
            "bill_id": safe_bill_id,
            "level1": result["level1_bill"].model_dump(),
            "level1_json_str": result["level1_json_str"],
            "stats": result["stats"],
            "history": [r.model_dump() for r in result["history"]],
            "answers": result["answers"],
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
train_bills_dir = Path(__file__).parent / "train" / "bills"
if train_bills_dir.is_dir():
    app.mount("/sample-bills", StaticFiles(directory=str(train_bills_dir)), name="samples")

# Mount static directory for frontend
static_dir = Path(__file__).parent / "static"
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    async def serve_index():
        index_file = static_dir / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)
        return {"message": "WTQ Utility Bill Decoder API"}

