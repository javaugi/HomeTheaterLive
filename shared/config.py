# shared/config.py
import secrets
import warnings
from typing import Literal
from pathlib import Path
import os

from pydantic import HttpUrl, EmailStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

"""
Where is the value from in this command :
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "127.0.0.1"):
    1. System environment variables - set in your OS or shell
    2. Docker/container environment variables - if running in containers
    3. Process environment - set by whatever process runs your Python app

Will it read from .env files?
    No, not automatically. The os.getenv() function only reads from the actual 
        OS environment variables, not directly from .env, .env_mobile, or .env_backend files.      

To make it work with .env files:
    You need to load the .env file first using a package like python-dotenv:

python
    from dotenv import load_dotenv
    import os
    
    # Load the specific .env file you want
    load_dotenv('.env')  # or '.env_mobile' or '.env_backend'
    
    # Now this will read from the loaded .env file
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "127.0.0.1")     

Common patterns:
# Load based on environment
    import os
    from dotenv import load_dotenv
    
    env = os.getenv('ENV', 'development')
    if env == 'mobile':
        load_dotenv('.env_mobile')
    elif env == 'backend':
        load_dotenv('.env_backend')
    else:
        load_dotenv('.env')
    
    BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")    
"""


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

    USE_BACKEND_API_CALL: bool = os.getenv("USE_BACKEND_API_CALL", True)
    USE_PATH_DOWNLOAD_CALL: bool = os.getenv("USE_PATH_DOWNLOAD_CALL", False)

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
