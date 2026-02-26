# backend/app/core/config.py
from typing import Annotated, Any, List, Self
from pathlib import Path
import sys
import os

from pydantic import PostgresDsn, computed_field, BeforeValidator, EmailStr, model_validator
from pydantic_settings import SettingsConfigDict

# Add project root to path before shared.config import
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def parse_cors(v: Any) -> list[str] | str:
    """Parse CORS origins from string or list"""
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


# class BackendSettings(BaseSettingsConfig):
class BackendSettings(__import__("shared.config",
                                 fromlist=["BaseSettingsConfig"]).BaseSettingsConfig):
    """Backend-specific settings"""
    model_config = SettingsConfigDict(
        env_file="../../.env.backend",  # Specific env file
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="BACKEND_",  # Optional: prefix for backend-specific env vars
    )

    # File Upload Settings
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Home Theater Live")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local")

    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    BACKEND_API_URL: str = os.getenv(
        "BACKEND_API_URL", BACKEND_URL + API_V1_STR)

    # Directory settings with automatic creation
    STATIC_DIR: Path = BASE_DIR / "static"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    VIDEO_OUTPUT_DIR: Path = BASE_DIR.parent / "video_output"
    SOUNDFONTS_DIR: Path = STATIC_DIR / "soundfonts"

    GM2_SOUNDFONT_PATH: Path = SOUNDFONTS_DIR / "GM2_Map_Soundfont.sf2"

    # File settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/gif",
        "image/bmp", "image/tiff", "image/webp"
    ]

    # Video Processing
    DEFAULT_FPS: int = 30
    DEFAULT_RESOLUTION: tuple = (1920, 1080)  # Full HD
    OUTPUT_FORMAT: str = "mp4"

    # CORS
    FRONTEND_HOST: str = "http://localhost:5173"
    BACKEND_CORS_ORIGINS: Annotated[
        list[str] | str, BeforeValidator(parse_cors)
    ] = []

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "mht_dev_user"
    POSTGRES_PASSWORD: str = "mht_dev_pwd_108"
    POSTGRES_DB: str = "PG_MHT_DEV"

    # Email/SMTP
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_TEST_USER: EmailStr = "david.lee.remax@gmail.com"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        """Build database URI from components"""
        uri = PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

        # ADD THIS - see what you're actually connecting to
        print(f"Using database: {uri}")
        print(f"Host: {self.POSTGRES_SERVER}, User: {
              self.POSTGRES_USER}, DB: {self.POSTGRES_DB}")
        return uri

    @computed_field
    @property
    def all_cors_origins(self) -> list[str]:
        """Get all allowed CORS origins"""
        origins = []
        if isinstance(self.BACKEND_CORS_ORIGINS, list):
            origins.extend([str(origin).rstrip("/")
                           for origin in self.BACKEND_CORS_ORIGINS])
        elif isinstance(self.BACKEND_CORS_ORIGINS, str):
            origins.append(self.BACKEND_CORS_ORIGINS.rstrip("/"))
        origins.append(self.FRONTEND_HOST.rstrip("/"))
        return origins

    @computed_field
    @property
    def emails_enabled(self) -> bool:
        """Check if email functionality is enabled"""
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        """Set default email from name if not provided"""
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    @model_validator(mode="after")
    def _create_directories(self) -> Self:
        """Ensure required directories exist"""
        self.STATIC_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.SOUNDFONTS_DIR.mkdir(parents=True, exist_ok=True)
        return self

    @model_validator(mode="after")
    def _validate_backend_secrets(self) -> Self:
        """Backend-specific secret validation"""
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        return self


# Create settings instance
settings = BackendSettings()
