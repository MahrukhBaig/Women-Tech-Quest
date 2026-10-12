"""Pydantic data models for Level 1 extraction, history, stats, and Level 2 Q&A."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


ProviderType = Literal["KE", "LESCO", "IESCO"]

ChargeType = Literal[
    "energy",
    "fixed",
    "fpa",
    "quarterly_adjustment",
    "surcharge",
    "meter_rent",
    "subsidy",
    "other",
]

TaxType = Literal[
    "gst",
    "electricity_duty",
    "income_tax",
    "municipal_tax",
    "other_tax",
]


class ChargeItem(BaseModel):
    """An individual line item from the charges section."""
    type: ChargeType
    amount: float


class TaxItem(BaseModel):
    """An individual line item from the taxes/government section."""
    type: TaxType
    amount: float


class Level1Bill(BaseModel):
    """Level 1 extracted bill details conforming strictly to the competition schema."""
    provider: Optional[ProviderType] = Field(
        default=None,
        description="Utility provider: KE, LESCO, or IESCO. Null if unreadable.",
    )
    tariff: Optional[str] = Field(
        default=None,
        description="Tariff code exactly as printed (e.g. A1-R, A-1a(01)). Null if unreadable.",
    )
    sanctioned_load_kw: Optional[float] = Field(
        default=None,
        description="Sanctioned load in kW (e.g. 3, 5.0). Null if unreadable.",
    )
    bill_month: Optional[str] = Field(
        default=None,
        description="Billing month in YYYY-MM format. Null if unreadable.",
    )
    reading_date: Optional[str] = Field(
        default=None,
        description="Meter reading date in YYYY-MM-DD format. Null if unreadable.",
    )
    issue_date: Optional[str] = Field(
        default=None,
        description="Bill issue date in YYYY-MM-DD format. Null if unreadable.",
    )
    due_date: Optional[str] = Field(
        default=None,
        description="Due date for payment in YYYY-MM-DD format. Null if unreadable.",
    )
    previous_reading: Optional[float] = Field(
        default=None,
        description="Previous meter reading numeric value. Null if unreadable.",
    )
    current_reading: Optional[float] = Field(
        default=None,
        description="Current meter reading numeric value. Null if unreadable.",
    )
    units_consumed: Optional[float] = Field(
        default=None,
        description="Units consumed/billed for the current month. Null if unreadable.",
    )
    charges: List[ChargeItem] = Field(
        default_factory=list,
        description="List of charge items. Empty list if none/unitemized.",
    )
    total_charges: Optional[float] = Field(
        default=None,
        description="Printed subtotal for charges, or null if not printed.",
    )
    taxes: List[TaxItem] = Field(
        default_factory=list,
        description="List of tax items. Empty list if none/combined.",
    )
    total_taxes: Optional[float] = Field(
        default=None,
        description="Printed subtotal for taxes, or combined tax amount.",
    )
    current_bill: Optional[float] = Field(
        default=None,
        description="Printed current month bill amount. Null if unreadable.",
    )
    arrears: Optional[float] = Field(
        default=None,
        description="Previous dues carried forward. Negative for credits. Null if blank.",
    )
    payable_within_due_date: Optional[float] = Field(
        default=None,
        description="Amount payable within/by due date. Null if unreadable.",
    )
    payable_after_due_date: Optional[float] = Field(
        default=None,
        description="Amount payable after due date (highest if multiple). Null if unreadable.",
    )

    @classmethod
    def fallback(cls) -> "Level1Bill":
        """Return a valid fallback object populated with nulls and empty lists."""
        return cls(
            provider=None,
            tariff=None,
            sanctioned_load_kw=None,
            bill_month=None,
            reading_date=None,
            issue_date=None,
            due_date=None,
            previous_reading=None,
            current_reading=None,
            units_consumed=None,
            charges=[],
            total_charges=None,
            taxes=[],
            total_taxes=None,
            current_bill=None,
            arrears=None,
            payable_within_due_date=None,
            payable_after_due_date=None,
        )


class HistoryRow(BaseModel):
    """One month row from the consumption/payment history table."""
    month: str
    units: Optional[float] = None
    bill_amount: Optional[float] = None
    payment: Optional[float] = None


class HistoryExtraction(BaseModel):
    """List of history rows extracted from the bill."""
    rows: List[HistoryRow] = Field(default_factory=list)


class Level2AnswerItem(BaseModel):
    """Answer for a single question."""
    question_id: str
    answer: str


class Level2AnswersResponse(BaseModel):
    """Collection of answers for all questions for a given bill."""
    answers: List[Level2AnswerItem]
