import os
import shutil
import tempfile
from fastapi import UploadFile, HTTPException
from typing import List
import magic

from app.core.config import settings


def ensure_directories():
    """Ensure all required directories exist"""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.STATIC_DIR, exist_ok=True)
    os.makedirs("processed_videos", exist_ok=True)


async def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """Save an uploaded file to disk"""
    filename = upload_file.filename or "unknown"
    file_path = os.path.join(destination, filename)

    with open(file_path, "wb") as buffer:
        content = await upload_file.read()
        buffer.write(content)
        await upload_file.seek(0)  # Reset file pointer

    return file_path


def validate_image_files(files: List[UploadFile]):
    """Validate uploaded image files"""
    for file in files:
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset pointer

        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} exceeds maximum size"
            )

        # Check MIME type
        mime_type = magic.from_buffer(file.file.read(1024), mime=True)
        file.file.seek(0)  # Reset pointer

        if mime_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} has unsupported type: {mime_type}"
            )


def create_temp_directory(prefix: str="image2video_") -> str:
    """Create a temporary directory for uploaded files"""
    try:
        temp_dir = tempfile.mkdtemp(prefix)
        print(f"app/utils/file_utils create_temp_directory prefix={prefix}, temp_dir={temp_dir}")
        return temp_dir
    except PermissionError as e:
        # Fallback to current directory
        fallback_dir = os.path.join(os.getcwd(), "temp_frames")
        os.makedirs(fallback_dir, exist_ok=True)
        print(f"Permission denied error {e}- app/utils/file_utils create_temp_directory prefix={prefix}. \n Try running with appropriate permissions. fallback_dir={fallback_dir}")
        return fallback_dir
    except OSError as e:
        print(f"OS error: {e}")
        # Try alternative location
        fallback_dir = os.path.join(os.path.expanduser("~"), "temp_frames")
        os.makedirs(fallback_dir, exist_ok=True)
        print(f"OS error: {e}- app/utils/file_utils create_temp_directory prefix={prefix}. \n Try running with appropriate permissions. fallback_dir={fallback_dir}")
        return fallback_dir

def cleanup_temp_directory(prefix="image2video_", max_age_hours=24):
    temp_base = tempfile.gettempdir()
    import time
    current_time = time.time()
    
    for item in os.listdir(temp_base):
        if item.startswith(prefix) or item.startswith("temp_frames"):
            item_path = os.path.join(temp_base, item)
            if os.path.isdir(item_path):
                # Check if older than max_age_hours
                age = current_time - os.path.getctime(item_path)
                if age > max_age_hours * 3600:
                    try:
                        shutil.rmtree(item_path)
                        print(f"app/utils/file_utils cleanup_temp_directory Removed old temp dir: {item_path}")
                    except:
                        pass
