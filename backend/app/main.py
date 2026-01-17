#backend/app/main.py
import sentry_sdk
from fastapi import FastAPI, APIRouter, Request

from app.db.session import engine
from app.db.base import Base
from starlette.middleware.cors import CORSMiddleware
from app.core.config import settings

from app.api import main, auth

# NOW tables will be created
Base.metadata.create_all(bind=engine)

def custom_generate_unique_id(route: APIRouter) -> str:
    return f"{route.tags[0]}-{route.name}"

if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(main.router, prefix=settings.API_V1_STR)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.middleware("http")
async def log_auth(request: Request, call_next):
    auth = request.headers.get("authorization")
    print("backend/app/main.py log_auth AUTH HEADER:", auth)
    return await call_next(request)