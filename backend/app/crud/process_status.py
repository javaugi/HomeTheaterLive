# backend/app/crud/process_status.py
print(">>> importing backend/app/crud/process_status.py")
from sqlalchemy.orm import Session
#from sqlalchemy import desc
from datetime import datetime


from app.model.process_status import ProcessStatusDB
from app.model.schemas import ProcessStatusCreate, ProcessStatusUpdate

from app.core.db import SessionLocal  # Import your session factory
"""
1. Depends(get_db) dependency is designed for request/response cycle, not background tasks
2. The request session might be closed when the background task runs
3. Sessions aren't thread-safe
4. pass SessionLocal instead of db or get_db.
"""

print(">>> importing backend/app/crud/process_status.py done")

class ProcessStatusCRUD:
    @staticmethod
    def getSessionDb(db: Session):
        # Check if db is a factory or a session
        if hasattr(db, 'query'):  # It's a Session
            session = db
        else:  # It's a factory or Depends object
            session = db() if callable(db) else SessionLocal()

        return session

    @staticmethod
    def create(db: Session, status_data: ProcessStatusCreate) -> ProcessStatusDB:
        db_status = ProcessStatusDB(
            job_id=status_data.job_id,
            status=status_data.status,
            progress=status_data.progress,
            message=status_data.message,
            video_url=status_data.video_url,
            video_path=status_data.video_path,
            filename=status_data.filename,
            media_type=status_data.media_type,
            created_at=status_data.created_at,
            completed_at=status_data.completed_at,
            error=status_data.error,
            notes=status_data.notes
        )

        session = ProcessStatusCRUD.getSessionDb(db)
        session.add(db_status)
        session.commit()
        session.refresh(db_status)
        return db_status


    @staticmethod
    def get_by_job_id(db: Session, job_id: str) -> ProcessStatusDB:
        session = ProcessStatusCRUD.getSessionDb(db)

        return session.query(ProcessStatusDB).filter(
            ProcessStatusDB.job_id == job_id
        ).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        session = ProcessStatusCRUD.getSessionDb(db)

        return session.query(ProcessStatusDB).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, job_id: str, update_data: ProcessStatusUpdate) -> ProcessStatusDB:
        session = ProcessStatusCRUD.getSessionDb(db)

        db_status = ProcessStatusCRUD.get_by_job_id(session, job_id)
        if not db_status:
            return None

        # Update only provided fields
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_status, key, value)

        session.commit()
        session.refresh(db_status)
        return db_status

    @staticmethod
    def update_progress(db: Session, job_id: str, progress: int=10, message: str = None) -> ProcessStatusDB:
        session = ProcessStatusCRUD.getSessionDb(db)

        db_status = ProcessStatusCRUD.get_by_job_id(session, job_id)
        if not db_status:
            return None

        db_status.progress = progress
        if message:
            db_status.message = message

        if progress >= 100:
            db_status.status = "completed"
            db_status.completed_at = datetime.utcnow()
        elif db_status.status == "pending":
            db_status.status = "processing"

        session.commit()
        session.refresh(db_status)
        return db_status

    @staticmethod
    def mark_failed(db: Session, job_id: str, error_message: str) -> ProcessStatusDB:
        session = ProcessStatusCRUD.getSessionDb(db)

        db_status = ProcessStatusCRUD.get_by_job_id(session, job_id)
        if not db_status:
            return None

        db_status.status = "failed"
        db_status.error = error_message
        db_status.completed_at = datetime.utcnow()

        session.commit()
        session.refresh(db_status)
        return db_status

    @staticmethod
    def delete(db: Session, job_id: str) -> bool:
        session = ProcessStatusCRUD.getSessionDb(db)

        db_status = ProcessStatusCRUD.get_by_job_id(session, job_id)
        if not db_status:
            return False

        session.delete(db_status)
        session.commit()
        return True# -*- coding: utf-8 -*-

