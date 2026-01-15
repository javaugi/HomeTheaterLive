# Run the function to create the test user when the script is executed
# backend/app/dev_seed.py
from app.db.session import SessionLocal
from app.model.user import User
from app.core.security import get_password_hash

def create_users():
    create_user('admin', 'admin@hometheater.live', 'admin', 'admin', 'Admin Joe', 0)
    create_user('user', 'user@hometheater.live', 'user', 'user', 'User Jane', 0)


def create_user(username, email, password, role='user', full_name=None, disabled=0):
    db = SessionLocal()
    if not db.query(User).filter(User.username == username or User.email == email).first():
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
            full_name=full_name,
            disabled=disabled
        )
        db.add(user)
        db.commit()
        print(f"User {username} created")
    else:
        print(f"User {username} already exists")

if __name__ == "__main__":
    create_users()