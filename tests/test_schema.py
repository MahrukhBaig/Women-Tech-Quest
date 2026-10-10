"""Tests for Pydantic schema validation and fallback behavior."""

import json
from billdecoder.models import Level1Bill, ChargeItem, TaxItem


def test_level1_schema_keys():
    fallback = Level1Bill.fallback()
    data = fallback.model_dump()
    expected_keys = {
        "provider", "tariff", "sanctioned_load_kw", "bill_month",
        "reading_date", "issue_date", "due_date", "previous_reading",
        "current_reading", "units_consumed", "charges", "total_charges",
        "taxes", "total_taxes", "current_bill", "arrears",
        "payable_within_due_date", "payable_after_due_date"
    }
    assert set(data.keys()) == expected_keys
    assert data["charges"] == []
    assert data["taxes"] == []
    assert data["provider"] is None


def test_level1_valid_instantiation():
    bill = Level1Bill(
        provider="KE",
        tariff="A1-R",
        sanctioned_load_kw=3,
        bill_month="2026-04",
        reading_date="2026-04-03",
        issue_date="2026-04-07",
        due_date="2026-04-21",
        previous_reading=8819,
        current_reading=8970,
        units_consumed=151,
        charges=[
            ChargeItem(type="fixed", amount=900),
            ChargeItem(type="energy", amount=1054),
        ],
        total_charges=1954,
        taxes=[
            TaxItem(type="gst", amount=350),
        ],
        total_taxes=350,
        current_bill=2304,
        arrears=-0.53,
        payable_within_due_date=2304,
        payable_after_due_date=2500,
    )
    serialized = bill.model_dump_json()
    parsed = json.loads(serialized)
    assert parsed["provider"] == "KE"
    assert len(parsed["charges"]) == 2
    assert parsed["arrears"] == -0.53
