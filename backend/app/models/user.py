from sqlalchemy import Column, Integer, String
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")
    full_name = Column(String, nullable=True)
    disabled = Column(Integer, default=0)  # 0 = active, 1 = disabled   
    def __repr__(self):
        return f"<User(username={self.username}, email={self.email}, role={self.role})>"    
    