import cv2
import numpy as np
import os
import glob
from typing import List, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import shutil
from datetime import datetime
#from PIL import Image
#import tempfile
import logging

logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self, output_dir: str = "processed_videos"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def process_images_to_video(
            self,
            image_paths: List[str],
            output_filename: Optional[str] = None,
            fps: int = 30,
            resolution: Optional[Tuple[int, int]] = None,
            transition_type: str = "none",
            duration_per_image: float = 2.0
    ) -> str:
        """Process images to video asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._process_images_sync,
            image_paths,
            output_filename,
            fps,
            resolution,
            transition_type,
            duration_per_image
        )

    def _process_images_sync(
            self,
            image_paths: List[str],
            output_filename: Optional[str] = None,
            fps: int = 30,
            resolution: Optional[Tuple[int, int]] = None,
            transition_type: str = "none",
            duration_per_image: float = 2.0
    ) -> str:
        """Synchronous image processing to video"""
        if not image_paths:
            raise ValueError("No images provided")

        # Sort images naturally
        image_paths.sort()

        # Read first image to get dimensions
        first_image = cv2.imread(image_paths[0])
        if first_image is None:
            raise ValueError(f"Could not read image: {image_paths[0]}")

        # Set resolution
        if resolution:
            height, width = resolution[1], resolution[0]
        else:
            height, width, _ = first_image.shape
            # Ensure even dimensions (required by some codecs)
            width = width - (width % 2)
            height = height - (height % 2)

        size = (width, height)

        # Create output filename
        if not output_filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"video_{timestamp}.mp4"

        output_path = os.path.join(self.output_dir, output_filename)

        # Create video writer with better codec for mobile compatibility
        fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
        video_writer = cv2.VideoWriter(output_path, fourcc, fps, size)

        frames_per_image = int(duration_per_image * fps)

        try:
            for i, image_path in enumerate(image_paths):
                img = cv2.imread(image_path)
                if img is None:
                    logger.warning(f"Could not read image: {image_path}")
                    continue

                # Resize image if needed
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

        finally:
            video_writer.release()
            cv2.destroyAllWindows()

        # Optimize video for mobile playback
        self._optimize_video_for_mobile(output_path)

        logger.info(f"Video created successfully: {output_path}")
        return output_path

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
                frame[:, :width - offset] = img1[:, offset:]

            # Right part from img2
            if offset < width:
                frame[:, width - offset:] = img2[:, :offset]

            writer.write(frame)

    def _optimize_video_for_mobile(self, video_path: str):
        """Optimize video for mobile playback (optional, requires ffmpeg)"""
        try:
            import subprocess
            temp_path = video_path + ".temp.mp4"

            # Use ffmpeg to optimize video
            cmd = [
                'ffmpeg', '-i', video_path,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                '-y', temp_path
            ]

            subprocess.run(cmd, check=True, capture_output=True)

            # Replace original with optimized version
            shutil.move(temp_path, video_path)

        except Exception as e:
            logger.warning(f"Could not optimize video: {e}")
            # Video is still usable without optimization

    def create_video_from_directory(
            self,
            directory: str,
            pattern: str = "**/*.jpg",
            **kwargs
    ) -> str:
        """Create video from all images in a directory"""
        # Find all image files
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.tiff']
        image_paths = []

        for ext in image_extensions:
            pattern = os.path.join(directory, ext)
            image_paths.extend(glob.glob(pattern, recursive=True))
            pattern = os.path.join(directory, ext.upper())
            image_paths.extend(glob.glob(pattern, recursive=True))

        if not image_paths:
            raise ValueError(f"No images found in directory: {directory}")

        return self._process_images_sync(image_paths, **kwargs)

    def cleanup_old_videos(self, days_old: int = 7):
        """Clean up videos older than specified days"""
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)

        for filename in os.listdir(self.output_dir):
            filepath = os.path.join(self.output_dir, filename)
            if os.path.getmtime(filepath) < cutoff_time:
                os.remove(filepath)
                logger.info(f"Removed old video: {filename}")


# Global processor instance
video_processor = VideoProcessor()