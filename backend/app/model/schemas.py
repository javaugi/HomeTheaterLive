# backend/app/model/schemas.py
print(">>> importing #backend/app/model/schemas.py")
from pydantic import BaseModel, Field
from typing import Optional, List, Tuple
from datetime import datetime
from enum import Enum
print(">>> importing #backend/app/model/schemas.py done")


""" ProcessingStatus or ProcessStatusBase """
class ProcessingStatus(BaseModel):
    job_id: str
    status: str  # processing, completed, failed
    progress: int = Field(ge=0, le=100)
    message: str
    video_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class ProcessStatusBase(BaseModel):
    job_id: str
    status: str  # processing, completed, failed
    progress: int = Field(ge=0, le=100)
    message: str
    video_url: Optional[str] = None
    video_path: Optional[str] = None
    filename: Optional[str] = None
    media_type: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    notes: Optional[str] = None

class ProcessStatusCreate(ProcessStatusBase):
    pass

class ProcessStatusUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    message: Optional[str] = None
    video_url: Optional[str] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class ProcessStatusResponse(ProcessStatusBase):
    id: str
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # For SQLAlchemy compatibility
""" ProcessingStatus """

class TransitionType(str, Enum):
    NONE = "none"
    FADE = "fade"
    SLIDE = "slide"
    ZOOM = "zoom"

class VideoSettings(BaseModel):
    fps: int = Field(default=30, ge=1, le=120)
    resolution: Optional[Tuple[int, int]] = None
    transition_type: TransitionType = TransitionType.NONE
    duration_per_image: float = Field(default=2.0, ge=0.5, le=10.0)

class DirectoryProcessRequest(BaseModel):
    directory_path: str
    video_settings: VideoSettings = Field(default_factory=VideoSettings)

class VideoCreate(BaseModel):
    image_paths: List[str]
    settings: VideoSettings = Field(default_factory=VideoSettings)

class VideoResponse(BaseModel):
    job_id: str
    status: str
    message: str
    video_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

