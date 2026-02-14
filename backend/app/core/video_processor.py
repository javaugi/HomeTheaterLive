#VideoProcessor
print(">>> importing VideoProcessor")
import numpy as np
import os
from typing import List, Optional, Tuple, Dict
import asyncio
import tempfile
import shutil
from datetime import datetime
import subprocess
import json
from app.core.config import settings

from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.model.process_status import ProcessStatuses
from app.model.schemas import ProcessStatusUpdate
from app.crud.process_status import ProcessStatusCRUD


import logging
logger = logging.getLogger(__name__)
print(">>> importing VideoProcessor done")


class VideoProcessor:
    def __init__(self, output_dir: str = settings.VIDEO_OUTPUT_DIR):
        print(">>>VideoProcessor  initializing VideoProcessor")
        self.output_dir = output_dir
        # ⚠️ DO NOT run ffmpeg, scan dirs, or heavy work here
        # just cheap setup

        from concurrent.futures import ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def create_video_from_images(
        self,
        job_id: str,
        image_paths: List[str],
        output_filename: Optional[str] = None,
        fps: int = 30,
        resolution: Optional[Tuple[int, int]] = None,
        transition_type: str = "none",
        duration_per_image: float = 2.0,
        quality: str = "high",
        db: Session = None
    ) -> Dict:
        """Create H.264 video from images asynchronously"""
        print(f"VideoProcessor create_video_from_images image_paths={len(image_paths)}")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.executor,
            self._create_video_sync,
            job_id,
            image_paths,
            output_filename,
            fps,
            resolution,
            transition_type,
            duration_per_image,
            quality,
            db
        )


    """ The _create_video_sync method is being called from a thread pool executor, so it doesn't have access to the database session.
    """
    def _create_video_sync(
        self,
        job_id: str,
        image_paths: List[str],
        output_filename: Optional[str] = None,
        fps: int = 30,
        resolution: Optional[Tuple[int, int]] = None,
        transition_type: str = "none",
        duration_per_image: float = 2.0,
        quality: str = "high",
        db: Session = None  # Remove Depends, just accept db session
    ) -> Dict:
        """Synchronous H.264 video creation"""
        print(f"VideoProcessor _create_video_sync image_paths={len(image_paths)}")
        try:
            # Validate inputs
            if not image_paths:
                raise ValueError("No images provided")

            # Sort images
            image_paths.sort()

            # Create output filename
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f"video_{timestamp}.mp4"

            print(f"VideoProcessor _create_video_sync output_filename={output_filename}")
            # Set quality parameters
            quality_settings = self._get_quality_settings(quality)


            # Check if FFmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
                has_ffmpeg = True
            except:
                has_ffmpeg = False
                print(f"VideoProcessor FFmpeg not found, using OpenCV from image_paths={len(image_paths)}")

            print(f"VideoProcessor _create_video_sync has_ffmpeg={has_ffmpeg}, quality_settings={quality_settings}")
            if has_ffmpeg:
                video_path = self._create_video_ffmpeg(
                    job_id=job_id,
                    image_paths=image_paths,
                    output_filename=output_filename,
                    fps=fps,
                    resolution=resolution,
                    transition_type=transition_type,
                    duration_per_image=duration_per_image,
                    quality_settings=quality_settings
                )
            else:
                video_path = self._create_video_opencv(
                    job_id=job_id,
                    image_paths=image_paths,
                    output_filename=output_filename,
                    fps=fps,
                    resolution=resolution,
                    transition_type=transition_type,
                    duration_per_image=duration_per_image,
                    quality_settings=quality_settings
                )

            # Verify the created video
            print(f"VideoProcessor _create_video_sync video created={os.path.exists(video_path)}. video_path={video_path}")
            if not os.path.exists(video_path):
                raise ValueError("Video file was not created")

            # Get video info
            video_size = os.path.getsize(video_path)
            if video_size == 0:
                raise ValueError("VideoProcessor _create_video_sync Video file is empty")
            video_info = self._get_video_info(video_path)
            print(f"VideoProcessor _create_video_sync video_info={video_info}, \n now return success with output_filename={output_filename}")

            db_status = ProcessStatusCRUD.update(
                db,
                job_id,
                ProcessStatusUpdate(
                    status=ProcessStatuses.completed,
                    progress=100,
                    message=f"H.264 video created successfully: {output_filename} ({self._format_bytes(video_size)})",
                    video_path=video_path,
                    video_url=f"/api/v1/video/{output_filename}",
                    filename=output_filename,
                    notes=f"codec=H.264, video_size={video_size}, video_info={video_info}"
                )
            )
            print(f"VideoProcessor _create_video_sync return db_status={db_status}")
            return db_status

        except Exception as e:
            logger.error(f"Error VideoProcessor _create_video_sync creating video: {e}", exc_info=True)
            db_status = ProcessStatusCRUD.update(
                db,
                job_id,
                ProcessStatusUpdate(
                    status=ProcessStatuses.failed,
                    progress=100,
                    message=f"Failed to create video: {str(e)}",
                    error=str(e)
                )
            )
            print(f"VideoProcessor _create_video_sync error db_status={db_status}")
            return db_status


    def _get_quality_settings(self, quality: str) -> Dict:
        """Get quality settings based on quality string"""
        quality_presets = {
            "low": {"preset": "ultrafast", "crf": 28, "bitrate": "1000k"},
            "medium": {"preset": "fast", "crf": 23, "bitrate": "2500k"},
            "high": {"preset": "medium", "crf": 20, "bitrate": "5000k"},
            "ultra": {"preset": "slow", "crf": 18, "bitrate": "8000k"}
        }
        return quality_presets.get(quality, quality_presets["medium"])

    def _create_video_opencv(
        self,
        job_id: str,
        image_paths: List[str],
        output_filename: str,
        fps: int,
        resolution: Optional[Tuple[int, int]],
        transition_type: str,
        duration_per_image: float,
        quality_settings: Dict
    ) -> str:
        """Create video using OpenCV with H.264 codec"""
        # video files go to the HomeTheaterLive/video_output/*.mp4
        video_path = os.path.join(self.output_dir, output_filename)
        print(f"VideoProcessor _create_video_opencv video_path={video_path}")

        # Read first image to get dimensions
        import cv2
        first_image = cv2.imread(image_paths[0])
        if first_image is None:
            raise ValueError(f"VideoProcessor _create_video_opencv Could not read first image: {image_paths[0]}")

        # Set resolution
        if resolution:
            height, width = resolution[1], resolution[0]
        else:
            height, width, _ = first_image.shape
            # Ensure even dimensions (required by H.264)
            width = width - (width % 2)
            height = height - (height % 2)

        size = (width, height)

        # Try different H.264 codec configurations
        codecs = [
            ('H264', cv2.VideoWriter_fourcc(*'H264')),
            ('X264', cv2.VideoWriter_fourcc(*'X264')),
            ('AVC1', cv2.VideoWriter_fourcc(*'avc1')),
            ('MP4V', cv2.VideoWriter_fourcc(*'mp4v')),  # Fallback
        ]

        video_writer = None
        codec_used = None

        for codec_name, fourcc in codecs:
            try:
                video_writer = cv2.VideoWriter(
                    video_path,
                    fourcc,
                    fps,
                    size,
                    True
                )

                if video_writer.isOpened():
                    codec_used = codec_name
                    logger.info(f"Using codec: {codec_name}")
                    break
                else:
                    video_writer.release()
            except:
                continue

        print(f"VideoProcessor _create_video_opencv codec_used={codec_used}, video_writer={video_writer}")
        if not video_writer or not video_writer.isOpened():
            raise ValueError("VideoProcessor _create_video_opencv Could not create video writer with any codec")

        try:
            frames_per_image = int(duration_per_image * fps)

            # Process each image
            for i, image_path in enumerate(image_paths):
                img = cv2.imread(image_path)
                if img is None:
                    logger.warning(f"Could not read image: {image_path}")
                    continue

                # Resize if needed
                if img.shape[:2] != (height, width):
                    img = cv2.resize(img, size, interpolation=cv2.INTER_LANCZOS4)

                # Write frames for this image
                for _ in range(frames_per_image):
                    video_writer.write(img)

                # Add transition if specified and not last image
                if transition_type != "none" and i < len(image_paths) - 1:
                    next_img = cv2.imread(image_paths[i + 1])
                    if next_img is not None:
                        if next_img.shape[:2] != (height, width):
                            next_img = cv2.resize(next_img, size)

                        if transition_type == "fade":
                            self._add_fade_transition(
                                video_writer, img, next_img, fps, duration=0.5
                            )
                        elif transition_type == "slide":
                            self._add_slide_transition(
                                video_writer, img, next_img, fps, duration=0.5
                            )

            video_writer.release()
            logger.info(f"VideoProcessor _create_video_opencv created with OpenCV using {codec_used}: {video_path}")

            # If not using H.264 codec, convert to H.264 using FFmpeg
            if codec_used != "H264" and codec_used != "X264":
                h264_path = video_path.replace('.mp4', '_h264.mp4')
                self._convert_to_h264_ffmpeg(video_path, h264_path, quality_settings)
                os.replace(h264_path, video_path)  # Replace with H.264 version

            return video_path

        finally:
            if video_writer:
                video_writer.release()
            cv2.destroyAllWindows()

    def _create_video_ffmpeg(
        self,
        job_id: str,
        image_paths: List[str],
        output_filename: str,
        fps: int,
        resolution: Optional[Tuple[int, int]],
        transition_type: str,
        duration_per_image: float,
        quality_settings: Dict,
        db: Session = Depends(get_db)
    ) -> str:
        """Create video using FFmpeg directly (most reliable for H.264)"""
        try:

            video_path = os.path.join(self.output_dir, output_filename)
            print(f"VideoProcessor _create_video_ffmpeg video_path={video_path}")
            db_status = ProcessStatusCRUD.update(
                db,
                job_id,
                ProcessStatusUpdate(
                    status=ProcessStatuses.processing,
                    progress=18,
                    video_path=video_path,
                    filename=output_filename,
                    message="_create_video_ffmpeg: Running FFmpeg command",
                    updated_at=datetime.utcnow()
                )
            )

            # Create a temporary directory for processed images
            temp_dir = tempfile.mkdtemp(prefix="video_frames_")


            from PIL import Image
            # Read first image to get dimensions
            first_image = Image.open(image_paths[0])
            # Set resolution
            if resolution:
                width, height = resolution
            else:
                width, height = first_image.size
                # Ensure even dimensions
                width = width - (width % 2)
                height = height - (height % 2)


            # Calculation to a proper playback spped
            #"""
            frames_per_image = max(1, int(fps * duration_per_image))
            global_frame_idx = 0
            import cv2
            for i, img_path in enumerate(image_paths):
                img = cv2.imread(img_path)
                if img is not None:
                    # Resize to even dimensions for H.264 compatibility
                    height, width = img.shape[:2]
                    width &= ~1  # Bitwise trick to ensure even number
                    height &= ~1

                    if img.shape[:2] != (height, width):
                        img = cv2.resize(img, (width, height), interpolation=cv2.INTER_LANCZOS4)

                    # Write the same image multiple times to create "duration"
                    for _ in range(frames_per_image):
                        temp_path = os.path.join(temp_dir, f"frame_{global_frame_idx:06d}.png")
                        cv2.imwrite(temp_path, img)
                        global_frame_idx += 1

                progress = 10 + (i / len(image_paths)) * 50
                print(f"VideoProcessor _create_video_ffmpeg *** looping progress={int(progress)}")
                db_status = ProcessStatusCRUD.update(
                    db,
                    job_id,
                    ProcessStatusUpdate(
                        progress=int(progress),
                        message=f"update_progress value: {int(progress)}",
                        updated_at=datetime.utcnow()
                    )
                )
                print(f"VideoProcessor _create_video_ffmpeg update_progress value: {int(progress)}, db_status={db_status}")


            frame_count = global_frame_idx
            total_duration = frame_count / fps
            print(f"VideoProcessor _create_video_ffmpeg settings fps={fps}, frame_count={frame_count}, total_duration={total_duration}")
            #"""

            # Create FFmpeg command for H.264 encoding
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-framerate', str(fps),
                '-i', os.path.join(temp_dir, 'frame_%06d.png'),
                '-c:v', 'libx264',  # H.264 codec
                '-preset', quality_settings['preset'],
                '-crf', str(quality_settings['crf']),
                '-pix_fmt', 'yuv420p',  # Required for broad compatibility
                '-movflags', '+faststart',  # Enable streaming
                '-vf', f'scale={width}:{height}:flags=lanczos',
            #    '-r', str(fps),  # Output frame rate
                video_path
            ]

            print(f"VideoProcessor _create_video_ffmpeg Running FFmpeg command:\n {' '.join(ffmpeg_cmd)}, \n db_status={db_status}")
            # Execute FFmpeg
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                check=True
            )

            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
            """
            db_status = ProcessStatusCRUD.update(
                db,
                job_id,
                ProcessStatusUpdate(
                    progress=90,
                    message="Finished Running FFmpeg command",
                    completed_at=datetime.utcnow()
                )
            )
            """
            print(f"VideoProcessor _create_video_ffmpeg return for success Video created with FFmpeg: \n video_path={video_path}, \n db_status={db_status}")
            # C:\Users\javau\dev\projects\python\HomeTheaterLive\backend\video_output\video_20260204_170404.mp4
            return video_path

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
            print(f"VideoProcessor _create_video_ffmpeg exception={str(e)}, \n db_status={db_status}")


        finally:
            print(f"DEBUG:backend/app/core/video-processor.py _create_video_ffmpeg finally temp_dir: {temp_dir}")
            # Cleanup temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _convert_to_h264_ffmpeg(self, input_path: str, output_path: str, quality_settings: Dict):
        """Convert any video to H.264 using FFmpeg"""
        print(f"VideoProcessor _convert_to_h264_ffmpeg input_path: {input_path}, output_path={output_path}")
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',
            '-i', input_path,
            '-c:v', 'libx264',
            '-preset', quality_settings['preset'],
            '-crf', str(quality_settings['crf']),
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            '-c:a', 'aac',  # Add audio codec (even if no audio)
            '-b:a', '128k',
            output_path
        ]

        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg conversion failed: {result.stderr}")

    def _add_fade_transition(self, writer, img1, img2, fps, duration=0.5):
        """Add fade transition between two images"""
        transition_frames = int(duration * fps)
        import cv2
        print(f"VideoProcessor _add_fade_transition transition_frames: {transition_frames}")
        for i in range(transition_frames):
            alpha = i / transition_frames
            beta = 1 - alpha
            blended = cv2.addWeighted(img1, beta, img2, alpha, 0)
            writer.write(blended)

    def _add_slide_transition(self, writer, img1, img2, fps, duration=0.5):
        """Add slide transition between two images"""
        transition_frames = int(duration * fps)
        height, width = img1.shape[:2]
        print(f"VideoProcessor _add_slide_transition transition_frames: {transition_frames}")

        for i in range(transition_frames):
            offset = int((i / transition_frames) * width)

            # Create sliding effect
            frame = np.zeros_like(img1)

            # Left part from img1
            if offset > 0:
                frame[:, :width-offset] = img1[:, offset:]

            # Right part from img2
            if offset < width:
                frame[:, width-offset:] = img2[:, :offset]

            writer.write(frame)

    def _get_video_info(self, video_path: str) -> Dict:
        """Get information about the created video"""
        print(f"VideoProcessor _get_video_info video_path: {video_path}")
        try:
            # Use FFprobe to get video info
            ffprobe_cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]

            result = subprocess.run(
                ffprobe_cmd,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                info = json.loads(result.stdout)

                # Extract video stream info
                video_stream = None
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        video_stream = stream
                        break

                if video_stream:
                    return {
                        "duration": float(info.get('format', {}).get('duration', 0)),
                        "resolution": f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}",
                        "codec": video_stream.get('codec_name', 'Unknown'),
                        "bitrate": info.get('format', {}).get('bit_rate', 'Unknown')
                    }

            # Fallback to OpenCV if FFprobe fails
            import cv2
            cap = cv2.VideoCapture(video_path)
            print(f"VideoProcessor _get_video_info video_path: {video_path} \n cap={cap}")
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else 0

                cap.release()

                return {
                    "duration": duration,
                    "resolution": f"{width}x{height}",
                    "fps": fps,
                    "frame_count": frame_count
                }

            return {"duration": 0, "resolution": "Unknown"}

        except Exception as e:
            logger.warning(f"Could not get video info: {e}")
            return {"duration": 0, "resolution": "Unknown"}

    def _format_bytes(self, size: int) -> str:
        """Format bytes to human readable"""
        print(f"VideoProcessor _format_bytes size: {size}")
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

# Global processor instance
#video_processor = VideoProcessor()# -*- coding: utf-8 -*-
_video_processor: VideoProcessor | None = None
def get_video_processor() -> VideoProcessor:
    global _video_processor
    if _video_processor is None:
        _video_processor = VideoProcessor()
    return _video_processor