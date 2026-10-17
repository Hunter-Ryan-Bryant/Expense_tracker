from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select, desc, asc
from database import create_db_and_tables, get_session
from models import Expense, ExpenseCreate, ExpenseRead, ExpenseUpdate
from typing import Optional
from datetime import date

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/expenses/", response_model=ExpenseRead)
def create_expense(expense: ExpenseCreate, session: Session = Depends(get_session)):
    db_expense = Expense.model_validate(expense)
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense

@app.get("/expenses/", response_model=list[ExpenseRead])
def read_expenses(category: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None,
                  sort_by: Optional[str] = "date_incurred", order: Optional[str] = "desc",
                   limit: int = 100, offset: int = 0, session: Session = Depends(get_session)):
    statement = select(Expense)
    if category:
        statement = statement.where(Expense.category == category)
    if start_date:
        statement = statement.where(Expense.date_incurred >= start_date)
    if end_date:
        statement = statement.where(Expense.date_incurred <= end_date)
    if sort_by == "amount":
        sort_column = Expense.amount
    else:
        sort_column = Expense.date_incurred
    if order == 'desc':
        statement = statement.order_by(desc(sort_column))
    else:
        statement = statement.order_by(asc(sort_column))
    statement = statement.offset(offset).limit(limit)
    expenses = session.exec(statement).all()
    return expenses
@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, session: Session = Depends(get_session)):
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    session.delete(expense)
    session.commit
    return {"ok": True, "message": f"Expense with ID {expense_id} deleted successfully"}
@app.patch("/expenses/{expense_id}", response_model=ExpenseRead)
def update_expense(expense_id: int, expense_update: ExpenseUpdate, session: Session = Depends(get_session)):
    db_expense = session.get(Expense, expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    update_data = expense_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_expense, key, value)
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense
    
