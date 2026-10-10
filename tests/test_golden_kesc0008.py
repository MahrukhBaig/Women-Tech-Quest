"""Golden test comparison for KESC_0008 with guide's official tolerances."""

import json
from billdecoder.models import Level1Bill

GOLDEN_KESC_0008 = {
    "provider": "KE",
    "tariff": "A1-R",
    "sanctioned_load_kw": 3,
    "bill_month": "2026-04",
    "reading_date": "2026-04-03",
    "issue_date": "2026-04-07",
    "due_date": "2026-04-21",
    "previous_reading": 8819,
    "current_reading": 8970,
    "units_consumed": 151,
    "charges": [
        {"type": "fixed", "amount": 900},
        {"type": "energy", "amount": 1054},
        {"type": "energy", "amount": 663.51},
        {"type": "quarterly_adjustment", "amount": 52.91},
        {"type": "fpa", "amount": 125.27},
        {"type": "surcharge", "amount": 64.93},
    ],
    "total_charges": 2860.62,
    "taxes": [
        {"type": "electricity_duty", "amount": 29.41},
        {"type": "gst", "amount": 520.21},
        {"type": "municipal_tax", "amount": 20},
    ],
    "total_taxes": 569.62,
    "current_bill": 3430.24,
    "arrears": -0.53,
    "payable_within_due_date": 3430,
    "payable_after_due_date": 3716,
}


def assert_matches_golden_with_tolerance(actual: Level1Bill, golden: dict = GOLDEN_KESC_0008):
    """Checks that text/dates match exactly, and numbers match within +-1.0."""
    act_dict = actual.model_dump()

    # Exact text/date checks
    assert act_dict["provider"] == golden["provider"], f"Provider mismatch: {act_dict['provider']} vs {golden['provider']}"
    assert act_dict["tariff"] == golden["tariff"], f"Tariff mismatch: {act_dict['tariff']} vs {golden['tariff']}"
    assert act_dict["bill_month"] == golden["bill_month"]
    assert act_dict["reading_date"] == golden["reading_date"]
    assert act_dict["issue_date"] == golden["issue_date"]
    assert act_dict["due_date"] == golden["due_date"]

    # Numeric checks with +-1.0 tolerance
    num_fields = [
        "sanctioned_load_kw", "previous_reading", "current_reading", "units_consumed",
        "total_charges", "total_taxes", "current_bill", "arrears",
        "payable_within_due_date", "payable_after_due_date"
    ]
    for field in num_fields:
        act_val = act_dict[field]
        gold_val = golden[field]
        assert act_val is not None, f"Field {field} is unexpectedly None"
        assert abs(act_val - gold_val) <= 1.0, f"Field {field} value {act_val} exceeds tolerance for {gold_val}"

    # Charges check
    assert len(act_dict["charges"]) == len(golden["charges"])
    for act_c, gold_c in zip(act_dict["charges"], golden["charges"]):
        assert act_c["type"] == gold_c["type"]
        assert abs(act_c["amount"] - gold_c["amount"]) <= 1.0

    # Taxes check
    assert len(act_dict["taxes"]) == len(golden["taxes"])
    for act_t, gold_t in zip(act_dict["taxes"], golden["taxes"]):
        assert act_t["type"] == gold_t["type"]
        assert abs(act_t["amount"] - gold_t["amount"]) <= 1.0


def test_golden_validator():
    """Verify that golden dictionary itself parses cleanly and passes tolerance."""
    bill = Level1Bill.model_validate(GOLDEN_KESC_0008)
    assert_matches_golden_with_tolerance(bill)
