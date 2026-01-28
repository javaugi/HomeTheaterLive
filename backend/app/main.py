#backend/app/main.py
print(">>> importing backend/app/main.py")
import sentry_sdk
from fastapi import FastAPI, APIRouter, Request

from starlette.middleware.cors import CORSMiddleware
from app.core.config import settings

from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
import os
print(">>> importing backend/app/main.py done")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting backend/app/main.py HomeTheaterLive Backend...")
    print(f"DEBUG: Current Working Directory: {os.getcwd()}")
    print(f"DEBUG: Looking for STATIC_DIR  directory at: {os.path.abspath(settings.STATIC_DIR)}")    
    print(f"DEBUG: Looking for UPLOAD_DIRs directory at: {os.path.abspath(settings.UPLOAD_DIR)}")   
    print(f"DEBUG: Looking for env_file location: {os.path.abspath(settings.ENV_FILE_LOC)}")
    #print(f"DEBUG: Looking for all settings: {settings.model_dump()}")   
    
    # Create database tables during startup (not at import time)
    from app.db.session import engine
    from app.db.base import Base
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    yield
    # Shutdown
    print("Shutting down...")

def custom_generate_unique_id(route: APIRouter) -> str:
    return f"{route.tags[0]}-{route.name}"

if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for images and photos, as well as converting images to video",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan    
)

print(">>> backend/app/main.py adding routers")
from app.api.routes import watch, recommendations
from app.api.auth import router as auth_router
from app.api.main import router as main_router
from app.api.endpoints import router as endpoints_router
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(main_router, prefix=settings.API_V1_STR)
app.include_router(endpoints_router, prefix=settings.API_V1_STR)
app.include_router(watch.router, prefix=settings.API_V1_STR)
app.include_router(recommendations.router, prefix=settings.API_V1_STR)
print(">>> backend/app/main.py adding routers done")

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount static files directory
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

@app.middleware("http")
async def log_auth(request: Request, call_next):
    auth = request.headers.get("authorization")
    print("backend/app/main.py log_auth AUTH HEADER:", auth)
    return await call_next(request)