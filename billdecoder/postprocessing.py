"""Post-processing and validation module for extracted bill data."""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from billdecoder.models import Level1Bill, ChargeItem, TaxItem

logger = logging.getLogger("billdecoder.postprocessing")

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")
CNIC_PATTERN = re.compile(r"\b\d{5}-\d{7}-\d\b")


def clean_date_str(val: Optional[str]) -> Optional[str]:
    """Ensure date is in YYYY-MM-DD or None."""
    if not val or not isinstance(val, str):
        return None
    val = val.strip()
    if DATE_PATTERN.match(val):
        return val
    # If partial YYYY-MM provided for a date, do not guess day
    return None


def clean_month_str(val: Optional[str]) -> Optional[str]:
    """Ensure bill_month is in YYYY-MM or None."""
    if not val or not isinstance(val, str):
        return None
    val = val.strip()
    if MONTH_PATTERN.match(val):
        return val
    return None


def postprocess_level1(bill_data: Dict[str, Any], raw_filename: str = "") -> Tuple[Level1Bill, List[str]]:
    """Post-process and validate Level 1 extracted dictionary:
    - Enforces negative sign on subsidies
    - Validates date formats
    - Cross-checks provider with filename prefix
    - Performs reconciliation checks to produce warnings (without modifying printed values)
    - Returns validated Level1Bill and list of warning strings.
    """
    warnings: List[str] = []

    # 1. Cross-check provider
    provider = bill_data.get("provider")
    if provider:
        provider = str(provider).strip().upper()
        if provider not in ("KE", "LESCO", "IESCO"):
            warnings.append(f"Invalid provider '{provider}'. Nulling.")
            provider = None

    # Check filename prefix cross-check
    fn_upper = raw_filename.upper()
    expected_prov = None
    if fn_upper.startswith("KESC"):
        expected_prov = "KE"
    elif fn_upper.startswith("LESCO"):
        expected_prov = "LESCO"
    elif fn_upper.startswith("IESCO"):
        expected_prov = "IESCO"

    if expected_prov and provider and provider != expected_prov:
        warnings.append(
            f"Filename suggests provider '{expected_prov}' but bill image indicates '{provider}'. Trusting image per rules."
        )

    # 2. Tariff
    tariff = bill_data.get("tariff")
    if tariff is not None:
        tariff = str(tariff).strip()
        if tariff.lower() in ("null", "none", "", "unreadable", "n/a"):
            tariff = None

    # 3. Numeric conversions & sanitizations
    def to_num(v: Any) -> Optional[float]:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return v
        s = str(v).strip().replace(",", "").replace("Rs.", "").replace("PKR", "").replace(" ", "")
        if s.lower() in ("null", "none", "", "n/a"):
            return None
        is_cr = s.upper().endswith("CR")
        if is_cr:
            s = s[:-2]
        try:
            val = float(s)
            return -abs(val) if is_cr else val
        except ValueError:
            return None

    sanctioned_load_kw = to_num(bill_data.get("sanctioned_load_kw"))
    previous_reading = to_num(bill_data.get("previous_reading"))
    current_reading = to_num(bill_data.get("current_reading"))
    units_consumed = to_num(bill_data.get("units_consumed"))
    total_charges = to_num(bill_data.get("total_charges"))
    total_taxes = to_num(bill_data.get("total_taxes"))
    current_bill = to_num(bill_data.get("current_bill"))
    arrears = to_num(bill_data.get("arrears"))
    payable_within_due_date = to_num(bill_data.get("payable_within_due_date"))
    payable_after_due_date = to_num(bill_data.get("payable_after_due_date"))

    # Dates
    bill_month = clean_month_str(bill_data.get("bill_month"))
    reading_date = clean_date_str(bill_data.get("reading_date"))
    issue_date = clean_date_str(bill_data.get("issue_date"))
    due_date = clean_date_str(bill_data.get("due_date"))

    # 4. Charges processing
    charges_raw = bill_data.get("charges") or []
    processed_charges: List[ChargeItem] = []
    valid_charge_types = {
        "energy", "fixed", "fpa", "quarterly_adjustment",
        "surcharge", "meter_rent", "subsidy", "other"
    }

    for c in charges_raw:
        if isinstance(c, dict):
            ctype = str(c.get("type", "other")).strip().lower()
            if ctype not in valid_charge_types:
                ctype = "other"
            amt = to_num(c.get("amount"))
            if amt is not None and amt != 0:
                # Rule: Subsidies must be negative
                if ctype == "subsidy" and amt > 0:
                    amt = -amt
                processed_charges.append(ChargeItem(type=ctype, amount=amt))  # type: ignore

    # Rule E deterministic guard for non-KE providers:
    # If charges has exactly one entry, with no subsidy type, whose amount equals total_charges,
    # then this was a subtotal mistakenly parsed as a charge line -> set charges = [] and log warning.
    if provider != "KE" and len(processed_charges) == 1 and total_charges is not None:
        single_c = processed_charges[0]
        if single_c.type != "subsidy" and abs(single_c.amount - total_charges) <= 1.0:
            warnings.append(
                f"Rule E guard applied: Non-KE provider '{provider}' had a single '{single_c.type}' charge matching total_charges ({total_charges}). Resetting charges to []."
            )
            processed_charges = []

    # 5. Taxes processing

    taxes_raw = bill_data.get("taxes") or []
    processed_taxes: List[TaxItem] = []
    valid_tax_types = {
        "gst", "electricity_duty", "income_tax", "municipal_tax", "other_tax"
    }

    for t in taxes_raw:
        if isinstance(t, dict):
            ttype = str(t.get("type", "other_tax")).strip().lower()
            if ttype not in valid_tax_types:
                ttype = "other_tax"
            amt = to_num(t.get("amount"))
            if amt is not None and amt != 0:
                processed_taxes.append(TaxItem(type=ttype, amount=amt))  # type: ignore

    # 6. Reconciliation checks (produce warnings only; never overwrite printed values)
    #
    # NOTE on subsidies:
    #  - total_charges on the bill is the GROSS electricity subtotal (before subsidy)
    #  - subsidy items are stored as negative amounts and offset the payable current_bill
    #  - We must exclude subsidy amounts from the charges-sum check and from the
    #    current-bill check so that subsidised bills don't generate false-positive notices.

    subsidy_sum = sum(
        c.amount for c in processed_charges if c.type == "subsidy"
    )  # will be <= 0

    has_itemized_energy = any(c.type == "energy" for c in processed_charges)
    if total_charges is not None and processed_charges and (has_itemized_energy or provider == "KE"):
        # Compare only non-subsidy charges against the printed total_charges when charges are fully itemized
        non_subsidy_sum = sum(
            c.amount for c in processed_charges if c.type != "subsidy"
        )
        if abs(non_subsidy_sum - total_charges) > 2.0:
            warnings.append(
                f"Charges reconciliation notice: sum of non-subsidy charges ({non_subsidy_sum:.2f}) differs from total_charges ({total_charges:.2f})."
            )

    if total_taxes is not None and processed_taxes:
        sum_taxes = sum(t.amount for t in processed_taxes)
        if abs(sum_taxes - total_taxes) > 2.0:
            warnings.append(
                f"Taxes reconciliation notice: sum of taxes ({sum_taxes:.2f}) differs from total_taxes ({total_taxes:.2f})."
            )

    if (
        current_bill is not None
        and total_charges is not None
        and total_taxes is not None
    ):
        # current_bill = total_charges + subsidy (negative) + total_taxes
        expected_curr = total_charges + subsidy_sum + total_taxes
        if abs(expected_curr - current_bill) > 2.0:
            warnings.append(
                f"Current bill reconciliation notice: total_charges + subsidy + total_taxes ({expected_curr:.2f}) differs from printed current_bill ({current_bill:.2f})."
            )

    # Construct validated model
    bill = Level1Bill(
        provider=provider,  # type: ignore
        tariff=tariff,
        sanctioned_load_kw=sanctioned_load_kw,
        bill_month=bill_month,
        reading_date=reading_date,
        issue_date=issue_date,
        due_date=due_date,
        previous_reading=previous_reading,
        current_reading=current_reading,
        units_consumed=units_consumed,
        charges=processed_charges,
        total_charges=total_charges,
        taxes=processed_taxes,
        total_taxes=total_taxes,
        current_bill=current_bill,
        arrears=arrears,
        payable_within_due_date=payable_within_due_date,
        payable_after_due_date=payable_after_due_date,
    )

    return bill, warnings


def sanitize_no_pii(text: str) -> str:
    """Ensure no personal identification numbers (like CNIC) leak into output."""
    if not text:
        return text
    # Redact any CNIC pattern if present
    cleaned = CNIC_PATTERN.sub("[REDACTED]", text)
    return cleaned
