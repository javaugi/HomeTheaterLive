# mobile/app/core/dependencies.py
from pathlib import Path

def get_cache_dir() -> Path:
    """Dependency to get cache directory"""
    from app.core.config import settings
    return settings.CACHE_DIR

def get_downloads_dir() -> Path:
    """Dependency to get downloads directory"""
    from app.core.config import settings
    return settings.DOWNLOADS_DIR

def get_temp_dir() -> Path:
    """Dependency to get temp directory"""
    import tempfile
    temp_root = Path(tempfile.gettempdir()) / "hometheaterlive_mobile"
    temp_root.mkdir(exist_ok=True)
    return temp_root

