# backend/app/crud/processing_status.py
print(">>> importing backend/app/crud/processing_status.py")
from sqlalchemy.orm import Session
#from sqlalchemy import desc
from app.models import ProcessingStatusDB
from app.model.schemas import ProcessingStatusCreate, ProcessingStatusUpdate
from datetime import datetime
print(">>> importing backend/app/crud/processing_status.py done")

class ProcessingStatusCRUD:
    @staticmethod
    def create(db: Session, status_data: ProcessingStatusCreate) -> ProcessingStatusDB:
        db_status = ProcessingStatusDB(
            job_id=status_data.job_id,
            status=status_data.status,
            progress=status_data.progress,
            message=status_data.message,
            video_url=status_data.video_url,
            created_at=status_data.created_at,
            completed_at=status_data.completed_at,
            error=status_data.error
        )
        db.add(db_status)
        db.commit()
        db.refresh(db_status)
        return db_status
    
    @staticmethod
    def get_by_job_id(db: Session, job_id: str) -> ProcessingStatusDB:
        return db.query(ProcessingStatusDB).filter(
            ProcessingStatusDB.job_id == job_id
        ).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(ProcessingStatusDB).offset(skip).limit(limit).all()
    
    @staticmethod
    def update(
        db: Session, 
        job_id: str, 
        update_data: ProcessingStatusUpdate
    ) -> ProcessingStatusDB:
        db_status = ProcessingStatusCRUD.get_by_job_id(db, job_id)
        if not db_status:
            return None
        
        # Update only provided fields
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_status, key, value)
        
        db.commit()
        db.refresh(db_status)
        return db_status
    
    @staticmethod
    def update_progress(
        db: Session, 
        job_id: str, 
        progress: int, 
        message: str = None
    ) -> ProcessingStatusDB:
        db_status = ProcessingStatusCRUD.get_by_job_id(db, job_id)
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
    def mark_failed(
        db: Session, 
        job_id: str, 
        error_message: str
    ) -> ProcessingStatusDB:
        db_status = ProcessingStatusCRUD.get_by_job_id(db, job_id)
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
        db_status = ProcessingStatusCRUD.get_by_job_id(db, job_id)
        if not db_status:
            return False
        
        db.delete(db_status)
        db.commit()
        return True# -*- coding: utf-8 -*-

