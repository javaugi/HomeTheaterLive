# app/db/session.py
from contextlib import contextmanager
from contextvars import ContextVar
from sqlalchemy.orm import Session

current_db_session: ContextVar[Session | None] = ContextVar("current_db_session", default=None)

@contextmanager
def db_session_scope():
    session = current_db_session.get()
    if session is None:
        raise RuntimeError("No database session in context")
    yield session

