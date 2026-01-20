#backend/app/api/main.py
from fastapi import APIRouter

from app.api import auth
from app.api.routes import watch, recommendations

router = APIRouter(tags=["main"])

@router.get("/")
async def root():
    return {"message": "Welcome to HomeTheaterLive API"}

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-19T00:00:00Z"}

router.include_router(auth.router)
router.include_router(watch.router)
router.include_router(recommendations.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )