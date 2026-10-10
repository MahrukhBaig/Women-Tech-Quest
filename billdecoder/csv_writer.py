"""CSV reader and writer module complying with exact competition templates and formatting."""

import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple


def read_level1_template(template_path: Path) -> List[str]:
    """Read level1.csv template and return list of bill_ids preserving original row order."""
    bill_ids = []
    with open(template_path, mode="r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        # Expected: bill_id, json
        for row in reader:
            if row and row[0].strip():
                bill_ids.append(row[0].strip())
    return bill_ids


def read_level2_template(template_path: Path) -> List[Tuple[str, str, str]]:
    """Read level2.csv template and return list of (bill_id, question_id, question) preserving order."""
    rows = []
    with open(template_path, mode="r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        # Expected: bill_id, question_id, question, answer
        for row in reader:
            if len(row) >= 3 and row[0].strip():
                rows.append((row[0].strip(), row[1].strip(), row[2].strip()))
    return rows


def write_level1_csv(
    output_path: Path,
    level1_results: Dict[str, str],
    template_path: Path,
) -> int:
    """Generate completed level1.csv adhering strictly to template row order.
    The json string is compact and on a single line. Python's csv module
    automatically handles CSV quoting and quotation-mark doubling.
    """
    bill_ids = read_level1_template(template_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    written_count = 0
    with open(output_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["bill_id", "json"])
        for bid in bill_ids:
            json_str = level1_results.get(bid, "")
            if not json_str:
                raise ValueError(f"Missing Level 1 JSON for bill_id: {bid}")
            # Ensure JSON is on a single line
            single_line_json = json_str.replace("\r", "").replace("\n", " ").strip()
            writer.writerow([bid, single_line_json])
            written_count += 1

    return written_count


def write_level2_csv(
    output_path: Path,
    level2_results: Dict[str, Dict[str, str]],
    template_path: Path,
) -> int:
    """Generate completed level2.csv adhering strictly to template row order.
    Preserves bill_id, question_id, and question exactly.
    """
    rows = read_level2_template(template_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    written_count = 0
    with open(output_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["bill_id", "question_id", "question", "answer"])
        for bid, qid, qtext in rows:
            bill_answers = level2_results.get(bid, {})
            ans = bill_answers.get(qid, "")
            if not ans:
                ans = "This could not be determined from the bill."
            writer.writerow([bid, qid, qtext, ans])
            written_count += 1

    return written_count


def validate_csv_outputs(
    level1_path: Path,
    level2_path: Path,
    expected_l1_rows: int = 10,
    expected_l2_rows: int = 120,
) -> List[str]:
    """Run self-check validations on produced CSV files.
    Returns list of validation errors (empty if completely valid).
    """
    errors: List[str] = []

    # 1. Check level1.csv
    if not level1_path.is_file():
        errors.append(f"level1.csv not found at {level1_path}")
    else:
        with open(level1_path, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header != ["bill_id", "json"]:
                errors.append(f"level1.csv invalid header: {header}")
            l1_rows = list(reader)
            if len(l1_rows) != expected_l1_rows:
                errors.append(
                    f"level1.csv row count mismatch: found {len(l1_rows)}, expected {expected_l1_rows}"
                )
            for i, row in enumerate(l1_rows, start=1):
                if len(row) != 2:
                    errors.append(f"level1.csv row {i} does not have exactly 2 columns")
                    continue
                bid, jstr = row[0], row[1]
                if not jstr.strip():
                    errors.append(f"level1.csv row {i} ({bid}) has empty json cell")
                    continue
                try:
                    parsed = json.loads(jstr)
                    required_keys = [
                        "provider", "tariff", "sanctioned_load_kw", "bill_month",
                        "reading_date", "issue_date", "due_date", "previous_reading",
                        "current_reading", "units_consumed", "charges", "total_charges",
                        "taxes", "total_taxes", "current_bill", "arrears",
                        "payable_within_due_date", "payable_after_due_date"
                    ]
                    for k in required_keys:
                        if k not in parsed:
                            errors.append(f"level1.csv row {i} ({bid}) missing required key '{k}'")
                except Exception as ex:
                    errors.append(f"level1.csv row {i} ({bid}) JSON parse error: {ex}")

    # 2. Check level2.csv
    if not level2_path.is_file():
        errors.append(f"level2.csv not found at {level2_path}")
    else:
        with open(level2_path, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header != ["bill_id", "question_id", "question", "answer"]:
                errors.append(f"level2.csv invalid header: {header}")
            l2_rows = list(reader)
            if len(l2_rows) != expected_l2_rows:
                errors.append(
                    f"level2.csv row count mismatch: found {len(l2_rows)}, expected {expected_l2_rows}"
                )
            for i, row in enumerate(l2_rows, start=1):
                if len(row) != 4:
                    errors.append(f"level2.csv row {i} does not have exactly 4 columns")
                    continue
                bid, qid, qtext, ans = row[0], row[1], row[2], row[3]
                if not ans.strip():
                    errors.append(f"level2.csv row {i} ({bid}, {qid}) has empty answer cell")

    return errors
