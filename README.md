
# 💰 FastAPI Expense Tracker API

A robust RESTful backend API built with **FastAPI**, **SQLModel**, and **Pydantic** for tracking, filtering, and managing personal expenses. Designed with automated testing in mind, featuring an isolated `pytest` suite and in-memory SQLite database fixtures.

---

## 🚀 Features

* **Full CRUD Operations:** Create, read, update, and delete expense records.
* **Advanced Query Parameters:** Filter expenses dynamically by category or date-range, with built-in sorting and pagination.
* **Data Validation:** Strict request/response validation and partial update handling using Pydantic (`exclude_unset=True`).
* **Automated Testing Suite:** Comprehensive unit and integration tests using `pytest` with isolated in-memory SQLite test databases (`conftest.py`).

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
expense-tracker/
│
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application & route definitions
│   ├── models.py        # SQLModel database tables & Pydantic schemas
│   └── database.py      # Database engine & session setup
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py      # Pytest fixtures & in-memory SQLite overrides
│   └── test_expenses.py # API endpoint test suite
│
├── .gitignore
├── requirements.txt
└── README.md
