from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel


def _strip(value):
    """Trim surrounding whitespace so "   " counts as empty."""
    return value.strip() if isinstance(value, str) else value


class ExpenseBase(SQLModel):
    title: str = Field(index=True, min_length=1, max_length=200)
    # Decimal, not float: money must be exact (0.1 + 0.2 == 0.3).
    # Sent in JSON as a string with 2 decimals, e.g. "4.50".
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    category: str = Field(default="General", min_length=1, max_length=50)
    date_incurred: date = Field(default_factory=date.today)

    @field_validator("title", "category", mode="before")
    @classmethod
    def strip_text(cls, value):
        return _strip(value)


class Expense(ExpenseBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseRead(ExpenseBase):
    id: int


class ExpenseUpdate(SQLModel):
    """Partial update: leave a field out to keep its current value."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    amount: Optional[Decimal] = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    category: Optional[str] = Field(default=None, min_length=1, max_length=50)
    date_incurred: Optional[date] = None

    # Validators only run for fields that were actually sent, so this rejects an
    # explicit null without affecting fields that were left out.
    @field_validator("title", "amount", "category", "date_incurred", mode="before")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("can't be null; leave the field out to keep its current value")
        return _strip(value)


class SummaryGroup(SQLModel):
    """Totals for one category (e.g. "Food") or one month (e.g. "2026-10")."""

    key: str
    total: Decimal
    count: int


class ExpenseSummary(SQLModel):
    group_by: Literal["category", "month"]
    category: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total: Decimal
    count: int
    groups: list[SummaryGroup]
