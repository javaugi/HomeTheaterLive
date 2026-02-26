#backend/app/api/deps.py
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db

from app.model.user import User
from app.models import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        print("backend/app/api/deps.py get_current_user, token:", token)
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="backend/app/api/deps.py get_current_user Could not validate credentials",
        )

    if not token_data.sub:
        print("backend/app/api/deps.py get_current_user Invalid token subject")
        raise HTTPException(status_code=403, detail="Invalid token subject")

    #user = session.get(User, token_data.sub)
    user = session.query(User).filter(User.username == token_data.sub).first()
    if not user:
        print("backend/app/api/deps.py get_current_user User not found")
        raise HTTPException(status_code=404, detail="User not found")

    if user.disabled == 1 or not user.is_active:
        print("backend/app/api/deps.py get_current_user Inactive user")
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
