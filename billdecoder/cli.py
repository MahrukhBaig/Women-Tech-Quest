"""Command-line interface for WTQ Utility Bill Decoder."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List

from billdecoder.config import settings
from billdecoder.csv_writer import (
    read_level1_template,
    read_level2_template,
    validate_csv_outputs,
    write_level1_csv,
    write_level2_csv,
)
from billdecoder.llm_client import GeminiClient
from billdecoder.pipeline import PipelineTracker, process_bill

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("billdecoder.cli")


def find_bill_file(bills_dir: Path, bill_id: str) -> Path:
    """Find the bill image file corresponding to bill_id (.png, .jpg, .jpeg)."""
    for ext in (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"):
        candidate = bills_dir / f"{bill_id}{ext}"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No image file found for bill_id '{bill_id}' in {bills_dir}")


def run_pipeline(
    bills_dir: Path,
    level1_template: Path,
    level2_template: Path,
    output_dir: Path,
    no_cache: bool = False,
) -> int:
    """Execute decoding for all bills in template and write output CSVs."""
    # Validate paths first (exit non-zero on config errors)
    if not bills_dir.is_dir():
        logger.error("Bills directory does not exist: %s", bills_dir)
        return 1
    if not level1_template.is_file():
        logger.error("Level 1 template not found: %s", level1_template)
        return 1
    if not level2_template.is_file():
        logger.error("Level 2 template not found: %s", level2_template)
        return 1

    try:
        settings.validate_or_raise()
    except Exception as ex:
        logger.error("Configuration validation failed: %s", ex)
        return 1

    logger.info("Initializing Gemini Client (Model: %s)...", settings.model_name)
    client = GeminiClient()
    tracker = PipelineTracker()

    # Read templates
    bill_ids = read_level1_template(level1_template)
    l2_rows = read_level2_template(level2_template)

    logger.info("Loaded templates: %d bills in Level 1, %d questions in Level 2", len(bill_ids), len(l2_rows))

    # Group questions by bill_id
    questions_by_bill: Dict[str, List[Dict[str, str]]] = {bid: [] for bid in bill_ids}
    for bid, qid, qtext in l2_rows:
        if bid in questions_by_bill:
            questions_by_bill[bid].append({"question_id": qid, "question": qtext})
        else:
            logger.warning("Question references bill_id '%s' not present in level1 template", bid)

    # Process bills sequentially
    level1_results: Dict[str, str] = {}
    level2_results: Dict[str, Dict[str, str]] = {}

    for idx, bid in enumerate(bill_ids, start=1):
        logger.info("--- Processing Bill [%d/%d]: %s ---", idx, len(bill_ids), bid)
        try:
            image_path = find_bill_file(bills_dir, bid)
        except Exception as ex:
            tracker.add_warning(f"File lookup failed for {bid}: {ex}")
            tracker.add_fallback(bid, "MissingImage", str(ex))
            image_path = None

        questions_for_this_bill = questions_by_bill.get(bid, [])

        if image_path is not None:
            res = process_bill(
                image_input=image_path,
                bill_id=bid,
                questions=questions_for_this_bill,
                client=client,
                tracker=tracker,
                force_no_cache=no_cache,
            )
            level1_results[bid] = res["level1_json_str"]
            level2_results[bid] = res["answers"]
        else:
            # Fallback
            from billdecoder.models import Level1Bill
            level1_results[bid] = Level1Bill.fallback().model_dump_json()
            level2_results[bid] = {
                q["question_id"]: "This could not be determined from the bill."
                for q in questions_for_this_bill
            }

    # Write output CSVs
    out_l1 = output_dir / "level1.csv"
    out_l2 = output_dir / "level2.csv"
    output_dir.mkdir(parents=True, exist_ok=True)

    written_l1 = write_level1_csv(out_l1, level1_results, level1_template)
    written_l2 = write_level2_csv(out_l2, level2_results, level2_template)

    logger.info("Wrote %d rows to %s", written_l1, out_l1)
    logger.info("Wrote %d rows to %s", written_l2, out_l2)

    # Run validation self-checks
    val_errors = validate_csv_outputs(
        level1_path=out_l1,
        level2_path=out_l2,
        expected_l1_rows=len(bill_ids),
        expected_l2_rows=len(l2_rows),
    )

    # Print run summary
    token_stats = client.usage.summary()
    print("\n" + "=" * 60)
    print("           WTQ BILL DECODER RUN SUMMARY")
    print("=" * 60)
    print(f"Total Bills Processed: {len(bill_ids)}")
    print(f"Level 1 Rows Written:  {written_l1}")
    print(f"Level 2 Rows Written:  {written_l2}")
    print(f"API Calls Executed:    {token_stats['calls']}")
    print(f"Cache Hits:            {token_stats['cached_hits']}")
    print(f"Prompt Tokens:         {token_stats['prompt_tokens']}")
    print(f"Candidate Tokens:      {token_stats['candidate_tokens']}")
    print(f"Total Tokens:          {token_stats['total_tokens']}")
    print(f"Retries Triggered:     {tracker.retries}")
    print(f"Warnings Logged:       {len(tracker.warnings)}")
    print(f"Fallbacks Triggered:   {len(tracker.fallbacks)}")

    if tracker.fallbacks:
        print("\n[PROMINENT ALERT] FALLBACKS OCCURRED:")
        for fb in tracker.fallbacks:
            print(f"  - Bill: {fb['bill_id']} | Item: {fb['type']} | Reason: {fb['reason']}")
    else:
        print("\n[SUCCESS] Zero fallbacks triggered! All extractions completed cleanly.")

    if val_errors:
        print("\n[VALIDATION ERRORS IN CSVs]:")
        for err in val_errors:
            print(f"  - {err}")
    else:
        print("[SUCCESS] Output CSVs passed all validation self-checks.")

    print("=" * 60 + "\n")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="WTQ Utility Bill Decoder - CLI Pipeline"
    )
    parser.add_argument(
        "--bills-dir",
        type=Path,
        required=True,
        help="Directory containing bill images",
    )
    parser.add_argument(
        "--level1-template",
        type=Path,
        required=True,
        help="Path to level1.csv template",
    )
    parser.add_argument(
        "--level2-template",
        type=Path,
        required=True,
        help="Path to level2.csv template",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory to save output CSVs (default: ./output)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable response disk caching",
    )

    args = parser.parse_args()
    ret = run_pipeline(
        bills_dir=args.bills_dir,
        level1_template=args.level1_template,
        level2_template=args.level2_template,
        output_dir=args.output_dir,
        no_cache=args.no_cache,
    )
    sys.exit(ret)


if __name__ == "__main__":
    main()
