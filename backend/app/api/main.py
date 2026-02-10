#backend/app/api/main.py
print(">>> importing backend/app/api/main.py")
from fastapi import APIRouter, Request
from datetime import datetime

router = APIRouter(tags=["main"])
print(">>> importing backend/app/api/main.py done")

@router.get("/")
async def root():
    return {"message": "Welcome to HomeTheaterLive API"}

@router.get("/health")
async def health_check(request: Request):
    print(f"Health check endpoint hit! Path: {request.url.path}")
    return {"status": "healthy", "status_code": 200, "timestamp": datetime.now().isoformat()}

"""
from app.core.config import settings

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
"""