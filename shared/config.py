# shared/config.py
import secrets
import warnings
from typing import Literal
from pathlib import Path

from pydantic import HttpUrl, EmailStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


class BaseSettingsConfig(BaseSettings):
    """Base settings shared across all modules"""
    
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    
    # Project Info
    PROJECT_NAME: str = "Home Theater Live"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    
    # API Settings
    ENV_FILE_LOC: str = "../.env"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    
    # Base directories (relative paths)
    PROJ_DIR: Path = Path(__file__).resolve().parent.parent
    
    # Timing/Expiration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Security
    FIRST_SUPERUSER: EmailStr = "david.lee.remax@gmail.com"
    FIRST_SUPERUSER_PASSWORD: str = "Jiaxiang1@8"
    
    # Monitoring
    SENTRY_DSN: HttpUrl | None = None
    
    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        """Warn or raise error for default secrets"""
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)
    
    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        """Validate that secrets are not default values"""
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )
        return self
