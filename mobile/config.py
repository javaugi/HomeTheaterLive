# mobile/config.py
from typing import Optional, Self
from pathlib import Path
from pydantic_settings import SettingsConfigDict
from pydantic import model_validator
import os

from shared.config import BaseSettingsConfig


class MobileSettings(BaseSettingsConfig):
    """Mobile-specific settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env.mobile",  # Mobile-specific env file
        env_ignore_empty=True,
        extra="ignore",
        env_prefix="MOBILE_",  # Optional: prefix for mobile-specific env vars
    )
    
    PROJECT_NAME = os.getenv("PROJECT_NAME", "Home Theater Live")
    API_V1_STR = os.getenv("API_V1_STR", "/api/v1")
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")    

    API_TIMEOUT_SECONDS: int = 30
    SOCKET_HOST: str = "localhost"
    SOCKET_PORT: int = 5000
    
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
    
    @model_validator(mode="after")
    def _set_mobile_directories(self) -> Self:
        """Set up mobile-specific directories"""
        # These would be set based on the mobile platform
        # For Kivy/KivyMD example:
        if self.CACHE_DIR is None:
            from kivy.app import App
            app = App.get_running_app()
            if app:
                self.CACHE_DIR = Path(app.user_data_dir) / "cache"
                self.DOWNLOADS_DIR = Path(app.user_data_dir) / "downloads"
        
        # Create directories if they exist
        if self.CACHE_DIR:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if self.DOWNLOADS_DIR:
            self.DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        
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

