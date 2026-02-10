# mobile/app/config.py
from typing import Optional, Self
from pathlib import Path
from sqlmodel import Field
from pydantic_settings import SettingsConfigDict
from pydantic import model_validator, computed_field
import os
import platform
import sys


# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from shared.config import BaseSettingsConfig


class MobileSettings(BaseSettingsConfig):
    """Mobile-specific settings"""
    model_config = SettingsConfigDict(
        env_file=".env.mobile",  # Mobile-specific env file
        env_ignore_empty=True,
        extra="ignore",
        env_prefix="MOBILE_",  # Optional: prefix for mobile-specific env vars
    )

    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Home Theater Live")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8001")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    API_TIMEOUT_SECONDS: int = 30
    SOCKET_HOST: str = "localhost"
    SOCKET_PORT: int = 5000

    """
    MOBILE_HOST: str = "0.0.0.0"
    MOBILE_PORT: int = 8001
    MOBILE_WORKERS: int = 1
    MOBILE_RELOAD: bool = True
    BACKEND_HOST: str = "localhost"
    BACKEND_PORT: int = 8000  # Backend runs on 8000
    BACKEND_URL: str = "http://localhost:8000"
    """

    # Mobile-specific settings
    MOBILE_CACHE_SIZE: int = 100  # Number of items to cache
    OFFLINE_MODE_ENABLED: bool = True
    PUSH_NOTIFICATIONS_ENABLED: bool = True

    # File handling (different from backend)
    MOBILE_UPLOAD_CHUNK_SIZE: int = 1024 * 1024  # 1MB chunks
    MOBILE_MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB for mobile

    # Local storage paths (platform-specific)
    CACHE_DIR: Optional[Path] = None
    DOWNLOADS_DIR: Optional[Path] = None

    # Authentication
    TOKEN_STORAGE_KEY: str = "access_token"
    REFRESH_TOKEN_STORAGE_KEY: str = "refresh_token"

    # UI/UX
    DEFAULT_PAGE_SIZE: int = 20
    PULL_TO_REFRESH_ENABLED: bool = True


    # Directory settings with sensible defaults
    CACHE_DIR: Optional[Path] = None
    DOWNLOADS_DIR: Optional[Path] = None
    LOGS_DIR: Optional[Path] = None
    DATA_DIR: Optional[Path] = None
   # Directory paths with environment variable support
    MOBILE_CACHE_DIR: Path = Field(
        default_factory=lambda: Path(
            os.getenv("MOBILE_CACHE_DIR",
                     Path.home() / ".hometheaterlive" / "mobile" / "cache")
        )
    )

    MOBILE_DOWNLOADS_DIR: Path = Field(
        default_factory=lambda: Path(
            os.getenv("MOBILE_DOWNLOADS_DIR",
                     Path.home() / ".hometheaterlive" / "mobile" / "downloads")
        )
    )

    MOBILE_DATA_DIR: Path = Field(
        default_factory=lambda: Path(
            os.getenv("MOBILE_DATA_DIR",
                     Path.home() / ".hometheaterlive" / "mobile" / "data")
        )
    )

    # Mobile API server settings
    MOBILE_HOST: str = "0.0.0.0"
    MOBILE_PORT: int = 8001
    MOBILE_WORKERS: int = 1
    MOBILE_RELOAD: bool = Field(default_factory=lambda: os.getenv("ENVIRONMENT") == "local")

    @computed_field
    @property
    def backend_api_url(self) -> str:
        """Get full backend API URL"""
        return f"http://{self.BACKEND_HOST}:{self.BACKEND_PORT}"

    @model_validator(mode="after")
    def _set_mobile_directories(self) -> Self:
        """Setup mobile server directories"""
        print("\nDEBUG: Setting up mobile directories...")

        # Determine platform-specific base directory
        if platform.system() == "Windows":
            base_dir = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        elif platform.system() == "Darwin":  # macOS
            base_dir = Path.home() / "Library" / "Application Support"
        else:  # Linux/Unix
            base_dir = Path.home() / ".local" / "share"

        # Project-specific directory
        project_dir = base_dir / "HomeTheaterLive" / "mobile"

        # Set directories if not explicitly configured
        if self.CACHE_DIR is None:
            self.CACHE_DIR = project_dir / "cache"
            print(f"DEBUG: Cache directory set to: {self.CACHE_DIR}")

        if self.DOWNLOADS_DIR is None:
            self.DOWNLOADS_DIR = project_dir / "downloads"
            print(f"DEBUG: Downloads directory set to: {self.DOWNLOADS_DIR}")

        if self.LOGS_DIR is None:
            self.LOGS_DIR = project_dir / "logs"
            print(f"DEBUG: Logs directory set to: {self.LOGS_DIR}")

        if self.DATA_DIR is None:
            self.DATA_DIR = project_dir / "data"
            print(f"DEBUG: Data directory set to: {self.DATA_DIR}")

        # Create all directories
        for dir_path in [self.CACHE_DIR, self.DOWNLOADS_DIR, self.LOGS_DIR, self.DATA_DIR]:
            if dir_path:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"DEBUG: Directory ensured: {dir_path} (exists: {dir_path.exists()})")

        return self

    @model_validator(mode="after")
    def _validate_mobile_settings(self) -> Self:
        """Mobile-specific validation"""
        if self.API_TIMEOUT_SECONDS < 5:
            raise ValueError("API timeout must be at least 5 seconds")
        if self.MOBILE_CACHE_SIZE <= 0:
            raise ValueError("Cache size must be positive")
        return self


# Create settings instance
settings = MobileSettings()# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

