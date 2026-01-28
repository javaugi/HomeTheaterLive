# -*- coding: utf-8 -*-
print(">>> importing #backend/app/model/video_job.py")
from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime
from app.db.base import Base
print(">>> importing #backend/app/model/video_job.py done")


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id = Column(String, primary_key=True, index=True)
    status = Column(String, index=True)   # processing | done | failed
    message = Column(Text, nullable=True)
    video_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)