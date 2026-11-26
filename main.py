from contextlib import asynccontextmanager
from datetime import date
from typing import Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Session, asc, desc, func, select

from database import create_db_and_tables, get_session
from models import Expense, ExpenseCreate, ExpenseRead, ExpenseUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Expense Tracker", lifespan=lifespan)


def get_expense_or_404(session: Session, expense_id: int) -> Expense:
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.post("/expenses/", response_model=ExpenseRead, status_code=201)
def create_expense(expense: ExpenseCreate, session: Session = Depends(get_session)):
    db_expense = Expense.model_validate(expense)
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense


@app.get("/expenses/", response_model=list[ExpenseRead])
def read_expenses(
    category: Optional[str] = Query(None, description="Case-insensitive match"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sort_by: Literal["date_incurred", "amount"] = "date_incurred",
    order: Literal["asc", "desc"] = "desc",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")

    statement = select(Expense)
    if category:
        statement = statement.where(func.lower(Expense.category) == category.strip().lower())
    if start_date:
        statement = statement.where(Expense.date_incurred >= start_date)
    if end_date:
        statement = statement.where(Expense.date_incurred <= end_date)

    sort_column = Expense.amount if sort_by == "amount" else Expense.date_incurred
    direction = desc if order == "desc" else asc
    # id breaks ties so pagination is stable when amounts or dates are equal.
    statement = statement.order_by(direction(sort_column), direction(Expense.id))

    return session.exec(statement.offset(offset).limit(limit)).all()


@app.get("/expenses/{expense_id}", response_model=ExpenseRead)
def read_expense(expense_id: int, session: Session = Depends(get_session)):
    return get_expense_or_404(session, expense_id)


@app.patch("/expenses/{expense_id}", response_model=ExpenseRead)
def update_expense(expense_id: int, expense_update: ExpenseUpdate, session: Session = Depends(get_session)):
    db_expense = get_expense_or_404(session, expense_id)
    for key, value in expense_update.model_dump(exclude_unset=True).items():
        setattr(db_expense, key, value)
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, session: Session = Depends(get_session)):
    session.delete(get_expense_or_404(session, expense_id))
    session.commit()
