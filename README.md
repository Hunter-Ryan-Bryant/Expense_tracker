
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
├── main.py            # FastAPI app and route definitions
├── models.py          # SQLModel table and Pydantic request/response schemas
├── database.py        # SQLite engine and session setup
├── conftest.py        # pytest fixtures: in-memory SQLite + dependency override
├── test_expenses.py   # API test suite
├── smoke_test.py      # Manual check against a running server (not run by pytest)
├── requirements.txt
└── README.md
expense_tracker/
├── main.py            # FastAPI app & route definitions
├── models.py          # SQLModel table & Pydantic request/response schemas
├── database.py        # Database engine & session setup
├── conftest.py        # Pytest fixtures (in-memory SQLite override)
├── test_expenses.py   # API endpoint test suite
├── requirements.txt
└── .github/workflows/tests.yml   # Runs pytest on every push & PR
```

---

## 🔌 API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/expenses/` | Create an expense |
| `GET` | `/expenses/` | List expenses. Query params: `category`, `start_date`, `end_date`, `sort_by` (`date_incurred` or `amount`), `order` (`asc` or `desc`), `limit`, `offset` |
| `GET` | `/expenses/{id}` | Fetch one expense (404 if missing) |
| `PATCH` | `/expenses/{id}` | Update only the fields you send |
| `DELETE` | `/expenses/{id}` | Delete an expense (404 if missing) |

Example expense body:

```json
{ "title": "Morning Coffee", "amount": 4.50, "category": "Food", "date_incurred": "2026-10-17" }
```
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/expenses/` | Create an expense (`amount` must be > 0) |
| `GET` | `/expenses/` | List expenses. Query params: `category`, `start_date`, `end_date`, `sort_by` (`date_incurred` or `amount`), `order` (`asc`/`desc`), `limit`, `offset` |
| `GET` | `/expenses/{id}` | Get one expense |
| `PATCH` | `/expenses/{id}` | Partially update an expense |
| `DELETE` | `/expenses/{id}` | Delete an expense |

Interactive docs are generated automatically at `/docs` once the server is running.

---

## 🏁 Getting Started

```bash
git clone https://github.com/rm9v27j9jv-collab/Expense_tracker.git
cd Expense_tracker
python -m venv .venv
.venv\Scripts\activate          # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Run the server:

```bash
uvicorn main:app --reload
```

Interactive API docs are at http://127.0.0.1:8000/docs. The SQLite database (`expenses.db`) is created automatically on first startup.
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000/docs.

## 🧪 Running Tests

```bash
python -m pytest
```

Tests use an in-memory SQLite database, so they never touch `expenses.db`.
pytest -v
```

Tests run against a fresh in-memory SQLite database, so they never touch `expenses.db`.
