"""Tests for deterministic calculator statistics."""

from billdecoder.calculator import compute_bill_stats
from billdecoder.models import ChargeItem, HistoryRow, Level1Bill, TaxItem


def test_calculator_stats():
    bill = Level1Bill(
        provider="KE",
        current_bill=3430.24,
        total_charges=2860.62,
        total_taxes=569.62,
        units_consumed=151,
        payable_within_due_date=3430,
        payable_after_due_date=3716,
        charges=[
            ChargeItem(type="energy", amount=1054),
            ChargeItem(type="fpa", amount=125.27),
        ],
        taxes=[
            TaxItem(type="gst", amount=520.21),
            TaxItem(type="electricity_duty", amount=29.41),
            TaxItem(type="municipal_tax", amount=20),
        ],
    )

    history = [
        HistoryRow(month="2025-07", units=239, bill_amount=6000),
        HistoryRow(month="2025-08", units=203, bill_amount=5200),
        HistoryRow(month="2025-09", units=180, bill_amount=4500),
    ]

    stats = compute_bill_stats(bill, history)

    # 16.61% tax share
    assert stats["tax_share_pct"] == 16.61
    # Average of 239, 203, 180 = 207.33
    assert stats["average_monthly_units"] == 207.33
    assert stats["history_months_above_200_count"] == 2
    assert stats["current_month_exceeds_200"] is False
    assert stats["total_above_200_including_current"] == 2
    assert stats["difference_vs_average_units"] == -56.33  # 151 - 207.33
    assert stats["late_payment_difference_pkr"] == 286.0  # 3716 - 3430
    assert stats["fpa_total_pkr"] == 125.27
