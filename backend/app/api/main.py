from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.db.session import engine
from app.db.base import Base
from app.api.router import api_router  # Import the router
from app.core.config import settings

app = FastAPI()

Base.metadata.create_all(bind=engine)

# app.include_router(auth_router, prefix="/api/v1")
# Include the router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to HomeTheaterLive API"}