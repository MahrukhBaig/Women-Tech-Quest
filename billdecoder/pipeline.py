"""End-to-end processing pipeline for bill decoding (Level 1 + History + Calculator + Level 2)."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

from billdecoder.calculator import compute_bill_stats
from billdecoder.history_extractor import extract_history_table
from billdecoder.image_prep import prepare_image
from billdecoder.llm_client import GeminiClient, get_llm_client
from billdecoder.models import (
    HistoryRow,
    Level1Bill,
    Level2AnswersResponse,
    Level2AnswerItem,
)
from billdecoder.postprocessing import postprocess_level1, sanitize_no_pii
from billdecoder.prompts import LEVEL1_SYSTEM_PROMPT, build_level2_prompt

logger = logging.getLogger("billdecoder.pipeline")

FALLBACK_L2_ANSWER = "This could not be determined from the bill."


class PipelineTracker:
    """Tracks run statistics: fallbacks, warnings, retries, tokens."""

    def __init__(self) -> None:
        self.fallbacks: List[Dict[str, str]] = []
        self.warnings: List[str] = []
        self.retries: int = 0

    def add_fallback(self, bill_id: str, item_type: str, reason: str) -> None:
        entry = {"bill_id": bill_id, "type": item_type, "reason": reason}
        self.fallbacks.append(entry)
        logger.warning("FALLBACK TRIGGERED: %s - %s (%s)", bill_id, item_type, reason)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)
        logger.warning(msg)

    def add_retry(self) -> None:
        self.retries += 1


def process_bill(
    image_input: Union[bytes, str, Path],
    bill_id: str,
    questions: List[Dict[str, str]],
    client: Optional[GeminiClient] = None,
    tracker: Optional[PipelineTracker] = None,
    force_no_cache: bool = False,
) -> Dict[str, Any]:
    """Execute the complete decoding pipeline for a single bill image.
    Never crashes on bad bills: logs, retries, and falls back gracefully.
    """
    if client is None:
        client = get_llm_client()
    if tracker is None:
        tracker = PipelineTracker()

    # Step 1: Read raw bytes & prepare image
    if isinstance(image_input, (str, Path)):
        p = Path(image_input)
        raw_bytes = p.read_bytes()
    else:
        raw_bytes = image_input

    try:
        prep_img = prepare_image(raw_bytes)
    except Exception as ex:
        tracker.add_warning(f"{bill_id}: Image preparation warning: {ex}")
        tracker.add_fallback(bill_id, "ImagePrep", str(ex))
        prep_img = None

    # Step 2: Level 1 Extraction
    level1_bill: Optional[Level1Bill] = None
    level1_raw_dict: Dict[str, Any] = {}

    if prep_img is not None:
        for attempt in range(2):
            try:
                resp_text = client.generate_structured(
                    prompt=LEVEL1_SYSTEM_PROMPT,
                    image=prep_img,
                    image_bytes=raw_bytes,
                    response_schema=Level1Bill,
                    force_no_cache=force_no_cache,
                )
                level1_raw_dict = json.loads(resp_text)
                bill_obj, warn_list = postprocess_level1(level1_raw_dict, raw_filename=bill_id)
                for w in warn_list:
                    tracker.add_warning(f"{bill_id}: {w}")
                level1_bill = bill_obj
                break
            except Exception as ex:
                tracker.add_retry()
                logger.warning("%s: Level 1 extraction attempt %d failed: %s", bill_id, attempt + 1, ex)
                if attempt == 1:
                    tracker.add_fallback(bill_id, "Level1", f"Failed after 2 attempts: {ex}")

    if level1_bill is None:
        level1_bill = Level1Bill.fallback()
        tracker.add_fallback(bill_id, "Level1", "Using null fallback object")

    # Step 3: History Extraction
    history_rows: List[HistoryRow] = []
    if prep_img is not None:
        try:
            history_rows = extract_history_table(
                client=client,
                image=prep_img,
                image_bytes=raw_bytes,
                force_no_cache=force_no_cache,
            )
        except Exception as ex:
            tracker.add_warning(f"{bill_id}: History table extraction error: {ex}")
            history_rows = []

    # Step 4: Precomputed Statistics via Calculator
    stats = compute_bill_stats(level1_bill, history_rows)

    # Step 5: Level 2 Q&A
    level1_json_str = json.dumps(level1_bill.model_dump(), indent=2)
    history_json_str = json.dumps([r.model_dump() for r in history_rows], indent=2)

    answers_map: Dict[str, str] = {}

    if questions and prep_img is not None:
        l2_prompt = build_level2_prompt(
            bill_id=bill_id,
            questions=questions,
            level1_json_str=level1_json_str,
            history_json_str=history_json_str,
            stats=stats,
        )

        try:
            l2_resp_text = client.generate_structured(
                prompt=l2_prompt,
                image=prep_img,
                image_bytes=raw_bytes,
                response_schema=Level2AnswersResponse,
                force_no_cache=force_no_cache,
            )
            l2_data = json.loads(l2_resp_text)
            parsed_l2 = Level2AnswersResponse.model_validate(l2_data)
            for item in parsed_l2.answers:
                if item.answer and item.answer.strip():
                    answers_map[item.question_id] = sanitize_no_pii(item.answer.strip())
        except Exception as ex:
            tracker.add_retry()
            logger.warning("%s: Batch Level 2 call failed: %s", bill_id, ex)

    # Single-question retry for missing / empty answers
    for q in questions:
        qid = q["question_id"]
        qtext = q["question"]
        if qid not in answers_map or not answers_map[qid]:
            tracker.add_retry()
            logger.info("%s: Retrying single question %s", bill_id, qid)
            try:
                single_prompt = build_level2_prompt(
                    bill_id=bill_id,
                    questions=[{"question_id": qid, "question": qtext}],
                    level1_json_str=level1_json_str,
                    history_json_str=history_json_str,
                    stats=stats,
                )
                single_resp = client.generate_structured(
                    prompt=single_prompt,
                    image=prep_img,
                    image_bytes=raw_bytes,
                    response_schema=Level2AnswersResponse,
                    force_no_cache=force_no_cache,
                )
                s_data = json.loads(single_resp)
                s_parsed = Level2AnswersResponse.model_validate(s_data)
                for item in s_parsed.answers:
                    if item.question_id == qid and item.answer:
                        answers_map[qid] = sanitize_no_pii(item.answer.strip())
            except Exception as single_ex:
                logger.warning("%s: Single retry failed for %s: %s", bill_id, qid, single_ex)

        # Fallback if still missing
        if qid not in answers_map or not answers_map[qid]:
            tracker.add_fallback(bill_id, f"Level2:{qid}", "Missing answer after retry")
            answers_map[qid] = FALLBACK_L2_ANSWER

    # Compact single-line JSON string for CSV
    compact_l1_json = json.dumps(level1_bill.model_dump(), separators=(",", ":"))

    return {
        "bill_id": bill_id,
        "level1_bill": level1_bill,
        "level1_json_str": compact_l1_json,
        "answers": answers_map,
        "history": history_rows,
        "stats": stats,
    }
