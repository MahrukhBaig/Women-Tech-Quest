"""Deterministic Python calculator for precomputing all numerical stats from Level 1 bill and history."""

from typing import Any, Dict, List, Optional
from billdecoder.models import HistoryRow, Level1Bill


def compute_bill_stats(bill: Level1Bill, history: List[HistoryRow]) -> Dict[str, Any]:
    """Compute deterministic statistics from Level 1 bill and historical consumption rows.
    The LLM must NEVER perform arithmetic. All counts, averages, percentages,
    and differences must be provided precomputed.
    """
    stats: Dict[str, Any] = {}

    # 1. Tax share and breakdown
    current_bill = bill.current_bill
    total_taxes = bill.total_taxes
    total_charges = bill.total_charges

    if current_bill and current_bill > 0 and total_taxes is not None:
        tax_pct = round((total_taxes / current_bill) * 100.0, 2)
        stats["tax_share_pct"] = tax_pct
        stats["tax_share_text"] = f"{tax_pct}% of current bill (PKR {total_taxes} out of PKR {current_bill})"
    else:
        stats["tax_share_pct"] = None
        stats["tax_share_text"] = "Unavailable"

    if current_bill and current_bill > 0 and total_charges is not None:
        charges_pct = round((total_charges / current_bill) * 100.0, 2)
        stats["charges_share_pct"] = charges_pct
        stats["charges_share_text"] = f"{charges_pct}% of current bill"
    else:
        stats["charges_share_pct"] = None
        stats["charges_share_text"] = "Unavailable"

    # Tax line details
    tax_lines = []
    for t in bill.taxes:
        tax_lines.append(f"{t.type} (PKR {t.amount})")
    stats["tax_lines_summary"] = ", ".join(tax_lines) if tax_lines else "None or combined"

    # 2. Charge lines summary & largest charge
    charge_lines = []
    largest_charge_type: Optional[str] = None
    largest_charge_amt: Optional[float] = None
    fpa_total: float = 0.0
    has_fpa: bool = False

    for c in bill.charges:
        charge_lines.append(f"{c.type} (PKR {c.amount})")
        if largest_charge_amt is None or c.amount > largest_charge_amt:
            largest_charge_amt = c.amount
            largest_charge_type = c.type
        if c.type == "fpa":
            has_fpa = True
            fpa_total += c.amount

    stats["charges_lines_summary"] = ", ".join(charge_lines) if charge_lines else "None"
    stats["largest_charge"] = (
        f"{largest_charge_type} (PKR {largest_charge_amt})"
        if largest_charge_amt is not None
        else "None"
    )
    stats["fpa_total_pkr"] = fpa_total if has_fpa else None

    # 3. Historical consumption stats
    # Filter rows with valid numeric units
    valid_history = [r for r in history if r.units is not None and isinstance(r.units, (int, float))]
    units_history = [r.units for r in valid_history]

    stats["history_months_count"] = len(units_history)

    if units_history:
        avg_units = round(sum(units_history) / len(units_history), 2)
        max_units = max(units_history)
        min_units = min(units_history)

        # Find which months were max and min
        max_months = [r.month for r in valid_history if r.units == max_units]
        min_months = [r.month for r in valid_history if r.units == min_units]

        stats["average_monthly_units"] = avg_units
        stats["max_monthly_units"] = max_units
        stats["max_monthly_months"] = ", ".join(max_months)
        stats["min_monthly_units"] = min_units
        stats["min_monthly_months"] = ", ".join(min_months)

        # Months above 200 units threshold
        above_200_rows = [r for r in valid_history if r.units > 200]
        above_200_count = len(above_200_rows)
        above_200_details = [f"{r.month} ({r.units} units)" for r in above_200_rows]
        stats["history_months_above_200_count"] = above_200_count
        stats["history_months_above_200_details"] = (
            ", ".join(above_200_details) if above_200_details else "None"
        )

        # Does current month exceed 200?
        curr_units = bill.units_consumed
        if curr_units is not None:
            curr_exceeds_200 = curr_units > 200
            stats["current_month_exceeds_200"] = curr_exceeds_200
            total_above_200 = above_200_count + (1 if curr_exceeds_200 else 0)
            stats["total_above_200_including_current"] = total_above_200
        else:
            stats["current_month_exceeds_200"] = None
            stats["total_above_200_including_current"] = above_200_count

        # Difference vs average
        if curr_units is not None:
            diff_vs_avg = round(curr_units - avg_units, 2)
            pct_diff_vs_avg = (
                round((diff_vs_avg / avg_units) * 100.0, 2) if avg_units > 0 else 0.0
            )
            stats["difference_vs_average_units"] = diff_vs_avg
            stats["difference_vs_average_pct"] = pct_diff_vs_avg
            if diff_vs_avg > 0:
                stats["difference_vs_average_summary"] = (
                    f"{abs(diff_vs_avg)} units higher than average ({pct_diff_vs_avg}% above average)"
                )
            elif diff_vs_avg < 0:
                stats["difference_vs_average_summary"] = (
                    f"{abs(diff_vs_avg)} units lower than average ({abs(pct_diff_vs_avg)}% below average)"
                )
            else:
                stats["difference_vs_average_summary"] = "Exactly equal to the average"
        else:
            stats["difference_vs_average_units"] = None
            stats["difference_vs_average_summary"] = "Unavailable"
    else:
        stats["average_monthly_units"] = None
        stats["max_monthly_units"] = None
        stats["max_monthly_months"] = "No history"
        stats["min_monthly_units"] = None
        stats["min_monthly_months"] = "No history"
        stats["history_months_above_200_count"] = 0
        stats["history_months_above_200_details"] = "No history recorded"
        stats["current_month_exceeds_200"] = (
            bill.units_consumed > 200 if bill.units_consumed is not None else None
        )
        stats["total_above_200_including_current"] = (
            1 if (bill.units_consumed and bill.units_consumed > 200) else 0
        )
        stats["difference_vs_average_units"] = None
        stats["difference_vs_average_summary"] = "No historical billing records to compute average"

    # 4. Late payment details
    if (
        bill.payable_after_due_date is not None
        and bill.payable_within_due_date is not None
    ):
        late_fee = round(bill.payable_after_due_date - bill.payable_within_due_date, 2)
        stats["late_payment_difference_pkr"] = late_fee
    else:
        stats["late_payment_difference_pkr"] = None

    # 5. Arrears
    stats["arrears_status"] = (
        "Credit carried forward"
        if (bill.arrears is not None and bill.arrears < 0)
        else ("Unpaid past dues" if (bill.arrears is not None and bill.arrears > 0) else "None")
    )

    return stats
