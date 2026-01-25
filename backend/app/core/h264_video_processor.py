import cv2
import numpy as np
import os
import glob
from typing import List, Optional, Tuple, Dict
from PIL import Image
import asyncio
from concurrent.futures import ThreadPoolExecutor
import tempfile
import shutil
from datetime import datetime
import logging
import subprocess
import json

logger = logging.getLogger(__name__)

class H264VideoProcessor:
    def __init__(self, output_dir: str = "processed_videos"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # H.264 codec settings
        self.h264_preset = "medium"  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
        self.h264_crf = 23  # Constant Rate Factor (0-51, lower is better quality)
        
    async def create_video_from_images(
        self,
        image_paths: List[str],
        output_filename: Optional[str] = None,
        fps: int = 30,
        resolution: Optional[Tuple[int, int]] = None,
        transition_type: str = "none",
        duration_per_image: float = 2.0,
        quality: str = "high"
    ) -> Dict:
        """Create H.264 video from images asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._create_video_sync,
            image_paths,
            output_filename,
            fps,
            resolution,
            transition_type,
            duration_per_image,
            quality
        )
    
    def _create_video_sync(
        self,
        image_paths: List[str],
        output_filename: Optional[str] = None,
        fps: int = 30,
        resolution: Optional[Tuple[int, int]] = None,
        transition_type: str = "none",
        duration_per_image: float = 2.0,
        quality: str = "high"
    ) -> Dict:
        """Synchronous H.264 video creation"""
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
            
            # Set quality parameters
            quality_settings = self._get_quality_settings(quality)
            
            # Method 1: Try using OpenCV with H.264 codec
            video_path = self._create_video_opencv(
                image_paths=image_paths,
                output_filename=output_filename,
                fps=fps,
                resolution=resolution,
                transition_type=transition_type,
                duration_per_image=duration_per_image,
                quality_settings=quality_settings
            )
            
            # Method 2: If OpenCV fails, try using FFmpeg directly
            if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
                logger.warning("OpenCV method failed, trying FFmpeg...")
                video_path = self._create_video_ffmpeg(
                    image_paths=image_paths,
                    output_filename=output_filename,
                    fps=fps,
                    resolution=resolution,
                    quality_settings=quality_settings
                )
            
            # Verify the created video
            if not os.path.exists(video_path):
                raise ValueError("Video file was not created")
            
            video_size = os.path.getsize(video_path)
            if video_size == 0:
                raise ValueError("Video file is empty")
            
            # Get video info
            video_info = self._get_video_info(video_path)
            
            return {
                "success": True,
                "video_path": video_path,
                "filename": output_filename,
                "size": video_size,
                "duration": video_info.get("duration", 0),
                "resolution": video_info.get("resolution", "Unknown"),
                "codec": "H.264",
                "message": f"H.264 video created successfully: {output_filename} ({self._format_bytes(video_size)})"
            }
            
        except Exception as e:
            logger.error(f"Error creating video: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create video: {str(e)}"
            }
    
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
        image_paths: List[str],
        output_filename: str,
        fps: int,
        resolution: Optional[Tuple[int, int]],
        transition_type: str,
        duration_per_image: float,
        quality_settings: Dict
    ) -> str:
        """Create video using OpenCV with H.264 codec"""
        video_path = os.path.join(self.output_dir, output_filename)
        
        # Read first image to get dimensions
        first_image = cv2.imread(image_paths[0])
        if first_image is None:
            raise ValueError(f"Could not read first image: {image_paths[0]}")
        
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
        
        if not video_writer or not video_writer.isOpened():
            raise ValueError("Could not create video writer with any codec")
        
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
            logger.info(f"Video created with OpenCV using {codec_used}: {video_path}")
            
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
        image_paths: List[str],
        output_filename: str,
        fps: int,
        resolution: Optional[Tuple[int, int]],
        quality_settings: Dict
    ) -> str:
        """Create video using FFmpeg directly (most reliable for H.264)"""
        video_path = os.path.join(self.output_dir, output_filename)
        
        # Create a temporary directory for processed images
        temp_dir = tempfile.mkdtemp(prefix="video_frames_")
        
        try:
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
            
            # Resize and save all images to temp directory
            for i, img_path in enumerate(image_paths):
                img = Image.open(img_path)
                
                # Resize if needed
                if img.size != (width, height):
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                # Save as PNG for best quality
                temp_path = os.path.join(temp_dir, f"frame_{i:06d}.png")
                img.save(temp_path, "PNG")
            
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
                '-r', str(fps),  # Output frame rate
                video_path
            ]
            
            logger.info(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
            
            # Execute FFmpeg
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
            
            logger.info(f"Video created with FFmpeg: {video_path}")
            return video_path
            
        finally:
            # Cleanup temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _convert_to_h264_ffmpeg(self, input_path: str, output_path: str, quality_settings: Dict):
        """Convert any video to H.264 using FFmpeg"""
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
        for i in range(transition_frames):
            alpha = i / transition_frames
            beta = 1 - alpha
            blended = cv2.addWeighted(img1, beta, img2, alpha, 0)
            writer.write(blended)
    
    def _add_slide_transition(self, writer, img1, img2, fps, duration=0.5):
        """Add slide transition between two images"""
        transition_frames = int(duration * fps)
        height, width = img1.shape[:2]
        
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
            cap = cv2.VideoCapture(video_path)
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
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

# Global processor instance
video_processor = H264VideoProcessor()# -*- coding: utf-8 -*-

