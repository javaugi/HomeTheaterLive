# backend/app/api/router.py
from fastapi import APIRouter
from app.core.config import settings
from app.api import auth, main
from app.api.routes import watch, recommendations

api_router = APIRouter(tags=["route"])

api_router.include_router(auth.router, prefix=settings.API_V1_STR, tags=["auth"])
api_router.include_router(main.router, prefix=settings.API_V1_STR, tags=["main"])
api_router.include_router(watch.router)
api_router.include_router(recommendations.router)