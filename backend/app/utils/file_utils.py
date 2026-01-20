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


def create_temp_directory() -> str:
    """Create a temporary directory for uploaded files"""
    return tempfile.mkdtemp(prefix="image2video_")


def cleanup_temp_directory(directory: str):
    """Clean up temporary directory"""
    if os.path.exists(directory):
        shutil.rmtree(directory)