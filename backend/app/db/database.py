# backend/app/db/database.py
from sqlalchemy.orm import declarative_base
from app.models import User, UserCreate
from app.core.config import settings
from app import crud_utils as crud
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, select
print(">>> importing #backend/app/core/db.py done")
# If you ever want to mix SQLModel + SQLAlchemy ORM → decide on one and stick to it (you currently have a mix).

load_dotenv()

Base = declarative_base()

engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    # Only needed for sqlite in some cases
    connect_args={"check_same_thread": False} if "sqlite" in str(
        settings.SQLALCHEMY_DATABASE_URI) else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)

# Dependency to get DB session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
