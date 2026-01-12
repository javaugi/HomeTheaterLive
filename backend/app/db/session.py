from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# DATABASE_URL = "sqlite:///./app.db"
DATABASE_URL = (
    "postgresql+psycopg2://mht_dev_user:mht_dev_pwd_108@localhost:5432/PG_MHT_DEV"
)


engine = create_engine(
    DATABASE_URL
    # , connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  
        