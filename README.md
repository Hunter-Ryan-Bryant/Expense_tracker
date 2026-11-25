
# 💰 FastAPI Expense Tracker API

A robust RESTful backend API built with **FastAPI**, **SQLModel**, and **Pydantic** for tracking, filtering, and managing personal expenses. Designed with automated testing in mind, featuring an isolated `pytest` suite and in-memory SQLite database fixtures.

---

## 🚀 Features

* **Full CRUD Operations:** Create, read, update, and delete expense records.
* **Advanced Query Parameters:** Filter expenses dynamically by category or date-range, with built-in sorting and pagination.
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
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000/docs.

## 🧪 Running Tests

```bash
pytest -v
```

Tests run against a fresh in-memory SQLite database, so they never touch `expenses.db`.
