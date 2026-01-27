#backend/app/api/endpoints.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List
import os
import uuid
import shutil
from datetime import datetime
import json

from app.core.config import settings
from app.core.video_processor import video_processor

from app.model_s.schemas import (
    VideoResponse, ProcessingStatus,
    DirectoryProcessRequest, VideoSettings
)
from app.utils.file_utils import (
    save_upload_file, validate_image_files,
    create_temp_directory, cleanup_temp_directory
)

router = APIRouter(tags=["endpoints"])


# In-memory storage for processing status (use Redis in production)
processing_status = {}


@router.post("/process/directory", response_model=VideoResponse)
async def process_directory(
        request: DirectoryProcessRequest,
        background_tasks: BackgroundTasks
):
    """Process images from a directory"""
    try:
        # Validate directory exists
        if not os.path.exists(request.directory_path):
            raise HTTPException(status_code=400, detail="Directory does not exist")

        # Create a unique job ID
        job_id = str(uuid.uuid4())

        # Store initial status
        processing_status[job_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Starting video creation...",
            "created_at": datetime.now().isoformat()
        }

        # Process in background
        background_tasks.add_task(
            process_video_task,
            job_id,
            request.directory_path,
            request.video_settings
        )

        return VideoResponse(
            job_id=job_id,
            status="processing",
            message="Video creation started in background",
            video_url=None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/upload", response_model=VideoResponse)
async def process_uploaded_images(
        files: List[UploadFile] = File(...),
        #settings: str = Form(default='{}'),
        background_tasks: BackgroundTasks = None
):
    """Process uploaded images"""
    try:
        # Parse settings
        try:
            video_settings = VideoSettings(**json.loads(settings))
        except:
            video_settings = VideoSettings()

        # Validate files
        validate_image_files(files)

        # Create temp directory for uploaded files
        temp_dir = create_temp_directory()

        # Save uploaded files
        saved_paths = []
        for i, file in enumerate(files):
            file_path = await save_upload_file(file, temp_dir)
            saved_paths.append(file_path)

        # Create job ID
        job_id = str(uuid.uuid4())

        # Store initial status
        processing_status[job_id] = {
            "status": "processing",
            "progress": 0,
            "message": f"Processing {len(saved_paths)} images...",
            "created_at": datetime.now().isoformat()
        }

        # Process in background
        background_tasks.add_task(
            process_upload_task,
            job_id,
            saved_paths,
            video_settings,
            temp_dir
        )

        return VideoResponse(
            job_id=job_id,
            status="processing",
            message="Video creation started",
            video_url=None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=ProcessingStatus)
async def get_processing_status(job_id: str):
    """Get processing status for a job"""
    if job_id not in processing_status:
        raise HTTPException(status_code=404, detail="Job not found")

    return ProcessingStatus(**processing_status[job_id])


@router.get("/video/{filename}")
async def get_video_file(filename: str):
    """Serve video file"""
    video_path = os.path.join(video_processor.output_dir, filename)

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename
    )


@router.get("/videos")
async def list_videos():
    """List all available videos"""
    videos = []

    for filename in os.listdir(video_processor.output_dir):
        if filename.endswith('.mp4'):
            filepath = os.path.join(video_processor.output_dir, filename)
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
    video_path = os.path.join(video_processor.output_dir, filename)

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")

    os.remove(video_path)
    return {"message": "Video deleted successfully"}


# Background task functions
async def process_video_task(job_id: str, directory_path: str, settings: VideoSettings):
    """Background task for processing directory"""
    try:
        # Update status
        processing_status[job_id]["progress"] = 10
        processing_status[job_id]["message"] = "Scanning directory for images..."

        # Create video
        output_filename = f"{job_id}.mp4"

        video_path = await video_processor.process_images_to_video(
            image_paths=[],  # Will be read from directory
            output_filename=output_filename,
            fps=settings.fps,
            resolution=settings.resolution,
            transition_type=settings.transition_type,
            duration_per_image=settings.duration_per_image
        )
        print(f"backend/app/api/endpoints.py process_video_task 1 video_path={video_path}")

        # Use the directory method
        video_path = video_processor.create_video_from_directory(
            directory=directory_path,
            fps=settings.fps,
            resolution=settings.resolution,
            output_filename=output_filename,
            transition_type=settings.transition_type,
            duration_per_image=settings.duration_per_image
        )        
        print(f"backend/app/api/endpoints.py process_video_task 2 video_path={video_path}")

        # Update status
        processing_status[job_id]["status"] = "completed"
        processing_status[job_id]["progress"] = 100
        processing_status[job_id]["message"] = "Video created successfully"
        processing_status[job_id]["video_url"] = f"/api/v1/video/{output_filename}"
        processing_status[job_id]["completed_at"] = datetime.now().isoformat()

    except Exception as e:
        processing_status[job_id]["status"] = "failed"
        processing_status[job_id]["message"] = str(e)
        processing_status[job_id]["error"] = str(e)


async def process_upload_task(job_id: str, image_paths: List[str], settings: VideoSettings, temp_dir: str):
    """Background task for processing uploaded files"""
    try:
        processing_status[job_id]["progress"] = 30
        processing_status[job_id]["message"] = "Processing images..."

        output_filename = f"{job_id}.mp4"

        video_path = await video_processor.process_images_to_video(
            image_paths=image_paths,
            output_filename=output_filename,
            fps=settings.fps,
            resolution=settings.resolution,
            transition_type=settings.transition_type,
            duration_per_image=settings.duration_per_image
        )
        print(f"backend/app/api/endpoints.py process_upload_task video_path={video_path}")

        processing_status[job_id]["status"] = "completed"
        processing_status[job_id]["progress"] = 100
        processing_status[job_id]["message"] = "Video created successfully"
        processing_status[job_id]["video_url"] = f"/api/v1/video/{output_filename}"
        processing_status[job_id]["completed_at"] = datetime.now().isoformat()

        # Cleanup temp directory
        cleanup_temp_directory(temp_dir)

    except Exception as e:
        processing_status[job_id]["status"] = "failed"
        processing_status[job_id]["message"] = str(e)
        processing_status[job_id]["error"] = str(e)
        # Cleanup on error too
        cleanup_temp_directory(temp_dir)
        
@router.post("/videos/create", response_model=VideoResponse)
async def create_video(
    files: List[UploadFile] = File(...),
    fps: int = Form(30),
    duration_per_image: float = Form(2.0),
    transition_type: str = Form("none"),
    resolution_width: int = Form(1920),
    resolution_height: int = Form(1080),
    quality: str = Form("high"),
    background_tasks: BackgroundTasks = None
):
    """API endpoint to create video from uploaded images"""
    print(f"backend/app/api/endpoints.py /videos/create fps={fps}, files={len(files)}")      
    try:
        # Create job ID
        job_id = str(uuid.uuid4())
        
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
        
        # Store job info
        processing_status[job_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Uploading images...",
            "created_at": datetime.now().isoformat()
        }
        
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
            temp_dir
        )
        
        return VideoResponse(
            job_id=job_id,
            status="processing",
            message="Video creation started",
            video_url=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_video_background(
    job_id: str,
    image_paths: List[str],
    fps: int,
    duration_per_image: float,
    transition_type: str,
    resolution: tuple,
    quality: str,
    temp_dir: str
):
    """Background task to process video"""
    print(f"backend/app/api/endpoints.py process_video_background job_id={job_id}, fps={fps}, image_paths={len(image_paths)}")      
    try:
        # Update status
        processing_status[job_id]["progress"] = 10
        processing_status[job_id]["message"] = "Processing images..."
        
        # Call the video processor
        result = await video_processor.create_video_from_images(
            image_paths=image_paths,
            fps=fps,
            resolution=resolution,
            transition_type=transition_type,
            duration_per_image=duration_per_image,
            quality=quality
        )
        print(f"backend/app/api/endpoints.py process_video_background result={result}")      
        
        if result["success"]:
            # Update status
            processing_status[job_id]["status"] = "completed"
            processing_status[job_id]["progress"] = 100
            processing_status[job_id]["message"] = result["message"]
            processing_status[job_id]["video_url"] = f"/api/v1/videos/{os.path.basename(result['video_path'])}"
            processing_status[job_id]["video_path"] = result["video_path"]
            processing_status[job_id]["completed_at"] = datetime.now().isoformat()
        else:
            processing_status[job_id]["status"] = "failed"
            processing_status[job_id]["message"] = result.get("error", "Unknown error")
            
    except Exception as e:
        processing_status[job_id]["status"] = "failed"
        processing_status[job_id]["message"] = str(e)
    finally:
        # Cleanup temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@router.get("/videos/{job_id}/status", response_model=ProcessingStatus)
async def get_video_status(job_id: str):
    """Get status of video processing job"""
    print(f"backend/app/api/endpoints.py get_video_status job_id={job_id}, processing_status={processing_status}")      
    if job_id not in processing_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return ProcessingStatus(**processing_status[job_id])

@router.get("/videos/download/{filename}")
async def download_video(filename: str):
    """Download video file"""
    video_path = os.path.join(video_processor.output_dir, filename)
    print(f"backend/app/api/endpoints.py download_video filename={filename}, video_path={video_path}")      
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename
    )        