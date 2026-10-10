"""Regression tests for current_bill values on all 5 training bills and sanity guard."""

import pytest
from billdecoder.postprocessing import postprocess_level1
from billdecoder.calculator import compute_bill_stats
from billdecoder.models import Level1Bill


def test_five_training_bills_expected_current_bill():
    """Verify expected current_bill values for all 5 training bills:
    - KESC_0008: 3430.24
    - KESC_0004: 45570.25
    - LESCO_0005: 20726.0
    - LESCO_0006: 5501.0
    - IESCO_0004: 3267.0
    """
    expected_values = {
        "KESC_0008": {
            "provider": "KE",
            "total_charges": 2860.62,
            "total_taxes": 569.62,
            "current_bill": 3430.24,
            "payable_within_due_date": 3430.0,
        },
        "KESC_0004": {
            "provider": "KE",
            "total_charges": 38098.01,
            "total_taxes": 7472.24,
            "current_bill": 45570.25,
            "payable_within_due_date": 0.0,
        },
        "LESCO_0005": {
            "provider": "LESCO",
            "total_charges": 17367.77,
            "total_taxes": 3358.23,
            "current_bill": 20726.0,
            "payable_within_due_date": -54770.0,
        },
        "LESCO_0006": {
            "provider": "LESCO",
            "total_charges": 3777.49,
            "total_taxes": 1723.51,
            "current_bill": 5501.0,
            "payable_within_due_date": 44912.0,
        },
        "IESCO_0004": {
            "provider": "IESCO",
            "total_charges": 6102.0,
            "total_taxes": 498.0,
            "charges": [{"type": "subsidy", "amount": -3332.0}, {"type": "fpa", "amount": 267.0}],
            "current_bill": 3267.0,
            "payable_within_due_date": 3535.0,
        },
    }

    for bid, raw_data in expected_values.items():
        bill, warnings = postprocess_level1(raw_data, raw_filename=bid)
        expected_cb = raw_data["current_bill"]
        assert bill.current_bill == pytest.approx(expected_cb, abs=0.01), (
            f"{bid}: Expected current_bill {expected_cb}, got {bill.current_bill}"
        )


def test_lesco_0005_tax_percentage_calculation():
    """Verify LESCO_0005 tax percentage is ~16.2% when current_bill is 20726."""
    raw_data = {
        "provider": "LESCO",
        "total_charges": 17367.77,
        "total_taxes": 3358.23,
        "current_bill": 20726.0,
        "payable_within_due_date": -54770.0,
    }
    bill, _ = postprocess_level1(raw_data, raw_filename="LESCO_0005")
    stats = compute_bill_stats(bill, history=[])
    assert stats["tax_share_pct"] == pytest.approx(16.20, abs=0.05)
    assert stats["charges_share_pct"] == pytest.approx(83.80, abs=0.05)
