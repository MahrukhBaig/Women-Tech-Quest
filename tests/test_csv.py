"""Tests for CSV round-trips, escaping, single-line JSON, and template integrity."""

import csv
from pathlib import Path
from billdecoder.csv_writer import (
    read_level1_template,
    read_level2_template,
    validate_csv_outputs,
    write_level1_csv,
    write_level2_csv,
)


def test_csv_round_trip(tmp_path: Path):
    # Create mock templates
    l1_tpl = tmp_path / "tpl_l1.csv"
    l1_tpl.write_text("bill_id,json\nKESC_0008,\nIESCO_0004,\n", encoding="utf-8")

    l2_tpl = tmp_path / "tpl_l2.csv"
    l2_tpl.write_text(
        "bill_id,question_id,question,answer\n"
        "KESC_0008,Q1,How much is tax?,\n"
        "IESCO_0004,Q1,How much is tax?,\n",
        encoding="utf-8",
    )

    out_l1 = tmp_path / "out_l1.csv"
    out_l2 = tmp_path / "out_l2.csv"

    # Write outputs
    l1_data = {
        "KESC_0008": '{"provider":"KE","current_bill":3430}',
        "IESCO_0004": '{"provider":"IESCO","current_bill":1500}',
    }
    l2_data = {
        "KESC_0008": {"Q1": "Tax is PKR 569.62."},
        "IESCO_0004": {"Q1": "Tax is PKR 498.00."},
    }

    count_l1 = write_level1_csv(out_l1, l1_data, l1_tpl)
    count_l2 = write_level2_csv(out_l2, l2_data, l2_tpl)

    assert count_l1 == 2
    assert count_l2 == 2

    # Verify quotes doubled and single line in raw CSV
    raw_text = out_l1.read_text(encoding="utf-8")
    assert '"{""provider"":""KE""' in raw_text
    lines = raw_text.strip().splitlines()
    assert len(lines) == 3  # Header + 2 rows

    # Validate output function
    errors = validate_csv_outputs(out_l1, out_l2, expected_l1_rows=2, expected_l2_rows=2)
    # Both test rows missing required keys will be reported by validator
    assert any("missing required key" in e for e in errors)
