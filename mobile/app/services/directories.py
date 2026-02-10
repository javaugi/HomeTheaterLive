# mobile/app/services/directories.py
import os
import shutil
from pathlib import Path
from typing import Dict, Optional
import platform

class DirectoryService:
    """Service for managing mobile server directories"""
    
    def __init__(self):
        self.directories: Dict[str, Path] = {}
        self._setup_directories()
    
    def _setup_directories(self) -> None:
        """Setup all required directories"""
        # Get platform-specific base
        if platform.system() == "Windows":
            base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        elif platform.system() == "Darwin":  # macOS
            base = Path.home() / "Library" / "Application Support"
        else:  # Linux/Unix
            base = Path.home() / ".local" / "share"
        
        # Project directories
        project_base = base / "HomeTheaterLive" / "mobile"
        
        self.directories = {
            "project": project_base,
            "cache": project_base / "cache",
            "downloads": project_base / "downloads",
            "logs": project_base / "logs",
            "data": project_base / "data",
            "temp": Path("/tmp/hometheaterlive_mobile") if os.name == "posix" 
                    else Path(os.getenv("TEMP", "")) / "hometheaterlive_mobile",
            "uploads": project_base / "uploads",
            "thumbnails": project_base / "thumbnails",
        }
        
        # Create all directories
        for name, path in self.directories.items():
            path.mkdir(parents=True, exist_ok=True)
            print(f"DirectoryService: Created {name} -> {path}")
    
    def get_path(self, directory_type: str, filename: Optional[str] = None) -> Path:
        """Get path for directory type, optionally with filename"""
        if directory_type not in self.directories:
            raise ValueError(f"Unknown directory type: {directory_type}")
        
        path = self.directories[directory_type]
        if filename:
            return path / filename
        return path
    
    def ensure_exists(self, directory_type: str) -> Path:
        """Ensure directory exists and return path"""
        path = self.get_path(directory_type)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_cache_file(self, key: str) -> Path:
        """Get path for cache file"""
        cache_dir = self.ensure_exists("cache")
        # Create safe filename from key
        import hashlib
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return cache_dir / f"{safe_key}.cache"
    
    def get_download_path(self, filename: str) -> Path:
        """Get path for downloads"""
        downloads_dir = self.ensure_exists("downloads")
        return downloads_dir / filename
    
    def get_temp_file(self, prefix: str = "temp", suffix: str = "") -> Path:
        """Get temporary file path"""
        import uuid
        temp_dir = self.ensure_exists("temp")
        return temp_dir / f"{prefix}_{uuid.uuid4().hex}{suffix}"
    
    def cleanup_temp(self, max_age_hours: int = 24):
        """Cleanup old temporary files"""
        import time
        temp_dir = self.get_path("temp")
        current_time = time.time()
        
        for file in temp_dir.iterdir():
            if file.is_file():
                file_age = current_time - file.stat().st_mtime
                if file_age > max_age_hours * 3600:
                    file.unlink()
                    print(f"DirectoryService: Cleaned up temp file: {file.name}")
    
    def get_directory_info(self) -> Dict[str, str]:
        """Get information about all directories"""
        info = {}
        for name, path in self.directories.items():
            if path.exists():
                try:
                    # Get directory size (recursive)
                    total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                    file_count = sum(1 for f in path.rglob('*') if f.is_file())
                    info[name] = {
                        "path": str(path),
                        "size_mb": total_size / (1024 * 1024),
                        "files": file_count,
                        "exists": True
                    }
                except:
                    info[name] = {"path": str(path), "exists": True, "error": "Could not read"}
            else:
                info[name] = {"path": str(path), "exists": False}
        
        return info


# Singleton instance
directory_service = DirectoryService()# -*- coding: utf-8 -*-

