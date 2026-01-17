# app/api/__init__.py
from fastapi import APIRouter
from app.api import auth
from app.api.routes import watch, recommendations

router = APIRouter(tags=["init"])


router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(watch.router)
router.include_router(recommendations.router)
