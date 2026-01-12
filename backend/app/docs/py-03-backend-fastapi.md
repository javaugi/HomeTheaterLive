3️⃣ Backend: FastAPI (JWT + Refresh)
Login (already exists in template)

POST /api/v1/login/access-token

🔐 Add Refresh Token (Important for Mobile)

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(refresh_token, settings.SECRET_KEY)
    new_access = create_access_token(payload["sub"])
    return {"access_token": new_access, "token_type": "bearer"}

Mobile-Friendly Settings

ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
