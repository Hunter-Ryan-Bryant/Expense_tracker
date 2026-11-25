from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date

class ExpenseBase(SQLModel):
    title: str = Field(index=True)
    amount: float = Field(gt=0)
    category: str = "General"
    date_incurred: date = Field(default_factory=date.today)

class Expense(ExpenseBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseRead(ExpenseBase):
    id: int
class ExpenseUpdate(SQLModel):
    title: Optional[str] = None
    amount: Optional[float] = Field(default=None, gt=0)
    category: Optional[str] = None
    date_incurred: Optional[date] = None