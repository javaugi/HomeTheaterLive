# Run the function to create the test user when the script is executed
# backend/app/dev_seed.py
from app.db.session import SessionLocal
from app.model.user import User
from app.core.security import get_password_hash

def create_test_user():
    db = SessionLocal()
    if not db.query(User).filter(User.username == "test").first():
        user = User(
            username="test",
            email="david.lee.remax@gmail.com",
            hashed_password=get_password_hash("test"),
            role="admin"
        )
        db.add(user)
        db.commit()
        print("Test user created")
    else:
        print("Test user already exists")

if __name__ == "__main__":
    create_test_user()