#3️⃣ Create the Test User (Guaranteed to Work)
#📄 backend/app/dev_seed.py

from app.db.session import SessionLocal
from app.model.user import User
from app.core.security import get_password_hash

def create_test_user():
    db = SessionLocal()
    if not db.query(User).filter(User.username == "test").first():
        db.add(
            User(
                username="test",
                email="test@example.com",
                hashed_password=get_password_hash("test"),
                role="admin"
            )
        )
        db.commit()
        print("✅ Test user created")
    else:
        print("ℹ️ Test user already exists")

if __name__ == "__main__":
    create_test_user()

