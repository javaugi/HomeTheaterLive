#Endpoints
print(">>> importing #Endpoints")
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List
import os
import uuid
from datetime import datetime
import json
import asyncio

from app.core.config import settings

from app.model.schemas import (
    DirectoryProcessRequest, VideoSettings
)

from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.model.process_status import ProcessStatuses
from app.model.schemas import ProcessStatusCreate, ProcessStatusResponse, ProcessStatusUpdate
from app.crud.process_status import ProcessStatusCRUD

router = APIRouter(tags=["endpoints"])
# In-memory storage for processing status (use Redis in production)

print(">>> importing #Endpoints done")


@router.post("/process/directory", response_model=ProcessStatusResponse)
async def process_directory(
        request: DirectoryProcessRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    """Process images from a directory"""
    try:
        # Validate directory exists
        if not os.path.exists(request.directory_path):
            raise HTTPException(status_code=400, detail="Directory does not exist")

        # Create a unique job ID
        job_id = str(uuid.uuid4())
        print(f"Endpoints process_directory job_id={job_id}, request.directory_path={request.directory_path}")
        # Create initial status record
        status_data = ProcessStatusCreate(
            job_id=job_id,
            status=ProcessStatuses.pending,
            progress=10,
            message="Job created, waiting to start...",
            created_at=datetime.utcnow()
        )

        db_status = ProcessStatusCRUD.create(db, status_data)
        print(f"Endpoints process_directory db_status={db_status}")


        background_tasks.add_task(
            run_async,
            process_video_task(job_id, request.directory_path, request.video_settings)
        )

        db_status = ProcessStatusCRUD.get_by_job_id(db, job_id)
        print(f"Endpoints process_directory return db_status={db_status}")

        #return db_status - using the response model
        return ProcessStatusResponse.from_orm(db_status)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_async(coro):
    asyncio.create_task(coro)

@router.post("/process/upload", response_model=ProcessStatusResponse)
async def process_uploaded_images(
        files: List[UploadFile] = File(...),
        background_tasks: BackgroundTasks = None,
        db: Session = Depends(get_db)
):
    """Process uploaded images"""
    try:
        # Parse settings
        try:
            video_settings = VideoSettings(**json.loads(settings))
        except:
            video_settings = VideoSettings()

        # Validate files
        from app.utils.file_utils import validate_image_files
        validate_image_files(files)

        # Create temp directory for uploaded files
        from app.utils.file_utils import create_temp_directory
        temp_dir = create_temp_directory()

        # Save uploaded files
        saved_paths = []


        from app.utils.file_utils import save_upload_file
        for i, file in enumerate(files):
            file_path = await save_upload_file(file, temp_dir)
            saved_paths.append(file_path)

        # Create job ID
        job_id = str(uuid.uuid4())
        print(f"Endpoints process_uploaded_images job_id={job_id}, saved_paths={len(saved_paths)}")
        status_data = ProcessStatusCreate(
            job_id=job_id,
            status=ProcessStatuses.pending,
            progress=10,
            message="Processing {len(saved_paths)} images...",
            created_at=datetime.utcnow()
        )

        db_status = ProcessStatusCRUD.create(db, status_data)
        print(f"Endpoints process_uploaded_images db_status={db_status}")

        # Process in background
        background_tasks.add_task(
            process_upload_task,
            job_id,
            saved_paths,
            video_settings,
            temp_dir
        )


        db_status = ProcessStatusCRUD.get_by_job_id(db, job_id)
        print(f"Endpoints process_uploaded_images return db_status={db_status}")
        #return db_status - using the response model
        return ProcessStatusResponse.from_orm(db_status)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=ProcessStatusResponse)
async def get_process_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get processing status for a job"""
    try:
        db_status = ProcessStatusCRUD.get_by_job_id(db, job_id)
        print(f"Endpoints get_process_status job_id={job_id}, db_status={db_status}")
        if not db_status:
            raise HTTPException(status_code=404, detail="Error get_process_status - Job not found")

        return db_status
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error Job not found get_process_status {str(e)}")




@router.get("/video/{filename}", response_model=ProcessStatusResponse)
async def get_video_file(filename: str,
    db: Session = Depends(get_db)
):
    """Serve video file"""
    from app.core.video_processor import get_video_processor
    video_path = os.path.join(get_video_processor().output_dir, filename)

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")

    # Create job ID
    job_id = str(uuid.uuid4())
    print(f"Endpoints get_video_file job_id={job_id}, filename={filename}, video_path={video_path}")
    status_data = ProcessStatusCreate(
        job_id=job_id,
        status=ProcessStatuses.completed,
        progress=100,
        message="Got video file {filename} at path {video_path}",
        video_path=video_path,
        filename=filename,
        media_type="video/mp4",
        created_at=datetime.utcnow()
    )

    db_status = ProcessStatusCRUD.create(db, status_data)
    print(f"Endpoints get_video_file db_status={db_status}")
    #return db_status - using the response model
    return ProcessStatusResponse.from_orm(db_status)

@router.get("/videos")
async def list_videos():
    """List all available videos"""
    videos = []

    from app.core.video_processor import get_video_processor
    for filename in os.listdir(get_video_processor().output_dir):
        if filename.endswith('.mp4'):
            filepath = os.path.join(get_video_processor().output_dir, filename)
            stat = os.stat(filepath)

            videos.append({
                "filename": filename,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "url": f"/api/v1/video/{filename}"
            })

    return {"videos": videos}


@router.delete("/video/{filename}")
async def delete_video(filename: str):
    """Delete a video file"""
    from app.core.video_processor import get_video_processor
    video_path = os.path.join(get_video_processor().output_dir, filename)

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")

    os.remove(video_path)
    return {"message": "Video deleted successfully"}


# Background task functions
async def process_video_task(job_id: str,
    directory_path: str,
    settings: VideoSettings,
    db: Session = Depends(get_db)
):
    """Background task for processing directory"""
    try:
        db_status = ProcessStatusCRUD.update(
            db,
            job_id,
            ProcessStatusUpdate(status="processing",
                    progress=12,
                    message="Scanning directory and processing for images..."
                )
        )
        print(f"Endpoints process_video_task job_id={job_id}, db_status={db_status}")

        # Create video
        output_filename = f"{job_id}.mp4"
        from app.core.video_processor import get_video_processor
        video_path = await get_video_processor().process_images_to_video(
            image_paths=[],  # Will be read from directory
            output_filename=output_filename,
            fps=settings.fps,
            resolution=settings.resolution,
            transition_type=settings.transition_type,
            duration_per_image=settings.duration_per_image
        )
        print(f"Endpoints process_video_task 1 video_path={video_path}")

        # Use the directory method
        video_path = get_video_processor().create_video_from_directory(
            directory=directory_path,
            fps=settings.fps,
            resolution=settings.resolution,
            output_filename=output_filename,
            transition_type=settings.transition_type,
            duration_per_image=settings.duration_per_image
        )
        print(f"Endpoints process_video_task 2 video_path={video_path}")

        # Update status
        db_status = ProcessStatusCRUD.update(
            db,
            job_id,
            ProcessStatusUpdate(
                status=ProcessStatuses.completed,
                progress=100,
                message="Video created successfully",
                video_url=f"/api/v1/video/{output_filename}",
                filename=output_filename,
                completed_at=datetime.utcnow()
            )
        )
        print(f"Endpoints process_video_task completed db_status={db_status}")

    except Exception as e:
        db_status = ProcessStatusCRUD.update(
            db,
            job_id,
            ProcessStatusUpdate(
                status=ProcessStatuses.failed,
                progress=100,
                message=str(e),
                error=str(e),
                completed_at=datetime.utcnow()
            )
        )
        print(f"Endpoints process_video_task error db_status={db_status}")


async def process_upload_task(job_id: str,
    image_paths: List[str],
    settings: VideoSettings,
    temp_dir: str,
    db: Session = Depends(get_db)
):
    """Background task for processing uploaded files"""
    try:
        db_status = ProcessStatusCRUD.update(
            db,
            job_id,
            ProcessStatusUpdate(
                    status="processing",
                    progress=14,
                    message="Processing images..."
                )
        )
        print(f"Endpoints process_upload_task job_id={job_id}, db_status={db_status}")

        output_filename = f"{job_id}.mp4"
        from app.core.video_processor import get_video_processor
        video_path = await get_video_processor().process_images_to_video(
            image_paths=image_paths,
            output_filename=output_filename,
            fps=settings.fps,
            resolution=settings.resolution,
            transition_type=settings.transition_type,
            duration_per_image=settings.duration_per_image
        )
        print(f"Endpoints process_upload_task video_path={video_path}")

        # Update status
        db_status = ProcessStatusCRUD.update(
            db,
            job_id,
            ProcessStatusUpdate(
                status=ProcessStatuses.completed,
                progress=100,
                message="Video created successfully",
                video_url=f"/api/v1/video/{output_filename}",
                filename=output_filename,
                completed_at=datetime.utcnow()
            )
        )
        print(f"Endpoints process_upload_task completed db_status={db_status}")

        # Cleanup temp directory
        from app.utils.file_utils import cleanup_temp_directory
        cleanup_temp_directory(temp_dir)

    except Exception as e:
        db_status = ProcessStatusCRUD.update(
            db,
            job_id,
            ProcessStatusUpdate(
                status=ProcessStatuses.failed,
                progress=100,
                message=str(e),
                error=str(e),
                completed_at=datetime.utcnow()
            )
        )
        # Cleanup on error too
        from app.utils.file_utils import cleanup_temp_directory
        cleanup_temp_directory(temp_dir)
        print(f"Endpoints process_upload_task error db_status={db_status}")

@router.post("/videos/create", response_model=ProcessStatusResponse)
async def create_video(
    files: List[UploadFile] = File(...),
    fps: int = Form(30),
    duration_per_image: float = Form(2.0),
    transition_type: str = Form("none"),
    resolution_width: int = Form(1920),
    resolution_height: int = Form(1080),
    quality: str = Form("high"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """API endpoint to create video from uploaded images"""
    try:
        # Create job ID
        job_id = str(uuid.uuid4())
        print(f"Endpoints create_video, job_id={job_id}, fps={fps}, files={len(files)}")

        # Create temp directory for uploaded files
        temp_dir = os.path.join("temp_uploads", job_id)
        os.makedirs(temp_dir, exist_ok=True)

        # Save uploaded files
        saved_paths = []
        for file in files:
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            saved_paths.append(file_path)


        # Create initial status record
        status_data = ProcessStatusCreate(
            job_id=job_id,
            status=ProcessStatuses.pending,
            progress=5,
            message=f"Endpoints create_video job_id {job_id} Uploading {len(files)} images ",
            video_path=temp_dir,
            created_at=datetime.utcnow()
        )
        print(f"Endpoints calling ProcessStatusCRUD.create, job_id={job_id}, saved_paths={len(saved_paths)}, status_data={status_data}")

        db_status = ProcessStatusCRUD.create(db, status_data)
        print(f"Endpoints create_video, job_id={job_id}, saved_paths={len(saved_paths)}, db_status={db_status}")

        # Process in background
        background_tasks.add_task(
            process_video_background,
            job_id,
            saved_paths,
            fps,
            duration_per_image,
            transition_type,
            (resolution_width, resolution_height),
            quality,
            temp_dir,
            db  # Pass the db session
        )

        db_status = ProcessStatusCRUD.update(
            db,
            job_id,
            ProcessStatusUpdate(
                status=ProcessStatuses.processing,
                progress=18,
                message="Video creation started",
                video_url=None,
                updated_at=datetime.utcnow()
            )
        )
        print(f"Endpoints done create_video return db_status={db_status}")
        #return db_status - using the response model
        return ProcessStatusResponse.from_orm(db_status)

    except Exception as e:
        db_status = ProcessStatusCRUD.update(
            db,
            job_id,
            ProcessStatusUpdate(
                status=ProcessStatuses.failed,
                progress=100,
                message=str(e),
                error=str(e),
                completed_at=datetime.utcnow()
            )
        )
        print(f"Endpoints /videos/create status_code=500 db_status={db_status}, \n exception={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_video_background(
    job_id: str,
    image_paths: List[str],
    fps: int,
    duration_per_image: float,
    transition_type: str,
    resolution: tuple,
    quality: str,
    temp_dir: str,
    db: Session
):
    """Background task to process video"""
    print(f"Endpoints process_video_background job_id={job_id}, fps={fps}, image_paths={len(image_paths)}")
    try:
        # Update status
        db_status = ProcessStatusCRUD.update(
            db,
            job_id,
            ProcessStatusUpdate(
                status=ProcessStatuses.processing,
                progress=16,
                message="Processing images...",
                updated_at=datetime.utcnow()
            )
        )
        print(f"Endpoints process_video_background db_status={db_status}")

        # Call the video processor
        from app.core.video_processor import get_video_processor
        db_status = await get_video_processor().create_video_from_images(
            job_id=job_id,
            image_paths=image_paths,
            fps=fps,
            resolution=resolution,
            transition_type=transition_type,
            duration_per_image=duration_per_image,
            quality=quality,
            db=db  # Pass the db session
        )
        print(f"Endpoints process_video_background finished successfully, \n db_status={db_status}")

        return db_status

    except Exception as e:
        db_status = ProcessStatusCRUD.update(
            db,
            job_id,
            ProcessStatusUpdate(
                status=ProcessStatuses.failed,
                progress=100,
                message=str(e),
                error=str(e),
                completed_at=datetime.utcnow()
            )
        )
        print(f"Endpoints process_video_background exception={str(e)}, \n db_status={db_status}")


@router.get("/videos/{job_id}/status", response_model=ProcessStatusResponse)
async def get_video_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get processing status for a job"""
    db_status = ProcessStatusCRUD.get_by_job_id(db, job_id)
    print(f"Endpoints get_video_status job_id={job_id}, db_status={db_status}")
    if not db_status:
        raise HTTPException(status_code=404, detail="Error get_video_status - Job not found")

    #return db_status - using the response model
    return ProcessStatusResponse.from_orm(db_status)

@router.get("/videos/download/{filename}")
async def download_video(filename: str,
    db: Session = Depends(get_db)
):
    """Download video file"""
    from app.core.video_processor import get_video_processor
    video_path = os.path.join(get_video_processor().output_dir, filename)
    print(f"Endpoints download_video filename={filename}, video_path={video_path}")

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Endpoints download_video Video not found")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename
    )