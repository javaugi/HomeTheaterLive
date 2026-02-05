print(">>> importing #backend/app/model/video_job.py")
import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import enum
print(">>> importing #backend/app/model/video_job.py done ")

Base = declarative_base()

class VideoJobStatus(str, enum.Enum):
    pending = 'pending'
    processing = 'processing'
    completed = 'completed'
    failed = 'failed'
    
class VideoJob(Base):
    __tablename__ = "video_jobs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: uuid.uuid4().hex)
    job_id = Column(String, nullable=False, index=True, unique=True)
    status = Column(Enum(VideoJobStatus), index=True, nullable=False, default=VideoJobStatus.pending)
    progress = Column(Integer, default=0)
    message = Column(Text, nullable=True)
    video_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)

    def __repr__(self):
        return f"VideoJob(id={self.id}, job_id={self.job_id}, status={self.status})"