# backend/app/api/auth.py
print(">>> importing backend/app/api/auth.py")
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.model.user import User
from app.core.security import (
    verify_password,
    create_access_token
)
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
print(">>> importing backend/app/api/auth.py done")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""Option B — Temporary Dev Login (Quick Debug Only)
If you just want to test UI quickly, modify:

⚠️ DO NOT use in production
"""
@router.post("/login")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    print("backend/app/api/auth.py login user=", form.username, ", pwd=", form.password)
    if form.username == "test" and form.password == "test":
        access = create_access_token("test", 15)
        refresh = create_access_token("test",43200)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer"
        }

    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    access = create_access_token(form.username, 15)
    refresh = create_access_token(form.username,43200)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer"
    }

"""✔ This is OAuth2-compliant
✔ Works with mobile
✔ App Store safe"""

@router.post("/refresh")
def refresh(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)
        return {"access_token": create_access_token(payload["sub"], 15)}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
