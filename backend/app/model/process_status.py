print(">>> importing #backend/app/model/video_job.py")
import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
import enum

#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
Base = declarative_base()

print(">>> importing #backend/app/model/video_job.py done ")

class ProcessStatuses(str, enum.Enum):
    pending = 'pending'
    processing = 'processing'
    completed = 'completed'
    failed = 'failed'


class MediaTypes(str, enum.Enum):
    text_html = 'text/html'
    text_plain = 'text/plain'
    application_json = 'application/json'
    application_pdf = 'application/pdf'
    image_jpeg = 'image/jpeg'
    image_gif = 'image/gif'
    image_png = 'image/png'
    image_apng = 'image/apng'
    image_avif = 'image/avif'
    audio_mpeg = 'audio/mpeg'
    audio_ogg = 'audio/ogg'
    audio_midi = 'audio/midi'
    audio_aac = 'audio/aac'
    video_mp4 = 'video/mp4'
    video_quicktime = 'video/quicktime'
    video_x_msvideo = 'video/x-msvideo'
    video_ogg = 'video/ogg'
    video_webm = 'video/webm'
    video_3gpp = 'video/3gpp'
    video_3gpp2 = 'video/3gpp2'

class ProcessStatusDB(Base):
    __tablename__ = "process_status"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: uuid.uuid4().hex)
    job_id = Column(String, nullable=False, index=True, unique=True)
    status = Column(Enum(ProcessStatuses), index=True, nullable=False, default=ProcessStatuses.pending)
    progress = Column(Integer, default=0)
    message = Column(Text, nullable=True)
    video_url = Column(String, nullable=True)
    video_path = Column(String, nullable=True)
    filename = Column(String, nullable=True)
    media_type = Column(Enum(MediaTypes), index=True, nullable=True, default=MediaTypes.video_mp4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"ProcessStatusDB(id={self.id}, job_id={self.job_id}, \n \
            status={self.status}, progress={self.progress}, message={self.message} \n \
            video_url={self.video_url}, video_path={self.video_path}, filename={self.filename} )"

"""
return {
    'job_id': None,
    'status': 'failed',
    'progress': 10,
    'message': None

}
"""