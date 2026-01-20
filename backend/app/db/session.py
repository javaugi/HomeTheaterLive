from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from sqlalchemy.ext.declarative import declarative_base

# DATABASE_URL = "sqlite:///./app.db"
#DATABASE_URL = (
#    "postgresql+psycopg2://mht_dev_user:mht_dev_pwd_108@localhost:5432/PG_MHT_DEV"
#)


engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    connect_args={"check_same_thread": False} if "PostgresDsn" in str(settings.SQLALCHEMY_DATABASE_URI) else {}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  
        