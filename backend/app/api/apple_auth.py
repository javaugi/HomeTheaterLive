
from fastapi import APIRouter
import jwt

router = APIRouter()

@router.post("/apple/login")
def apple_login(identity_token: str):
    # TODO: Verify token with Apple's public keys
    payload = jwt.decode(identity_token, options={"verify_signature": False})
    return {
        "email": payload.get("email"),
        "provider": "apple"
    }
