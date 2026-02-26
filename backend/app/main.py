# backend/app/main.py
from .api.endpoints import router as endpoints_router
from .api.main import router as main_router
from .api.auth import router as auth_router
from .api.routes import watch, recommendations
from .core.config import settings
from pathlib import Path
import sys
import os
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
# from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks

import sentry_sdk
print(">>> importing backend/app/main.py")


# Add shared module to Python path before app.core.config import
shared_path = Path(__file__).resolve().parent.parent.parent / "shared"
print(f">>> importing backend/app/main.py shared_path={shared_path}")
sys.path.insert(0, str(shared_path))

print(">>> importing backend/app/main.py done")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting backend/app/main.py HomeTheaterLive Backend...")
    print(f"DEBUG: Current Working Directory: {os.getcwd()}")
    print(f"DEBUG: Looking for STATIC_DIR  directory at: {
          os.path.abspath(settings.STATIC_DIR)}")
    print(f"DEBUG: Looking for UPLOAD_DIRs directory at: {
          os.path.abspath(settings.UPLOAD_DIR)}")
    print(f"DEBUG: Looking for env_file location: {
          os.path.abspath(settings.ENV_FILE_LOC)}")
    print(f"DEBUG: Looking for PROJ_DIR location: {
          os.path.abspath(settings.PROJ_DIR)}")
    print(f"DEBUG: Looking for settings.VIDEO_OUTPUT_DIR location: {
          os.path.abspath(settings.VIDEO_OUTPUT_DIR)}")
    # print(f"DEBUG: Looking for all settings: {settings.model_dump()}")
    print(f"DEBUG: Looking for settings.SOUNDFONTS_DIR location: {
          os.path.abspath(settings.SOUNDFONTS_DIR)}")
    print(f"DEBUG: Looking for settings.GM2_SOUNDFONT_PATH location: {
          os.path.abspath(settings.GM2_SOUNDFONT_PATH)}")

    # Create database tables during startup (not at import time)
    from app.db.database import Base, engine
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    yield
    # Shutdown
    print("Shutting down...")


def custom_generate_unique_id(route: APIRouter) -> str:
    # return f"{route.tags[0]}-{route.name}"
    if route.tags and len(route.tags) > 0:
        return f"{route.tags[0]}-{route.name or 'unnamed'}"
    else:
        # Fallback for untagged routes (like favicon, root, etc.)
        # Use the path or method or just a safe string
        path_clean = route.path.replace(
            "/", "-").replace("{", "").replace("}", "")
        return f"untagged-{route.name or path_clean or 'route'}"


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
        expose_headers=["*"],
        # expose_headers=["Authorization"]  # Important!
    )

# Mount static files directory
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
app.mount("/api/v1/video",
          StaticFiles(directory=settings.VIDEO_OUTPUT_DIR), name="videos")
# Then put favicon.ico in backend/static/
# Browser will find it at /static/favicon.ico (but you'd need <link> in HTML if serving HTML)


@app.middleware("http")
async def log_auth(request: Request, call_next):
    auth = request.headers.get("authorization") or request.headers.get("Authorization") \
        or request.headers.get("AUTHORIZATION")
    print(f"\nExtracted auth header: {auth}, Request URL: {request.url}, Request method: {
          request.method}", "\n ALL HEADERS:", dict(request.headers))
    return await call_next(request)

# Option 1: Return an empty/transparent 1x1 pixel (no real file needed)


# @app.get("/favicon.ico", include_in_schema=False)
# async def favicon():
#    return Response(status_code=204)  # No Content → browser stops asking

# Option 2: If you have a real favicon.ico file (recommended for production)
favicon_path = "path/to/your/static/favicon.ico"


@app.get("/favicon.ico", include_in_schema=False, tags=["favicon"])
async def favicon():
    if not os.path.exists(favicon_path):
        raise HTTPException(status_code=404)
    return FileResponse(favicon_path, media_type="image/x-icon")
