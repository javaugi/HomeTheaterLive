#backend/app/api/main.py
from fastapi import APIRouter
from app.api import auth
from app.api.routes import watch, recommendations

router = APIRouter(tags=["main"])

@router.get("/")
async def root():
    return {"message": "Welcome to HomeTheaterLive API"}

router.include_router(auth.router)
router.include_router(watch.router)
router.include_router(recommendations.router)