"""Tests for normalisation, date parsing, negative signs, and PII sanitisation."""

from billdecoder.postprocessing import clean_date_str, clean_month_str, postprocess_level1, sanitize_no_pii


def test_date_and_month_cleaning():
    assert clean_date_str("2026-04-21") == "2026-04-21"
    assert clean_date_str("invalid-date") is None
    assert clean_date_str(None) is None

    assert clean_month_str("2026-04") == "2026-04"
    assert clean_month_str("2026-04-01") is None
    assert clean_month_str("") is None


def test_cr_credits_negative():
    raw_data = {
        "provider": "KE",
        "arrears": "38209CR",
        "current_bill": "19,964",
    }
    bill, _ = postprocess_level1(raw_data)
    assert bill.arrears == -38209.0
    assert bill.current_bill == 19964.0


def test_subsidy_enforced_negative():
    raw_data = {
        "provider": "IESCO",
        "charges": [
            {"type": "subsidy", "amount": 3332.0},
            {"type": "energy", "amount": 5000.0},
        ],
    }
    bill, _ = postprocess_level1(raw_data)
    subsidy_item = next(c for c in bill.charges if c.type == "subsidy")
    assert subsidy_item.amount == -3332.0


def test_pii_sanitization():
    text_with_cnic = "Customer with CNIC 42101-1234567-1 must pay on time."
    clean = sanitize_no_pii(text_with_cnic)
    assert "42101-1234567-1" not in clean
    assert "[REDACTED]" in clean


def test_rule_e_deterministic_guard_lesco():
    # LESCO bill where a subtotal was mistakenly parsed as a single energy charge
    raw_data = {
        "provider": "LESCO",
        "charges": [{"type": "energy", "amount": 3777.49}],
        "total_charges": 3777.49,
    }
    bill, warnings = postprocess_level1(raw_data)
    assert bill.charges == []
    assert bill.total_charges == 3777.49
    assert any("Rule E guard applied" in w for w in warnings)


def test_rule_e_does_not_affect_ke_or_multi_charges():
    # KE bill with single charge matching total_charges is preserved
    ke_data = {
        "provider": "KE",
        "charges": [{"type": "energy", "amount": 1054.0}],
        "total_charges": 1054.0,
    }
    bill_ke, _ = postprocess_level1(ke_data)
    assert len(bill_ke.charges) == 1

    # IESCO bill with subsidy and FPA is preserved
    iesco_data = {
        "provider": "IESCO",
        "charges": [
            {"type": "subsidy", "amount": -3332.0},
            {"type": "fpa", "amount": 267.0},
        ],
        "total_charges": 6102.0,
    }
    bill_iesco, _ = postprocess_level1(iesco_data)
    assert len(bill_iesco.charges) == 2

