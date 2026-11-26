import csv
import io
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from sqlmodel import Session, asc, desc, func, select

from database import create_db_and_tables, get_session
from models import (
    Expense,
    ExpenseCreate,
    ExpenseRead,
    ExpenseSummary,
    ExpenseUpdate,
    SummaryGroup,
)


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


def clean_search(q: Optional[str]) -> Optional[str]:
    """Trim the search text; blank means "no search"."""
    q = q.strip() if q else ""
    return q or None


def title_contains(q: str):
    """Case-insensitive "title contains q". % and _ are matched literally, not as LIKE wildcards."""
    escaped = q.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return func.lower(Expense.title).like(f"%{escaped}%", escape="\\")


def apply_filters(
    statement,
    category: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
    q: Optional[str] = None,
):
    """Search, category (case-insensitive) and inclusive date-range filters shared by list and summary."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")
    if q:
        statement = statement.where(title_contains(q))
    if category:
        statement = statement.where(func.lower(Expense.category) == category.strip().lower())
    if start_date:
        statement = statement.where(Expense.date_incurred >= start_date)
    if end_date:
        statement = statement.where(Expense.date_incurred <= end_date)
    return statement


def apply_sort(statement, sort_by: str, order: str):
    sort_column = Expense.amount if sort_by == "amount" else Expense.date_incurred
    direction = desc if order == "desc" else asc
    # id breaks ties so pagination is stable when amounts or dates are equal.
    return statement.order_by(direction(sort_column), direction(Expense.id))


# Spreadsheets run cells starting with these as formulas (CSV injection).
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def spreadsheet_safe(text: str) -> str:
    """Prefix text that a spreadsheet would treat as a formula so it shows as plain text."""
    return "'" + text if text.startswith(FORMULA_PREFIXES) else text


@app.post("/expenses/", response_model=ExpenseRead, status_code=201)
def create_expense(expense: ExpenseCreate, session: Session = Depends(get_session)):
    db_expense = Expense.model_validate(expense)
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense


SEARCH_QUERY = Query(None, max_length=100, description='Case-insensitive "title contains" search')


@app.get("/expenses/", response_model=list[ExpenseRead])
def read_expenses(
    q: Optional[str] = SEARCH_QUERY,
    category: Optional[str] = Query(None, description="Case-insensitive match"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sort_by: Literal["date_incurred", "amount"] = "date_incurred",
    order: Literal["asc", "desc"] = "desc",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    statement = apply_filters(select(Expense), category, start_date, end_date, clean_search(q))
    statement = apply_sort(statement, sort_by, order)
    return session.exec(statement.offset(offset).limit(limit)).all()


CSV_COLUMNS = ["id", "title", "amount", "category", "date_incurred"]


# Must be registered before /expenses/{expense_id}, or "export.csv" is parsed as an id.
@app.get(
    "/expenses/export.csv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}, "description": "CSV file of matching expenses"}},
)
def export_expenses_csv(
    q: Optional[str] = SEARCH_QUERY,
    category: Optional[str] = Query(None, description="Case-insensitive match"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sort_by: Literal["date_incurred", "amount"] = "date_incurred",
    order: Literal["asc", "desc"] = "desc",
    session: Session = Depends(get_session),
):
    """Download every matching expense as CSV (same filters as the list, no paging).

    Built in memory rather than streamed: FastAPI closes the database session
    before a streamed response finishes. Starts with a UTF-8 BOM so Excel shows
    accents and emoji correctly.
    """
    statement = apply_filters(select(Expense), category, start_date, end_date, clean_search(q))
    expenses = session.exec(apply_sort(statement, sort_by, order)).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)  # RFC 4180: quotes commas/quotes/newlines, \r\n line endings
    writer.writerow(CSV_COLUMNS)
    for e in expenses:
        writer.writerow(
            [e.id, spreadsheet_safe(e.title), f"{e.amount:.2f}", spreadsheet_safe(e.category), e.date_incurred.isoformat()]
        )

    filename = f"expenses-{date.today().isoformat()}.csv"
    return Response(
        content=buffer.getvalue().encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# Must be registered before /expenses/{expense_id}, or "summary" is parsed as an id.
@app.get("/expenses/summary", response_model=ExpenseSummary)
def summarize_expenses(
    group_by: Literal["category", "month"] = "category",
    q: Optional[str] = SEARCH_QUERY,
    category: Optional[str] = Query(None, description="Case-insensitive match"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    session: Session = Depends(get_session),
):
    """Total spent and number of expenses, overall and per category or month.

    Totals are added up in Python with Decimal so they're exact (SQLite would
    sum them as floats). Categories are grouped case-insensitively, shown with
    their first-used spelling, and sorted by total (largest first); months are
    "YYYY-MM" in date order.
    """
    statement = select(Expense.category, Expense.date_incurred, Expense.amount).order_by(Expense.id)
    q = clean_search(q)
    rows = session.exec(apply_filters(statement, category, start_date, end_date, q)).all()

    groups: dict[str, dict] = {}
    for row_category, row_date, amount in rows:
        if group_by == "month":
            group_id = label = row_date.strftime("%Y-%m")
        else:
            group_id, label = row_category.lower(), row_category
        group = groups.setdefault(group_id, {"key": label, "total": Decimal("0.00"), "count": 0})
        group["total"] += amount
        group["count"] += 1

    if group_by == "month":
        ordered = sorted(groups.values(), key=lambda g: g["key"])
    else:
        ordered = sorted(groups.values(), key=lambda g: (-g["total"], g["key"].lower()))

    return ExpenseSummary(
        group_by=group_by,
        q=q,
        category=category.strip() if category else None,
        start_date=start_date,
        end_date=end_date,
        total=sum((g["total"] for g in ordered), Decimal("0.00")),
        count=len(rows),
        groups=[SummaryGroup(**g) for g in ordered],
    )


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
