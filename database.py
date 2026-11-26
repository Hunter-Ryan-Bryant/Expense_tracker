import os
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

# The database lives next to this file, so it's the same no matter which folder
# the server is started from. Set EXPENSES_DATABASE_URL to use a different one.
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "expenses.db"
DATABASE_URL = os.environ.get("EXPENSES_DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
