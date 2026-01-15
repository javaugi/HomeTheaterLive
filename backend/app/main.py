import sentry_sdk
#from fastapi import FastAPI
from fastapi import APIRouter
# IMPORTANT: import models FIRST
from app.model import user  # noqa: F401

from app.api.auth import router as auth_router
from app.db.session import engine
from app.db.base import Base
from starlette.middleware.cors import CORSMiddleware
from app.api.main import api_router
from app.core.config import settings
from app.api.main import app

# app = FastAPI(
#     title=settings.PROJECT_NAME,
#     openapi_url=f"{settings.API_V1_STR}/openapi.json",
#     generate_unique_id_function=custom_generate_unique_id,
# )
# NOW tables will be created
Base.metadata.create_all(bind=engine)
app.include_router(auth_router, prefix="/api/v1")

def custom_generate_unique_id(route: APIRouter) -> str:
    return f"{route.tags[0]}-{route.name}"

if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
