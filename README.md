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
| `GET` | `/expenses/summary` | `200` | Totals and counts, overall and per category or month ([details](#spending-summary)) |
| `GET` | `/expenses/export.csv` | `200` | Download matching expenses as a CSV file ([details](#csv-export)) |
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
| `q` | none | Search titles: case-insensitive "contains" match, up to 100 characters. `coffee` matches "Morning Coffee" and "Iced COFFEE". `%` and `_` are matched literally |
| `category` | none | Case-insensitive: `food` matches `Food` |
| `start_date`, `end_date` | none | Inclusive; `start_date` must not be after `end_date` |
| `sort_by` | `date_incurred` | `date_incurred` or `amount` |
| `order` | `desc` | `asc` or `desc` |
| `limit` | `100` | 1–500 |
| `offset` | `0` | 0 or more |

### Spending summary

`GET /expenses/summary` answers questions like "how much did I spend on food in October?":

```
GET /expenses/summary?category=food&start_date=2026-10-01&end_date=2026-10-31
```

| Parameter | Default | Notes |
|---|---|---|
| `group_by` | `category` | `category` or `month` |
| `q`, `category`, `start_date`, `end_date` | none | Same filters as the list endpoint. For example, `?q=coffee` answers "how much have I spent on coffee?" |

```json
{
  "group_by": "category",
  "q": null,
  "category": null,
  "start_date": null,
  "end_date": null,
  "total": "52.80",
  "count": 4,
  "groups": [
    { "key": "Transport", "total": "40.00", "count": 1 },
    { "key": "School", "total": "12.50", "count": 1 },
    { "key": "Food", "total": "0.30", "count": 2 }
  ]
}
```

- **Exact totals:** amounts are added as decimals, so `0.10 + 0.20` is exactly `"0.30"`.
- **By category:** groups go from largest total to smallest. Categories are matched ignoring case, so `Food` and `food` are one group, shown with the first spelling used.
- **By month:** keys look like `"2026-10"` and go in date order.
- **Nothing found:** you get `"total": "0.00"`, `"count": 0` and an empty `groups` list.

### CSV export

`GET /expenses/export.csv` downloads matching expenses as `expenses-YYYY-MM-DD.csv`, ready to open in Excel, Google Sheets or Numbers. You can open it straight from your browser, for example http://127.0.0.1:8000/expenses/export.csv?category=food.

```csv
id,title,amount,category,date_incurred
2,Gas,40.00,Transport,2026-10-02
1,Coffee,4.50,Food,2026-10-01
```

- **Filters and sorting:** accepts the same `q`, `category`, `start_date`, `end_date`, `sort_by` and `order` parameters as the list endpoint.
- **No paging:** every matching expense is included.
- **Amounts** are exact, with 2 decimals.
- **Excel-friendly:** the file is UTF-8 with a byte-order mark (BOM) so Excel shows accents and emoji correctly. Commas, quotes and line breaks inside titles are quoted properly.
- **Formula safety:** text that a spreadsheet would run as a formula, meaning it starts with `=`, `+`, `-` or `@`, gets a leading `'` so it displays as plain text. This guards against CSV injection.

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
