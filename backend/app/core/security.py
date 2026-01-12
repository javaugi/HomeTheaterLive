from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext
import bcrypt
from app.core.config import settings

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Or keep using pwd_context but with bcryptpbkdf
# pwd_context = CryptContext(
#     schemes=["bcrypt"],
#     default="bcrypt",
#     bcrypt__ident="2b",  # Use 2b ident
#     bcrypt__max_password_size=72,  # Explicitly set max size
# )

# You could switch to argon2 or another algorithm that doesn't have this issue: size > 72 bytes
# pwd_context = CryptContext(
#     schemes=["argon2", "bcrypt"],  # Argon2 first, bcrypt fallback
#     default="argon2",
# )

# Workaround for bcrypt 72-byte limit
def hash_password(password: str) -> str:
    # Truncate or hash the password if it's too long
    if len(password.encode('utf-8')) > 72:
        # Option 1: Truncate (simpler but less secure for very long passwords)
        password = password[:72]
        # Option 2: Hash first with SHA256 (more secure)
        # import hashlib
        # password = hashlib.sha256(password.encode()).hexdigest()[:72]
    
    # Use bcrypt directly
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Truncate if too long (must match the hashing method)
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password[:72]
    
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
