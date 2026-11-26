# 💰 FastAPI Expense Tracker API

A robust RESTful backend API built with **FastAPI**, **SQLModel**, and **Pydantic** for tracking, filtering, and managing personal expenses. Designed with automated testing in mind, featuring an isolated `pytest` suite and in-memory SQLite database fixtures.

---

## 🚀 Features

* **Full CRUD Operations:** Create, list, fetch by ID, partially update, and delete expense records.
* **Advanced Query Parameters:** Filter by category and date range, sort by date or amount (ascending or descending), and page through results with `limit`/`offset`.
* **Data Validation:** Strict request/response validation and partial update handling using Pydantic (`exclude_unset=True`).
* **Automated Testing Suite:** Integration tests for every endpoint using `pytest` with isolated in-memory SQLite test databases (`conftest.py`).

---

## 🛠️ Tech Stack

* **Language:** Python 3.10+
* **Framework:** FastAPI
* **Database & ORM:** SQLite, SQLModel
* **Validation & Settings:** Pydantic
* **Testing:** pytest, FastAPI TestClient
* **Version Control:** Git & GitHub

---

## 📂 Project Structure

```text
Expense_tracker/
├── main.py                 # FastAPI app and route definitions
├── models.py               # SQLModel table and Pydantic request/response schemas
├── database.py             # SQLite engine and session setup
├── conftest.py             # pytest fixtures: in-memory SQLite + dependency override
├── test_expenses.py        # API test suite
├── manual_smoke_check.py   # Manual check against a running server: python manual_smoke_check.py
├── requirements.txt
├── README.md
└── .github/workflows/tests.yml   # Runs pytest on every push & PR
```

---

## 🔌 API Endpoints

| Method | Path | Success | Description |
|---|---|---|---|
| `POST` | `/expenses/` | `201` | Create an expense |
| `GET` | `/expenses/` | `200` | List expenses (query parameters below) |
| `GET` | `/expenses/{id}` | `200` | Fetch one expense (404 if missing) |
| `PATCH` | `/expenses/{id}` | `200` | Update only the fields you send (404 if missing) |
| `DELETE` | `/expenses/{id}` | `204` | Delete an expense; empty response body (404 if missing) |

Invalid input returns `422` with details about which field is wrong.

### Expense fields

| Field | Rules |
|---|---|
| `title` | Required, 1–200 characters (surrounding spaces are trimmed) |
| `amount` | Required, greater than 0, at most 2 decimal places and 10 digits |
| `category` | Optional, 1–50 characters, defaults to `"General"` |
| `date_incurred` | Optional `YYYY-MM-DD`, defaults to today |

**Amounts are exact.** They're stored as decimals rather than floats, so `0.10 + 0.20` is exactly `0.30`. Responses send them as strings with 2 decimals, for example `"4.50"`. Requests can send either `4.5` or `"4.50"`.

With `PATCH`, leave a field out to keep its current value. Sending `null` is rejected.

```jsonc
// POST /expenses/
{ "title": "Morning Coffee", "amount": 4.50, "category": "Food", "date_incurred": "2026-10-17" }

// 201 Created
{ "id": 1, "title": "Morning Coffee", "amount": "4.50", "category": "Food", "date_incurred": "2026-10-17" }
```

### List query parameters

| Parameter | Default | Notes |
|---|---|---|
| `category` | none | Case-insensitive: `food` matches `Food` |
| `start_date`, `end_date` | none | Inclusive; `start_date` must not be after `end_date` |
| `sort_by` | `date_incurred` | `date_incurred` or `amount` |
| `order` | `desc` | `asc` or `desc` |
| `limit` | `100` | 1–500 |
| `offset` | `0` | 0 or more |

Interactive docs are generated automatically at `/docs` once the server is running.

---

## 🏁 Getting Started

```bash
git clone https://github.com/Hunter-Ryan-Bryant/Expense_tracker.git
cd Expense_tracker
python -m venv .venv
.venv\Scripts\activate          # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Run the server:

```bash
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000/docs. The SQLite database (`expenses.db`) is created automatically on first startup, next to `main.py`, no matter which folder you start the server from. To use a different database, set `EXPENSES_DATABASE_URL`, for example `sqlite:///C:/data/expenses.db`.

---

## 🧪 Running Tests

```bash
python -m pytest -v
```

Tests run against a fresh in-memory SQLite database, so they never touch `expenses.db`.
