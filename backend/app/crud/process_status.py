# backend/app/crud/process_status.py
print(">>> importing backend/app/crud/process_status.py")
from sqlalchemy.orm import Session
from typing import Optional
#from sqlalchemy import desc
from datetime import datetime


from app.model.process_status import ProcessStatusDB
from app.model.schemas import ProcessStatusCreate, ProcessStatusUpdate

#from app.db.database import SessionLocal  # Import your session factory
"""
1. Depends(get_db) dependency is designed for request/response cycle, not background tasks
2. The request session might be closed when the background task runs
3. Sessions aren't thread-safe
4. pass SessionLocal instead of db or get_db.
"""

print(">>> importing backend/app/crud/process_status.py done")

class ProcessStatusCRUD:

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

        db.add(db_status)
        db.commit()
        db.refresh(db_status)
        return db_status


    def get_by_job_id(db: Session, job_id: str) -> Optional[ProcessStatusDB]:
        if db is None:
            raise ValueError("Database session is None")
        if not hasattr(db, 'query'):
            raise TypeError(f"db is not a SQLAlchemy Session: {type(db)} - {db}")

        try:
            print(f"Querying for job_id={job_id} using session id={id(db)}")
            db_status = (
                db.query(ProcessStatusDB)
                .filter(ProcessStatusDB.job_id == job_id)
                .first()
            )
            print(f"Found: {db_status is not None}")
            return db_status
        except Exception as e:
            print(f"Query failed: {type(e).__name__}: {str(e)}")
            raise

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(ProcessStatusDB).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, job_id: str, update_data: ProcessStatusUpdate) -> ProcessStatusDB:
        db_status = ProcessStatusCRUD.get_by_job_id(db, job_id)
        if not db_status:
            return None

        # Update only provided fields
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            if value:
                setattr(db_status, key, value)

        db.commit()
        db.refresh(db_status)
        print(f"ProcessStatusCRUD update job_id={job_id}, \n update_data={update_data}, \n update_dict={update_dict} \n db_status={db_status}")
        return db_status

    @staticmethod
    def update_progress(db: Session, job_id: str, progress: int=10, message: str = None) -> ProcessStatusDB:
        db_status = ProcessStatusCRUD.get_by_job_id(db, job_id)
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

        db.commit()
        db.refresh(db_status)
        return db_status

    @staticmethod
    def mark_failed(db: Session, job_id: str, error_message: str) -> ProcessStatusDB:
        db_status = ProcessStatusCRUD.get_by_job_id(db, job_id)
        if not db_status:
            return None

        db_status.status = "failed"
        db_status.error = error_message
        db_status.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(db_status)
        return db_status

    @staticmethod
    def delete(db: Session, job_id: str) -> bool:
        db_status = ProcessStatusCRUD.get_by_job_id(db, job_id)
        if not db_status:
            return False

        db.delete(db_status)
        db.commit()
        return True# -*- coding: utf-8 -*-

