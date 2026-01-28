import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import asyncio
from pathlib import Path
from ..utils.icon_loader import load_icon
import os
import sys
import logging
from datetime import datetime
import time
import cv2
import numpy as np
import tempfile
import subprocess
import json
import shutil
import aiohttp

BASE_URL = "http://127.0.0.1:8000/api/v1"

logger = logging.getLogger(__name__)
# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app_debug.log'
)

USE_BACKEND_API_CALL: bool = True
#USE_BACKEND_API_CALL: bool = False

class VideoView:
    """Main video processing view"""

    def __init__(self, app, navigate_back_callback=None):
        self.app = app
        self.app.api_base_url = BASE_URL
        self.navigate_back_callback = navigate_back_callback
        #from ..api import APIClient
        #self.api_client = APIClient(app=self.app)
        self.api_client = None  # Will be initialized when needed        

        # Current state
        self.selected_images = []
        self.current_video_path = None  # Track the created video path
        self.current_job_id = None
        self.is_processing = False

        # Initialize UI elements to None
        self.init_ui_elements()
        try:
            self.container = self.create_ui()
            print("DEBUG: VideoView UI built successfully")
        except Exception as e:
            print(f"DEBUG ERROR: Failed to build UI: {e}")
            raise

    async def get_api_client(self):
        """Get or create API client"""
        if self.api_client is None:
            from ..api import APIClient
            self.api_client = APIClient(self.app, self.app.api_base_url)
        return self.api_client
    

    def init_ui_elements(self):
        """Initialize all UI element references"""
        # Core UI elements
        self.status_label = None
        self.file_list = None
        self.progress_bar = None
        self.progress_label = None
        self.progress_container = None
        self.download_section = None

        # Buttons
        self.pick_images_btn = None
        self.pick_directory_btn = None
        self.clear_btn = None
        self.create_video_btn = None
        self.download_btn = None

        # Inputs
        self.fps_input = None
        self.duration_input = None
        self.transition_select = None
        self.quality_select = None

    def create_ui(self):
        """Create the video processing UI"""
        # Main container
        self.container = toga.Box(style=Pack(direction=COLUMN, margin=0, flex=1))

        # Header with back button
        self.create_header()

        # Content area
        self.create_content()

        # Status area
        self.create_status_area()

        return self.container;

    def create_header(self):
        """Create the header with back button and title"""
        header_box = toga.Box(style=Pack(
            direction=ROW,
            margin=15,
            text_align="center",
            background_color="#f0f0f0"
        ))

        # Back button (if we have a navigate back callback)
        if self.navigate_back_callback:
            back_btn = toga.Button(
                "← Back",
                on_press=self.go_back,
                style=Pack(margin_right=20, font_weight="bold")
            )
            header_box.add(back_btn)

        # App icon and title
        icon = load_icon("video", size=40)

        title_label = toga.Label(
            "Create Video from Images",
            style=Pack(font_size=22, font_weight="bold", flex=1)
        )

        header_box.add(icon)
        header_box.add(title_label)

        self.container.add(header_box)
        self.container.add(toga.Divider(style=Pack(margin=0)))

        return header_box

    def create_content(self):
        """Create the main content area"""
        # Scroll container for better mobile experience
        scroll_container = toga.ScrollContainer(style=Pack(flex=1))
        content_box = toga.Box(style=Pack(direction=COLUMN, margin=20, flex=1))

        # File selection section
        self.create_file_selection(content_box)

        # Settings section
        self.create_settings_section(content_box)

        # Action buttons
        self.create_action_buttons(content_box)

        scroll_container.content = content_box
        self.container.add(scroll_container)

        return scroll_container

    def create_file_selection(self, parent):
        """Create file selection section"""
        section_box = toga.Box(style=Pack(direction=COLUMN, margin=15))

        # Section title
        title_box = toga.Box(style=Pack(direction=ROW, margin_bottom=10))
        folder_icon = load_icon("folder", size=24)
        title_label = toga.Label(
            "Select Images",
            style=Pack(font_size=18, font_weight="bold", margin_left=10)
        )
        title_box.add(folder_icon)
        title_box.add(title_label)
        section_box.add(title_box)

        # Button row
        button_row = toga.Box(style=Pack(direction=ROW, margin=10))

        # Pick Images button
        self.pick_images_btn = toga.Button(
            "📷 Pick Images",
            on_press=self.pick_images,
            style=Pack(flex=1, margin=12, background_color="#4CAF50")
        )

        # Pick Directory button
        self.pick_directory_btn = toga.Button(
            "📂 Pick Directory",
            on_press=self.pick_directory,
            style=Pack(flex=1, margin=12, margin_left=10, background_color="#2196F3")
        )

        button_row.add(self.pick_images_btn)
        button_row.add(self.pick_directory_btn)
        section_box.add(button_row)

        # Clear button
        clear_box = toga.Box(style=Pack(direction=ROW, margin_top=10, text_align="right"))
        self.clear_btn = toga.Button(
            "🗑️ Clear Selection",
            on_press=self.clear_selection,
            style=Pack(margin=8, background_color="#f44336")
        )
        clear_box.add(self.clear_btn)
        section_box.add(clear_box)

        # File list display
        self.file_list = toga.MultilineTextInput(
            readonly=True,
            placeholder="No images selected\n\nClick 'Pick Images' or 'Pick Directory' to select images",
            style=Pack(
                height=120,
                margin=10,
                margin_top=10,
                background_color="#fafafa",
                #border_color="#ddd",
                #border_width=1
            )
        )
        section_box.add(self.file_list)

        parent.add(section_box)
        parent.add(toga.Divider(style=Pack(margin=10)))

        return section_box

    def create_settings_section(self, parent):
        """Create video settings section"""
        section_box = toga.Box(style=Pack(direction=COLUMN, margin=15))

        # Section title
        title_box = toga.Box(style=Pack(direction=ROW, margin_bottom=10))
        settings_icon = load_icon("settings", size=24)
        title_label = toga.Label(
            "Video Settings",
            style=Pack(font_size=18, font_weight="bold", margin_left=10)
        )
        title_box.add(settings_icon)
        title_box.add(title_label)
        section_box.add(title_box)

        # FPS Setting
        fps_box = toga.Box(style=Pack(direction=ROW, margin=8, text_align="center"))
        fps_label = toga.Label(
            "Frame Rate (FPS):",
            style=Pack(width=150, margin_right=10)
        )
        self.fps_input = toga.NumberInput(
            min=1,
            max=60,
            value=24,
            style=Pack(flex=1, margin=8)
        )
        fps_box.add(fps_label)
        fps_box.add(self.fps_input)
        section_box.add(fps_box)

        # Duration per image
        duration_box = toga.Box(style=Pack(direction=ROW, margin=8, text_align="center"))
        duration_label = toga.Label(
            "Seconds per image:",
            style=Pack(width=150, margin_right=10)
        )
        self.duration_input = toga.NumberInput(
            min=0.5,
            max=10,
            value=2.0,
            step=0.5,
            style=Pack(flex=1, margin=8)
        )
        duration_box.add(duration_label)
        duration_box.add(self.duration_input)
        section_box.add(duration_box)

        # Transition type
        transition_box = toga.Box(style=Pack(direction=ROW, margin=8, text_align="center"))
        transition_label = toga.Label(
            "Transition effect:",
            style=Pack(width=150, margin_right=10)
        )
        self.transition_select = toga.Selection(
            items=["None", "Fade", "Slide", "Zoom", "Crossfade"],
            style=Pack(flex=1, margin=8)
        )
        transition_box.add(transition_label)
        transition_box.add(self.transition_select)
        section_box.add(transition_box)

        # Video quality (simulated)
        quality_box = toga.Box(style=Pack(direction=ROW, margin=8, text_align="center"))
        quality_label = toga.Label(
            "Output Quality:",
            style=Pack(width=150, margin_right=10)
        )
        self.quality_select = toga.Selection(
            items=["Low (480p)", "Medium (720p)", "High (1080p)", "Ultra (4K)"],
            style=Pack(flex=1, margin=8)
        )
        self.quality_select.value = "High (1080p)"
        quality_box.add(quality_label)
        quality_box.add(self.quality_select)
        section_box.add(quality_box)

        parent.add(section_box)
        parent.add(toga.Divider(style=Pack(margin=10)))

        return section_box

    def create_action_buttons(self, parent):
        """Create action buttons"""
        section_box = toga.Box(style=Pack(direction=COLUMN, margin=15))

        # Section title
        title_label = toga.Label(
            "Create Video",
            style=Pack(font_size=18, font_weight="bold", margin_bottom=15)
        )
        section_box.add(title_label)

        # Primary action button
        button_box = toga.Box(style=Pack(direction=ROW, margin=10, text_align="center"))

        self.create_video_btn = toga.Button(
            "🎬 CREATE VIDEO NOW",
            on_press=self.create_video,
            style=Pack(
                flex=1,
                margin=15,
                font_size=16,
                font_weight="bold",
                background_color="#FF5722",
                color="white"
            )
        )

        button_box.add(self.create_video_btn)
        section_box.add(button_box)

        # Download section (initially hidden)
        self.download_section = toga.Box(
            style=Pack(direction=COLUMN, margin=15, margin_top=20, display='none')
        )

        download_title = toga.Label(
            "Your Video is Ready!",
            style=Pack(font_size=16, font_weight="bold", margin_bottom=10, text_align="center")
        )
        self.download_section.add(download_title)

        download_btn_box = toga.Box(style=Pack(direction=ROW, margin=10, text_align="center"))
        self.download_btn = toga.Button(
            "📥 DOWNLOAD VIDEO",
            on_press=self.download_video,
            style=Pack(
                flex=1,
                margin=12,
                background_color="#4CAF50",
                color="white"
            )
        )
        download_btn_box.add(self.download_btn)
        self.download_section.add(download_btn_box)

        section_box.add(self.download_section)
        parent.add(section_box)

        return section_box

    def create_status_area(self):
        """Create status and progress area"""
        status_box = toga.Box(style=Pack(
            direction=COLUMN,
            margin=20,
            background_color="#f5f5f5"
        ))

        # Status label
        self.status_label = toga.Label(
            "Ready to create amazing videos from your images",
            style=Pack(margin=10, text_align=CENTER, font_size=14, color="#666")
        )
        status_box.add(self.status_label)

        # Progress bar container (initially hidden)
        self.progress_container = toga.Box(
            style=Pack(direction=COLUMN, margin=10, display='none')
        )

        # Progress bar
        self.progress_bar = toga.ProgressBar(
            max=100,
            value=0,
            style=Pack(margin=5, height=20)
        )
        self.progress_container.add(self.progress_bar)

        # Progress percentage label
        self.progress_label = toga.Label(
            "0%",
            style=Pack(margin=5, text_align="center", font_size=12)
        )
        self.progress_container.add(self.progress_label)

        status_box.add(self.progress_container)
        self.container.add(status_box)

        return status_box

    def go_back(self, widget):
        """Navigate back to home view"""
        if self.navigate_back_callback:
            self.navigate_back_callback()

    async def pick_images(self, widget):
        """Pick multiple image files"""
        try:
            # For iOS/Android, you'd use platform-specific file pickers
            # For now, simulate file picking
            self.update_status("Opening file picker...")

            # Simulate selected files
            self.selected_images = [
                "/Users/me/Pictures/vacation1.jpg",
                "/Users/me/Pictures/vacation2.jpg",
                "/Users/me/Pictures/vacation3.jpg",
                "/Users/me/Pictures/vacation4.jpg",
                "/Users/me/Pictures/vacation5.jpg"
            ]

            self.update_file_list()
            self.update_status(f"Selected {len(self.selected_images)} images")

        except Exception as e:
            self.show_error(f"Error picking images: {str(e)}")


    async def pick_directory(self, widget):
        """Pick a directory with platform-specific implementation"""
        import sys
        # Log the attempt
        logging.info("Starting directory picker...")
        print("DEBUG: Starting directory picker")
        try:
            selected_path = None

            # Platform-specific directory picking
            if sys.platform == 'darwin':  # macOS/iOS
                selected_path = await self._pick_directory_macos()
            elif 'android' in sys.platform:
                selected_path = await self._pick_directory_android()
            elif sys.platform == 'win32':
                selected_path = await self._pick_directory_windows()
            else:
                selected_path = await self._pick_directory_fallback()

            if selected_path:
                #logging.info(f"Directory selected: {selected_path}")
                print(f"DEBUG: Directory selected: {selected_path}")
                # Process the directory
                await self._debug_directory_info(selected_path)
                print(f"DEBUG: calling _process_selected_directory Directory selected: {selected_path}")
                await self._process_selected_directory(selected_path)
                #await self._process_directory_with_logging(selected_path)
            else:
                logging.warning("No directory selected (user cancelled)")
                print("DEBUG: No directory selected or dialog cancelled")
                self.update_status("No directory selected (user cancelled)")

        except Exception as e:
            print(f"Directory selection error: {e}")
            self.show_error(f"Directory selection error: {str(e)}")

    async def _pick_directory_macos(self):
        """Directory picker for macOS/iOS"""
        # For iOS/macOS, use the native file dialog
        print("MacOS _pick_directory_macos")
        selected_path = await self.app.main_window.select_folder_dialog(
            title="Select Folder Containing Images",
            multiselect=False
        )
        print(f"macOS/iOS selected: {selected_path}")

        return selected_path

    async def _pick_directory_android(self):
        """Directory picker for Android"""
        # For Android, you might need to use an intent
        # This is a simplified version
        print("Android _pick_directory_android")
        try:
            # Using Toga's dialog
            selected_path = await self.app.main_window.select_folder_dialog(
                title="Select Folder",
                multiselect=False
            )
            print(f"Android selected: {selected_path}")

            return selected_path
        except:
            # Fallback or custom implementation
            print("Using fallback directory picker for Android")
            return None

    async def _pick_directory_windows(self):
        """Directory picker for Windows"""
        print("Windows _pick_directory_windows")
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()  # Hide the main window

            folder_selected = filedialog.askdirectory(
                title="Select a directory containing images"
            )

            root.destroy()
            print(f"Windows folder_selected selected: {folder_selected}")

            return folder_selected
        except:
            return None

    async def _pick_directory_fallback(self):
        """Fallback to a text input dialog"""
        print("Fallback _pick_directory_fallback")
        try:
            # Ask user to enter path manually
            path = await self.show_info_dialog(
                title="Enter Directory Path",
                message="Please enter the full path to the directory:",
                #initial_value="C:\\Users\\javau\\devdownloads"
            )

            print(f"Windows _pick_directory_fallback path selected: {path}")
            if path:
                # Validate the path
                path_obj = Path(path)
                if path_obj.exists() and path_obj.is_dir():
                    print(f"Windows _pick_directory_fallback return path selected: {str(path_obj)}")
                    return str(path_obj)
                else:
                    self.show_error(f"_pick_directory_fallback Invalid directory: {path}")

        except Exception as e:
            print(f"_pick_directory_fallback Fallback picker error: {e}")

        return None

    async def _debug_directory_info(self, directory_path):
        """Print detailed information about the selected directory"""
        from pathlib import Path

        directory = Path(directory_path)

        print("\n=== DIRECTORY DEBUG INFO ===")
        print(f"Path: {directory}, Absolute: {directory.absolute()}")
        print(f"Exists: {directory.exists()}, Is directory: {directory.is_dir()}")

        if directory.exists() and directory.is_dir():
            print("\nContents:")
            try:
                items = list(directory.iterdir())
                for i, item in enumerate(items[:20]):  # Limit to first 20 items
                    file_type = "DIR" if item.is_dir() else "FILE"
                    size = item.stat().st_size if item.is_file() else 0
                    print(f"  [{i + 1}] {file_type}: {item.name} ({size} bytes)")

                if len(items) > 20:
                    print(f"  ... and {len(items) - 20} more items")

            except PermissionError:
                print("  Permission denied to list contents")
            except Exception as e:
                print(f"  Error listing contents: {e}")

        print("===========================\n")

    async def _process_directory_with_logging(self, directory_path):
        """Process directory with logging"""
        from pathlib import Path
        directory = Path(directory_path)
        # Find image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        image_files = []

        print("Searching for image files...")
        logging.info(f"Searching {directory} for image files")
        try:
            for file in directory.iterdir():
                if file.is_file():
                    suffix = file.suffix.lower()
                    if suffix in image_extensions:
                        image_files.append(str(file))
                        print(f"  ✓ {file.name}")
                        logging.debug(f"Found image: {file.name}")

            print(f"\nTotal images found: {len(image_files)}")
            logging.info(f"Found {len(image_files)} images in {directory}")

            if image_files:
                self.selected_images = image_files
                self.update_file_list()
                self.update_status(f"Selected {len(image_files)} images from {directory.name}")

                # Log to file
                with open('selected_images.log', 'w') as f:
                    f.write(f"Directory: {directory}\n")
                    f.write(f"Selection time: {datetime.now()}\n")
                    f.write(f"Total images: {len(image_files)}\n\n")
                    for img in image_files:
                        f.write(f"{img}\n")
            else:
                self.show_error(f"No images found in {directory.name}")
                logging.warning(f"No images found in {directory}")

        except Exception as e:
            error_msg = f"Error processing directory: {str(e)}"
            logging.error(error_msg, exc_info=True)
            print(f"ERROR: {error_msg}")
            self.show_error(error_msg)

    async def _process_selected_directory(self, directory_path):
        """Process the selected directory"""
        print(f"Processing directory: {directory_path}")
        # Convert to Path object for easier manipulation
        directory = Path(directory_path)
        # Print directory info
        print(f"Directory exists: {directory.exists()}, Directory is dir: {directory.is_dir()}, Directory absolute path: {directory.absolute()}")

        # List all contents
        for item in directory.iterdir():
            print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")

        # Find image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        image_files = []

        for file in directory.iterdir():
            if file.is_file() and file.suffix.lower() in image_extensions:
                image_files.append(str(file))
                print(f"Found image: {file.name}")

        print(f"Total images found: {len(image_files)}")

        if image_files:
            self.selected_images = image_files
            self.update_file_list()
            self.update_status(f"Found {len(image_files)} images in {directory.name}")
        else:
            self.show_error(f"No images found in {directory.name}")

    def clear_selection(self, widget):
        """Clear selected images"""
        self.selected_images = []
        self.update_file_list()
        self.update_status("Selection cleared")
        self.hide_download_section()

    async def create_video_bk2(self, widget):
        """Create video from selected images"""
        print(f"Creating video from selected Selected {len(self.selected_images)} images")
        if not self.selected_images:
            self.show_error("Please select images first")
            return

        print(f"Creating video from selected images self.is_processing:{self.is_processing}")
        if self.is_processing:
            self.show_error("Already processing a video")
            return

        try:
            self.is_processing = True
            self.update_status("Starting video creation...")            
            print("Creating video show_progress_container ...")
            self.show_progress_container()            
            print("Creating video update_progress ...")
            self.update_progress(0)
            
            print("Creating video hide_download_section ...")
            self.hide_download_section()

            # Disable buttons during processing
            self.pick_images_btn.enabled = False
            self.pick_directory_btn.enabled = False
            self.create_video_btn.enabled = False
            self.clear_btn.enabled = False

            # Get settings from UI
            settings = {
                "fps": int(self.fps_input.value),
                "duration_per_image": float(self.duration_input.value),
                "transition_type": self.transition_select.value.lower(),
                "quality": self.quality_select.value
            }

            # Simulate API call and processing
            print(f"Creating video simulate_video_processing settings={settings}")
            await self.simulate_video_processing(settings)

            # Enable buttons after processing
            self.pick_images_btn.enabled = True
            self.pick_directory_btn.enabled = True
            self.create_video_btn.enabled = True
            self.clear_btn.enabled = True

        except Exception as e:
            print(f"ERROR: Creating video {str(e)}")
            self.show_error(f"Error creating video: {str(e)}")
            self.is_processing = False
            self.pick_images_btn.enabled = True
            self.pick_directory_btn.enabled = True
            self.create_video_btn.enabled = True
            self.clear_btn.enabled = True


    """
    This call the backend through api
    """
    async def create_video_backend(self, widget):
        """Create video using backend API"""
        if self.is_processing:
            self.show_error("Already processing a video")
            return
        
        if not self.selected_images:
            self.show_error("Please select images first")
            return
        
        try:
            self.is_processing = True
            self.update_status("Starting video creation...")
            
            # Show progress container
            print("Creating video show_progress_container ...")
            self.show_progress_container()
            print("Creating video update_progress ...")
            self.update_progress(5)
            
            # Disable buttons during processing
            self.set_buttons_enabled(False)
            
            # Get settings from UI
            fps = int(self.fps_input.value) if self.fps_input else 24
            duration_per_image = float(self.duration_input.value) if self.duration_input else 2.0
            transition = self.transition_select.value.lower() if self.transition_select else "none"
            quality = self.quality_select.value.lower() if self.quality_select else "high"
            
            print(f"DEBUG: create_video Creating video with {len(self.selected_images)} images")
            print(f"DEBUG: create_video Settings - FPS: {fps}, Duration: {duration_per_image}, Transition: {transition}, quality: {quality}")
            
            
            if not hasattr(self, 'api_client') or self.api_client is None:
                self.api_client = await self.get_api_client()
            # Test connection first
            #if not await self.check_backend_connection():
            if not await self.api_client.test_connection():
                self.show_error("Cannot connect to video server")
                self.is_processing = False
                self.set_buttons_enabled(True)
                return
            
            # Send to backend for processing
            await self.process_with_backend(fps, duration_per_image, transition, quality)
            
        except Exception as e:
            error_msg = f"Video creation failed: {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            self.show_error(error_msg)
            self.is_processing = False
            self.set_buttons_enabled(True)
            self.hide_progress_container()
    
    async def check_backend_connection(self):
        """Check if backend is reachable"""
        try:
            print(f"DEBUG: video-view.py check_backend_connection calling {self.app.api_base_url}/health")
            if not hasattr(self, 'api_client') or self.api_client is None:
                self.api_client = await self.get_api_client()
            # Try to connect to the backend
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.app.api_base_url}/health") as response:
                    return response.status == 200
        except:
            return False
    
    async def process_with_backend(self, fps, duration_per_image, transition, quality):
        """Process video using backend API"""
        try:
            print(f"DEBUG: video-view.py process_with_backend fps={fps}")
            self.update_status("Uploading images to server...")
            self.update_progress(10)
            
            # Initialize API client
            if not hasattr(self, 'api_client') or self.api_client is None:
                self.api_client = await self.get_api_client()
            
            # Upload images and start processing
            result = await self.api_client.create_video(
                image_paths=self.selected_images,
                fps=fps,
                duration_per_image=duration_per_image,
                transition_type=transition,
                quality=quality
            )
            print(f"DEBUG: video-view.py process_with_backend calling self.api_client.create_video result={result}")
            
            #if not result.get('success', False):
            #    raise ValueError(result.get('error', 'Unknown error from server'))
            
            job_id = result.get('job_id')
            if not job_id:
                #raise ValueError("No job ID received from server")
                raise ValueError(result.get("message", "Failed to start video job on server"))                
            
            self.current_job_id = job_id
            self.update_status("Processing on server...")
            self.update_progress(20)
            
            # Poll for completion
            #await self.poll_backend_progress(job_id)
            print(f"DEBUG: video-view.py process_with_backend calling poll_video_progress job_id={job_id}")
            await self.poll_video_progress(job_id, self.api_client)
            
        except Exception as e:
            raise Exception(f"Backend processing failed: {str(e)}")
    
    async def poll_video_progress(self, job_id, api):
        """Poll for video progress"""
        print(f"DEBUG: video-view.py poll_video_progress job_id={job_id}")
        def on_progress_callback(progress, message, status):
            # This runs in the async context
            self.update_progress(progress)
            self.update_status(message)
            return True  # Continue polling
        
        result = await api.poll_status_new(
            job_id=job_id,
            on_progress=on_progress_callback,
            interval=2.0,
            timeout=600.0,
            max_attempts=300
        )
        
        if result.get('success'):
            self.update_status("Video created successfully!")
            self.download_btn.enabled = True
        else:
            raise ValueError(result.get('error', 'Processing failed'))
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.api_client:
            await self.api_client.close()
            
    async def poll_backend_progress(self, job_id):
        """Poll backend for processing progress"""
        try:
            print(f"DEBUG: video-view.py poll_backend_progress self.api_client.get_video_status(job_id) job_id={job_id}")
            last_progress = 0
            
            while True:
                # Get status from backend
                status = await self.api_client.get_video_status(job_id)
                
                if not status.get('success', True):
                    raise ValueError(status.get('error', 'Status check failed'))
                
                current_status = status.get('status')
                progress = status.get('progress', 0)
                message = status.get('message', 'Processing...')
                
                # Update UI
                if progress > last_progress:
                    self.update_progress(progress)
                    self.update_status(message)
                    last_progress = progress
                
                # Check if done
                if current_status == 'completed':
                    # Get video URL
                    video_url = status.get('video_url')
                    video_filename = os.path.basename(video_url) if video_url else None
                    
                    if video_filename:
                        self.current_video_filename = video_filename
                        self.current_job_id = job_id
                    
                    # Final update
                    self.update_progress(100)
                    self.update_status("Video created on server!")
                    
                    # Enable download button
                    self.download_btn.enabled = True
                    self.is_processing = False
                    self.set_buttons_enabled(True)
                    
                    # Show success message
                    if self.app and self.app.main_window:
                        await self.show_info_dialog("Video created successly!", 
                                    "Video has been created on the server.\nClick 'Download' to save it to your device.")
                    break
                    
                elif current_status == 'failed':
                    error_msg = status.get('message', 'Processing failed')
                    raise ValueError(f"Server processing failed: {error_msg}")
                
                # Wait before polling again
                await asyncio.sleep(2)  # Poll every 2 seconds
                
        except Exception as e:
            raise Exception(f"Progress polling failed: {str(e)}")
    
    async def download_video_bk0(self, widget):
        """Download video from backend"""
        try:
            print(f"DEBUG: video-view.py download_video self.current_job_id={self.current_job_id}")
            if not self.current_job_id:
                self.show_error("No video has been created yet")
                return
            
            self.update_status("Preparing download...")
            self.show_progress_container()
            self.update_progress(10)
            
            # Get save location
            save_path = await self.get_save_location()
            
            if not save_path:
                self.update_status("Download cancelled")
                self.hide_progress_container()
                return
            
            self.update_progress(30)
            self.update_status("Downloading video...")
            
            # Download from backend
            if not hasattr(self, 'api_client') or self.api_client is None:
                self.api_client = await self.get_api_client()
            
            # Get filename from job status
            status = await self.api_client.get_video_status(self.current_job_id)
            if status.get('status') != 'completed':
                raise ValueError("Video is not ready for download")
            
            video_url = status.get('video_url')
            if not video_url:
                raise ValueError("No video URL available")
            
            video_filename = os.path.basename(video_url)
            
            # Download the file
            success = await self.api_client.download_video(video_filename, save_path)
            
            if not success:
                raise ValueError("Download failed")
            
            self.update_progress(100)
            self.update_status("Download complete!")
            
            # Show success
            await self.show_download_success(save_path)
            
            # Hide progress
            self.hide_progress_container()
            
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            self.show_error(error_msg)
            self.hide_progress_container()
        
    """ 
    The following is create video on the client side 
    """
    
    async def create_video(self, widget):
        if USE_BACKEND_API_CALL:
            await self.create_video_backend(widget)
        else:
            await self.create_video_frontend(widget)
        
    
    async def create_video_frontend(self, widget):
        """Create actual H.264 video from selected images"""
        print(f"Creating video from selected images self.is_processing:{self.is_processing}")
        if self.is_processing:
            self.show_error("Already processing a video")
            return
        
        print(f"Creating video from selected {len(self.selected_images)} images")
        if not self.selected_images:
            self.show_error("Please select images first")
            return
        
        try:
            self.is_processing = True
            self.update_status("Starting video creation...")
            
            # Show progress container
            print("Creating video show_progress_container ...")
            self.show_progress_container()
            print("Creating video update_progress ...")
            self.update_progress(5)
            
            # Disable buttons during processing
            self.set_buttons_enabled(False)
            
            # Get settings from UI
            fps = int(self.fps_input.value) if self.fps_input else 24
            duration_per_image = float(self.duration_input.value) if self.duration_input else 2.0
            transition = self.transition_select.value.lower() if self.transition_select else "none"
            quality = "high"  # Default quality
            
            print(f"DEBUG: create_video Creating video with {len(self.selected_images)} images")
            print(f"DEBUG: create_video Settings - FPS: {fps}, Duration: {duration_per_image}, Transition: {transition}, quality: {quality}")
            
            # Create actual video using OpenCV
            #await self.create_actual_video(fps, duration_per_image, transition, quality)
            await self.create_video_with_ffmpeg(fps, duration_per_image, transition, quality)
            """3. Alternative: Using FFmpeg (Recommended for Better H.264)
            Key Changes:
            1. H.264 Codec Support: Uses libx264 codec via FFmpeg or OpenCV's H.264 codec
            2. Even Dimensions: Ensures width and height are even numbers (H.264 requirement)
            3. Proper Pixel Format: Uses yuv420p for broad compatibility
            4. Faststart Flag: Enables streaming/quick playback
            5. Quality Settings: Configurable CRF and preset for quality/size trade-off
            6. Video Verification: Checks that files are created and not empty
            7. Error Handling: Comprehensive error handling for all failure modes            
            """
            
            # Enable buttons
            self.set_buttons_enabled(True)
            self.is_processing = False
            
            # Enable download button
            self.download_btn.enabled = True
            # Set a simulated video path
            print("DEBUG: Video creation complete, download enabled")
            
        except Exception as e:
            error_msg = f"Video creation failed: {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            self.show_error(error_msg)
            self.is_processing = False
            self.set_buttons_enabled(True)
            self.hide_progress_container()

    def get_simulated_video_path(self):
        """Get a simulated video path for download"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"video_{timestamp}.mp4"
    
    def set_buttons_enabled(self, enabled):
        """Enable or disable all action buttons"""
        buttons = [
            self.pick_images_btn,
            self.pick_directory_btn,
            self.clear_btn,
            self.create_video_btn,
            self.download_btn
        ]
        
        for button in buttons:
            if button:
                button.enabled = enabled
                

    async def create_actual_video(self, fps, duration_per_image, transition, quality):
        """Create actual H.264 video file"""
        try:
            print(f"create_actual_video Preparing images calling update_status/update_progress self.selected_images={self.selected_images}")
            self.update_status("Preparing images...")
            self.update_progress(10)
            
            # Validate images exist
            valid_images = []
            for img_path in self.selected_images:
                if isinstance(img_path, str) and Path(img_path).exists():
                    valid_images.append(img_path)
                else:
                    print(f"DEBUG: Image not found: {img_path}")
            
            print(f"create_actual_video calling update_status/update_progress valid_images={valid_images}")
            if not valid_images:
                raise ValueError("No valid images found")
            
            print(f"2 create_actual_video Processing images calling update_status/update_progress  valid_images={valid_images}")
            self.update_status(f"Processing {len(valid_images)} images...")
            self.update_progress(20)
            
            # Read first image to get dimensions
            first_img = cv2.imread(valid_images[0])
            if first_img is None:
                raise ValueError(f"Could not read first image: {valid_images[0]}")
            
            height, width = first_img.shape[:2]
            
            # Ensure even dimensions for H.264
            width = width - (width % 2)
            height = height - (height % 2)
            
            print(f"3 create_actual_video Creating video frames calling update_status/update_progress image height={height}")
            self.update_status("Creating video frames...")
            self.update_progress(35)
            
            # Create temporary video file
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_video_path = os.path.join(temp_dir, f"temp_video_{timestamp}.mp4")
            
            # Try different H.264 codecs
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
                        temp_video_path,
                        fourcc,
                        fps,
                        (width, height),
                        True
                    )
                    
                    if video_writer.isOpened():
                        codec_used = codec_name
                        print(f"DEBUG: Using codec: {codec_name}")
                        break
                    else:
                        if video_writer:
                            video_writer.release()
                except Exception as e:
                    print(f"DEBUG: Codec {codec_name} failed: {e}")
                    continue
            
            if not video_writer or not video_writer.isOpened():
                raise ValueError("Could not create video writer with any codec")
            
            try:
                frames_per_image = int(duration_per_image * fps)
                total_frames = len(valid_images) * frames_per_image
                frames_written = 0
                
                print(f"4 create_actual_video Encoding video calling update_status total_frames={total_frames}")
                self.update_status("Encoding video...")
                
                # Process each image
                for i, img_path in enumerate(valid_images):
                    # Update progress based on images processed
                    image_progress = 35 + (i / len(valid_images)) * 50
                    self.update_progress(int(image_progress))
                    self.update_status(f"Processing image {i+1}/{len(valid_images)}...")
                    
                    img = cv2.imread(img_path)
                    if img is None:
                        print(f"DEBUG: Could not read image: {img_path}")
                        continue
                    
                    # Resize if needed
                    if img.shape[:2] != (height, width):
                        img = cv2.resize(img, (width, height), interpolation=cv2.INTER_LANCZOS4)
                    
                    # Write frames for this image
                    for _ in range(frames_per_image):
                        video_writer.write(img)
                        frames_written += 1
                    
                    # Add transition if specified
                    if transition != "none" and i < len(valid_images) - 1:
                        next_img = cv2.imread(valid_images[i + 1])
                        if next_img is not None:
                            if next_img.shape[:2] != (height, width):
                                next_img = cv2.resize(next_img, (width, height))
                            
                            if transition == "fade":
                                self.add_fade_transition(video_writer, img, next_img, fps)
                            elif transition == "slide":
                                self.add_slide_transition(video_writer, img, next_img, fps)
                
                video_writer.release()
                cv2.destroyAllWindows()
                
                print("5 create_actual_video Finalizing video frames calling update_status/update_progress ")
                self.update_progress(90)
                self.update_status("Finalizing video...")
                
                # Verify video was created
                if not os.path.exists(temp_video_path):
                    raise ValueError("Video file was not created")
                
                video_size = os.path.getsize(temp_video_path)
                if video_size == 0:
                    raise ValueError("Video file is empty")
                
                # Store the video path for download
                self.current_video_path = temp_video_path
                
                # Convert to final filename
                final_filename = f"video_{timestamp}.mp4"
                self.current_video_filename = final_filename
                
                self.update_progress(100)
                self.update_status(f"H.264 video created successfully! ({self.format_bytes(video_size)}), self.current_video_filename={self.current_video_filename}, self.current_video_path={self.current_video_path}")
                
                print(f"DEBUG: Video created: {temp_video_path}")
                print(f"DEBUG: Video size: {video_size} bytes")
                print(f"DEBUG: Codec used: {codec_used}")
                print(f"DEBUG: Resolution: {width}x{height}")
                print(f"DEBUG: FPS: {fps}")
                print(f"DEBUG: Total frames: {frames_written}")
                
                # Show success message
                await asyncio.sleep(1)
                self.hide_progress_container()
                
                if self.app and self.app.main_window:
                    message = f"""
    ✅ H.264 VIDEO CREATED SUCCESSFULLY!    
    • Resolution: {width}x{height}
    • Frame rate: {fps} FPS
    • Duration: {(frames_written / fps):.1f} seconds
    • File size: {self.format_bytes(video_size)}
    • Codec: {codec_used}
    • Images used: {len(valid_images)}
    
    Click 'Download Video' to save it to your device.
    """
                    await self.show_info_dialog("Video Created", message.strip())
                
            finally:
                if video_writer:
                    video_writer.release()
                
        except Exception as e:
            print(f"DEBUG ERROR in create_actual_video: {e}")
            raise
            
            
    async def create_video_with_ffmpeg(self, fps, duration_per_image, transition, quality):
        """Create H.264 video using FFmpeg (most reliable)"""
        try:
            print("create_video_with_ffmpeg calling update_status")
            self.update_status("Checking FFmpeg...")
            
            # Check if FFmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
                has_ffmpeg = True
            except:
                has_ffmpeg = False
                self.update_status("FFmpeg not found, using OpenCV...")
            
            if has_ffmpeg:
                await self._create_with_ffmpeg(fps, duration_per_image, quality)
            else:
                await self._create_with_opencv(fps, duration_per_image, transition)
                
        except Exception as e:
            raise Exception(f"FFmpeg video creation failed: {str(e)}")
    
    async def _create_with_ffmpeg(self, fps, duration_per_image, quality):
        """Create video using FFmpeg"""
        
        try:
            temp_dir = tempfile.mkdtemp(prefix="video_frames_")
            print(f"_create_with_ffmpeg  temp_dir={temp_dir}, calling update_status/update_progress")
            self.update_status("Preparing images for FFmpeg...")
            self.update_progress(20)
            
            #for i, img_path in enumerate(self.selected_images):
            #    img = cv2.imread(img_path)
            #    if img is not None:
            #        # Resize to even dimensions
            #        height, width = img.shape[:2]
            #        width = width - (width % 2)
            #        height = height - (height % 2)
            #       
            #        if img.shape[:2] != (height, width):
            #            img = cv2.resize(img, (width, height), interpolation=cv2.INTER_LANCZOS4)                    
            #        temp_path = os.path.join(temp_dir, f"frame_{i:06d}.png")
            #        cv2.imwrite(temp_path, img)                    
            #    progress = 20 + (i / len(self.selected_images)) * 40
            #    self.update_progress(int(progress))
            
            # 1. Calculate how many times to repeat each image to hit the duration
            # If duration_per_image is 2.0s and fps is 24, we need 48 frames per image
            frames_per_image = max(1, int(fps * duration_per_image))
            global_frame_idx = 0
            for i, img_path in enumerate(self.selected_images):
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
                
                progress = 10 + (i / len(self.selected_images)) * 50
                self.update_progress(int(progress))
            
            self.update_status("Creating H.264 video with FFmpeg...")
            self.update_progress(65)
            
            frame_count = len(self.selected_images)
            total_duration = frame_count / fps
            print(f"_create_with_ffmpeg settings fps={fps}, frame_count={frame_count}, total_duration={total_duration}")
            
            # Create video using FFmpeg
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_path = os.path.join(tempfile.gettempdir(), f"video_{timestamp}.mp4")
            print(f"_create_with_ffmpeg settings fps={fps}, timestamp={timestamp}, video_path={video_path}")
            
            # H.264 encoding settings
            preset = "medium"  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
            crf = 23  # Constant Rate Factor (0-51, lower is better quality)
                        
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',  # Overwrite output
                '-framerate', str(fps),
                '-i', os.path.join(temp_dir, 'frame_%06d.png'),
                '-c:v', 'libx264',  # H.264 codec
                '-preset', preset,
                '-crf', str(crf),
                '-pix_fmt', 'yuv420p',  # Required for compatibility
                '-movflags', '+faststart',  # Enable streaming
            #    '-r', str(fps),
                video_path
            ]
            
            print(f"DEBUG: Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
            """ sample command
            ffmpeg -y -framerate 24 -i C:/Users/javau/AppData/Local/Temp\video_frames_bvxs04og/frame_%06d.png -c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p -movflags +faststart -r 24 C:/Users/javau/AppData/Local/Temp/video_20260124_165034.mp4
            
            run and calculate during in shell script as follows
                 ffprobe -show_entries format=duration -of default=noprint_wrappers=1 output.mp4
             duration = frames / fps
            """
            
            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.update_progress(80)
            self.update_status("Encoding H.264 video...")
            
            # Wait for completion
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")
            
            self.update_progress(95)
            
            # Verify output
            if not os.path.exists(video_path):
                raise ValueError("FFmpeg did not create output file")
            
            video_size = os.path.getsize(video_path)
            if video_size == 0:
                raise ValueError("Output video file is empty")
            
            self.current_video_path = video_path
            self.current_video_filename = f"video_{timestamp}.mp4"
            
            self.update_progress(100)
            self.update_status(f"H.264 video created with FFmpeg! ({self.format_bytes(video_size)})")
            
            print(f"DEBUG: FFmpeg video created: {video_path}")
            print(f"DEBUG: Video size: {video_size} bytes")
            
        finally:
            # Cleanup temp directory
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    async def _create_with_opencv(self, fps, duration_per_image, transition):
        """Create video using OpenCV when FFmpeg is not available"""
        try:
            print(f"DEBUG: _create_with_opencv OpenCV version: {cv2.__version__}")
            self.update_status("Creating video with OpenCV...")
            self.update_progress(25)
            
            # Validate and prepare images
            start_time = time.time()            
            valid_images = []
            for img_path in self.selected_images:
                if isinstance(img_path, str):
                    path = Path(img_path)
                    if path.exists():
                        valid_images.append(str(path))
                    else:
                        print(f"DEBUG: Image not found, using placeholder: {img_path}")
                        # Create a placeholder image
                        placeholder = self._create_placeholder_image()
                        temp_path = os.path.join(tempfile.gettempdir(), f"placeholder_{len(valid_images)}.png")
                        cv2.imwrite(temp_path, placeholder)
                        valid_images.append(temp_path)
                else:
                    print(f"DEBUG: Invalid image path type: {type(img_path)}")
            
            if not valid_images:
                raise ValueError("No valid images to process")
            print(f"DEBUG: Processing {len(valid_images)} images with OpenCV")
            
            end_time = time.time()
            frame_count = len(self.selected_images)
            duration = end_time - start_time
            fps_calc = max(1, round(frame_count / duration, 2))
            print(f"_create_with_ffmpeg settings fps={fps}, to be reset to thes fps_calc={fps_calc}, duration={duration}, frame_count={frame_count}")
            fps = fps_calc
            
            # Read first image to get dimensions
            first_img = cv2.imread(valid_images[0])
            if first_img is None:
                # Try to load as PIL and convert
                try:
                    from PIL import Image
                    pil_img = Image.open(valid_images[0])
                    first_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                except:
                    raise ValueError(f"Could not read first image: {valid_images[0]}")
            
            height, width = first_img.shape[:2]
            
            # Ensure even dimensions (required by most codecs)
            width = width - (width % 2)
            height = height - (height % 2)
            size = (width, height)
            
            self.update_status(f"Setting up video: {width}x{height} @ {fps} FPS")
            self.update_progress(30)
            
            # Create output video path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_path = os.path.join(tempfile.gettempdir(), f"opencv_video_{timestamp}.mp4")
            print(f"DEBUG: reate output video path={video_path} image with OpenCV")

            # Try different video codecs in order of preference
            codecs = [
                ('H264', cv2.VideoWriter_fourcc(*'H264')),  # Best for H.264
                ('X264', cv2.VideoWriter_fourcc(*'X264')),  # Alternative H.264
                ('AVC1', cv2.VideoWriter_fourcc(*'avc1')),  # Another H.264 variant
                ('MP4V', cv2.VideoWriter_fourcc(*'mp4v')),  # MPEG-4
                ('MJPG', cv2.VideoWriter_fourcc(*'MJPG')),  # Motion JPEG
                ('XVID', cv2.VideoWriter_fourcc(*'XVID')),  # XVID
            ]
            
            video_writer = None
            codec_used = None
            
            for codec_name, fourcc in codecs:
                try:
                    print(f"DEBUG: Trying codec: {codec_name}")
                    video_writer = cv2.VideoWriter(
                        video_path,
                        fourcc,
                        fps,
                        size,
                        True  # Is color
                    )
                    
                    if video_writer.isOpened():
                        codec_used = codec_name
                        print(f"DEBUG: Successfully opened video writer with codec: {codec_name}")
                        break
                    else:
                        if video_writer:
                            video_writer.release()
                        print(f"DEBUG: Codec {codec_name} failed to open")
                except Exception as e:
                    print(f"DEBUG: Codec {codec_name} error: {e}")
                    continue
            
            if not video_writer or not video_writer.isOpened():
                # Try one more time with default parameters
                try:
                    print("DEBUG: Trying fallback with default parameters")
                    video_writer = cv2.VideoWriter(
                        video_path,
                        cv2.VideoWriter_fourcc(*'mp4v'),
                        fps,
                        size
                    )
                    if video_writer.isOpened():
                        codec_used = 'MP4V (fallback)'
                        print("DEBUG: Fallback succeeded")
                    else:
                        raise ValueError("Could not create video writer with any codec")
                except Exception as e:
                    raise ValueError(f"All video codecs failed: {e}")
            
            try:
                # Calculate frames per image
                frames_per_image = max(1, int(duration_per_image * fps))
                total_images = len(valid_images)
                total_frames = total_images * frames_per_image
                
                print(f"DEBUG: Video parameters: - Resolution: {width}x{height}")
                print(f"  - FPS: {fps}")
                print(f"  - Frames per image: {frames_per_image}")
                print(f"  - Total images: {total_images}")
                print(f"  - Estimated total frames: {total_frames}")
                print(f"  - Codec: {codec_used}")
                print(f"  - Transition: {transition}")
                
                self.update_status(f"Processing {total_images} images...")
                
                # Process each image
                for i, img_path in enumerate(valid_images):
                    # Calculate and update progress
                    image_progress = 30 + (i / total_images) * 60
                    self.update_progress(int(image_progress))
                    self.update_status(f"Processing image {i+1}/{total_images}...")
                    
                    # Load image
                    img = cv2.imread(img_path)
                    if img is None:
                        print(f"DEBUG: Could not load {img_path}, creating placeholder")
                        img = self._create_placeholder_image()
                    
                    # Resize to target dimensions
                    if img.shape[:2] != (height, width):
                        img = cv2.resize(img, size, interpolation=cv2.INTER_LANCZOS4)
                    
                    # Write the image for the specified duration
                    for frame_num in range(frames_per_image):
                        video_writer.write(img)
                    
                    # Add transition if specified and not the last image
                    if transition != "none" and i < total_images - 1:
                        # Load next image for transition
                        next_img_path = valid_images[i + 1]
                        next_img = cv2.imread(next_img_path)
                        if next_img is None:
                            next_img = self._create_placeholder_image()
                        
                        # Resize next image
                        if next_img.shape[:2] != (height, width):
                            next_img = cv2.resize(next_img, size, interpolation=cv2.INTER_LANCZOS4)
                        
                        # Apply transition
                        if transition == "fade":
                            await self._apply_fade_transition(video_writer, img, next_img, fps)
                        elif transition == "slide":
                            await self._apply_slide_transition(video_writer, img, next_img, fps)
                        elif transition == "zoom":
                            await self._apply_zoom_transition(video_writer, img, next_img, fps)
                
                # Release the video writer
                video_writer.release()
                
                # Give system time to finalize file
                await asyncio.sleep(0.5)
                
                self.update_progress(95)
                self.update_status("Finalizing video file...")
                
                # Verify the video was created
                if not os.path.exists(video_path):
                    raise ValueError(f"Video file was not created at {video_path}")
                
                video_size = os.path.getsize(video_path)
                if video_size == 0:
                    raise ValueError("Video file is empty (0 bytes)")
                
                # Try to open and verify the video
                cap = cv2.VideoCapture(video_path)
                if cap.isOpened():
                    actual_fps = cap.get(cv2.CAP_PROP_FPS)
                    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    cap.release()
                    
                    print(f"DEBUG: Video created successfully:  - File: {video_path}")
                    print(f"  - Size: {await self._format_bytes(video_size)}")
                    print(f"  - Actual resolution: {actual_width}x{actual_height}")
                    print(f"  - Actual FPS: {actual_fps}")
                    print(f"  - Frame count: {frame_count}")
                    print(f"  - Duration: {frame_count/actual_fps:.2f} seconds")
                    
                    if actual_width == 0 or actual_height == 0:
                        print("DEBUG: WARNING: Video has invalid dimensions")
                    
                    if frame_count == 0:
                        print("DEBUG: WARNING: Video has 0 frames")
                else:
                    print("DEBUG: WARNING: Could not open video for verification")
                    # File might still be valid but OpenCV can't read it
                
                # Store video information
                self.current_video_path = video_path
                self.current_video_filename = f"video_{timestamp}.mp4"
                self.video_info = {
                    'path': video_path,
                    'size': video_size,
                    'codec': codec_used,
                    'resolution': f"{width}x{height}",
                    'fps': fps,
                    'images_used': total_images,
                    'created_at': datetime.now().isoformat()
                }
                
                self.update_progress(100)
                self.update_status(f"Video created successfully! ({await self._format_bytes(video_size)})")
                
                print(f"DEBUG: Video ready for download: self.current_video_filename={self.current_video_filename}, self.current_video_path={self.current_video_path}")
                
            except Exception as e:
                print(f"Error: Creating Video : {e}")
                # Clean up video writer if it exists
                if video_writer:
                    try:
                        video_writer.release()
                    except:
                        pass
                raise
        
        except Exception as e:
            print(f"DEBUG ERROR in _create_with_opencv: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"OpenCV video creation failed: {str(e)}")
        
    async def _apply_fade_transition(self, writer, img1, img2, fps, duration=0.5):
        """Apply fade transition between two images"""
        transition_frames = max(1, int(duration * fps))
        
        for i in range(transition_frames):
            alpha = i / transition_frames
            beta = 1 - alpha
            
            # Blend the two images
            blended = cv2.addWeighted(img1, beta, img2, alpha, 0)
            writer.write(blended)
            
            # Small delay to prevent UI freezing
            if i % 5 == 0:  # Yield every 5 frames
                await asyncio.sleep(0)
    
    async def _apply_slide_transition(self, writer, img1, img2, fps, duration=0.5):
        """Apply slide transition between two images"""
        transition_frames = max(1, int(duration * fps))
        height, width = img1.shape[:2]
        
        for i in range(transition_frames):
            # Calculate slide offset
            offset = int((i / transition_frames) * width)
            
            # Create sliding effect
            frame = np.zeros_like(img1)
            
            # Left part from current image (img1)
            if offset > 0:
                frame[:, :width-offset] = img1[:, offset:]
            
            # Right part from next image (img2)
            if offset < width:
                frame[:, width-offset:] = img2[:, :offset]
            
            writer.write(frame)
            
            # Small delay to prevent UI freezing
            if i % 5 == 0:
                await asyncio.sleep(0)
    
    async def _apply_zoom_transition(self, writer, img1, img2, fps, duration=0.5):
        """Apply zoom transition between two images"""
        transition_frames = max(1, int(duration * fps))
        height, width = img1.shape[:2]
        
        for i in range(transition_frames):
            # Calculate zoom factor
            zoom_factor = 1.0 + (i / transition_frames) * 0.3  # Zoom out 30%
            
            # Create zoomed versions
            if zoom_factor > 1.0:
                # Zoom out current image
                new_width = int(width / zoom_factor)
                new_height = int(height / zoom_factor)
                x_offset = (width - new_width) // 2
                y_offset = (height - new_height) // 2
                
                # Resize and place in center
                zoomed_img1 = cv2.resize(img1, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
                frame = np.zeros_like(img1)
                frame[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = zoomed_img1
            else:
                # Start with normal image
                frame = img1.copy()
            
            writer.write(frame)
            
            # Small delay
            if i % 5 == 0:
                await asyncio.sleep(0)
    
    def _create_placeholder_image(self, width=1920, height=1080):
        """Create a placeholder image when real images fail to load"""
        # Create a gradient background
        placeholder = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add gradient
        for y in range(height):
            color_value = int(50 + (y / height) * 100)
            placeholder[y, :] = [color_value, color_value, color_value + 50]
        
        # Add text
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = "Image Placeholder"
        text_size = cv2.getTextSize(text, font, 2, 3)[0]
        text_x = (width - text_size[0]) // 2
        text_y = (height + text_size[1]) // 2
        
        cv2.putText(placeholder, text, (text_x, text_y), font, 2, (255, 255, 255), 3)
        
        return placeholder
              
        
    def add_fade_transition(self, writer, img1, img2, fps, duration=0.5):
        """Add fade transition between images"""
        transition_frames = int(duration * fps)
        for i in range(transition_frames):
            alpha = i / transition_frames
            beta = 1 - alpha
            blended = cv2.addWeighted(img1, beta, img2, alpha, 0)
            writer.write(blended)
    
    def add_slide_transition(self, writer, img1, img2, fps, duration=0.5):
        """Add slide transition between images"""
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
    
    def format_bytes(self, size):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


    async def simulate_video_processing(self, settings):
        """Simulate the video processing steps"""
        print(f"simulate_video_processing Simulating video processing settings={settings}")
        steps = [
            (10, "Validating images..."),
            (20, "Processing image sizes..."),
            (35, "Applying transition effects..."),
            (50, "Encoding video frames..."),
            (70, "Optimizing video quality..."),
            (85, "Finalizing video file..."),
            (100, "Video created successfully!")
        ]

        for progress, message in steps:
            await asyncio.sleep(1.5)  # Simulate processing time
            print(f"simulate_video_processing update_progress progress={progress}")
            self.update_progress(progress)
            print(f"simulate_video_processing update_progress update_status={message}")
            self.update_status(message)

            if progress == 100:
                # Show download button when complete
                print("simulate_video_processing show_download_section ...")
                self.show_download_section()
                print("simulate_video_processing waiting download dialog")
                if self.app and self.app.main_window:
                    # self.app.main_window.error_dialog("Error", message)
                    print(f"DEBUG: simulate_video_processing self.app.main_window={self.app.main_window}")
                    await self.show_info_dialog(
                            title="Download Success!",
                            message=f"Video created from {len(self.selected_images)} images!\n\n Settings: {settings['fps']} FPS, {settings['duration_per_image']}s per image"
                        )                    
                else:
                    print("DEBUG: simulate_video_processing Cannot show download dialog - self.app.main_window not available")

                self.is_processing = False

    async def download_video(self, widget):
        """Download the created video"""
        try:
            print(f"DEBUG: self.current_video_path = {self.current_video_path}")            
            if not self.current_video_path:
                print("DEBUG: No video created yet, simulating one...")
                await self.create_video()
                
            
                if not self.current_video_path:
                    raise ValueError("Video creation failed")                
                    return
            
            print(f"DEBUG: Starting download of {self.current_video_path}")
            await self.perform_download()
            
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            self.show_error(error_msg)
            
            
    async def perform_download(self):
        """Perform the actual download/save operation"""
        try:
            self.update_status("Preparing download...")
            self.show_progress_container()
            self.update_progress(10)
            
            if not self.current_video_path:
                self.update_status("Creating video first...")
                await self.create_video()
                if not self.current_video_path:
                    raise ValueError("Video creation failed")
            
            # Get save location
            save_path = await self.get_save_location()
            
            if not save_path:
                self.update_status("Download cancelled")
                self.hide_progress_container()
                return
            
            self.update_progress(30)
            self.update_status(f"Saving to: {os.path.basename(save_path)}")
            
            # Show copying progress
            self.update_progress(40)
            
            # Save the actual video file
            save_result = await self.save_video_file(save_path)
            
            if not save_result.get('success', False):
                raise RuntimeError(save_result.get('error', 'Unknown error during save'))
            
            self.update_progress(90)
            self.update_status("Finalizing...")
            
            # Verify the file
            if not os.path.exists(save_path):
                raise FileNotFoundError(f"Video was not saved to {save_path}")
            
            file_size = os.path.getsize(save_path)
            if file_size == 0:
                raise ValueError("Saved video file is empty")
            
            self.update_progress(100)
            self.update_status(f"Video saved! ({await self._format_bytes(file_size)})")
            
            # Show success with file details
            await self.show_download_success(save_path, save_result)
            
            # Hide progress
            self.hide_progress_container()
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            self.show_error(f"Download failed: {str(e)}")
            self.hide_progress_container()
            raise
                
    async def get_save_location(self):
        """Get location to save the video with user interaction"""
        try:
            print(f"DEBUG: get_save_location self.current_video_filename: {self.current_video_filename}")
            # Generate default filename
            if hasattr(self, 'current_video_filename') and self.current_video_filename:
                default_name = self.current_video_filename
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_name = f"video_{timestamp}.mp4"
            
            # Try to use platform-specific save dialog
            save_path = await self._get_save_path_from_dialog(default_name)
            print(f"DEBUG: get_save_location Using fallback save path: {save_path}")
            
            if save_path:
                return save_path
            
            # Fallback: Use downloads folder
            downloads_path = self.get_downloads_folder()
            save_path = os.path.join(downloads_path, default_name)
            
            # Ensure unique filename
            save_path = self._ensure_unique_filename(save_path)
            
            print(f"DEBUG: get_save_location Using fallback save path: {save_path}")
            return save_path
            
        except Exception as e:
            print(f"DEBUG: Error getting save location: {e}")
            # Ultimate fallback
            return os.path.join(os.getcwd(), default_name)
    
    async def _get_save_path_from_dialog(self, default_name):
        """Try to get save path from platform-specific dialog"""
        try:
            if self.app and hasattr(self.app, 'main_window') and self.app.main_window:
                # For Toga, we need to check if save_file_dialog is available
                if hasattr(self.app.main_window, 'save_file_dialog'):
                    save_path = await self.app.main_window.dialog(
                        toga.SaveFileDialog(
                            title="Save Video As",
                            suggested_filename=default_name,
                            file_types=[("MP4 files", "*.mp4"), ("All files", "*.*")]
                        )
                    )                                          
                    return save_path
        except Exception as e:
            print(f"DEBUG: Save dialog failed: {e}")
        
        return None
    
    def _ensure_unique_filename(self, filepath):
        """Ensure filename is unique by adding counter if needed"""
        if not os.path.exists(filepath):
            return filepath
        
        base, ext = os.path.splitext(filepath)
        counter = 1
        
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
        
        return f"{base}_{counter}{ext}"            
                    
    async def save_video_file(self, save_path):
        """Copy the actual video file to the specified save location"""
        try:
            print(f"DEBUG: save_video_file called with save_path={save_path}")
            print(f"DEBUG: current_video_path={self.current_video_path}")
            print(f"DEBUG: current_video_filename={self.current_video_filename}")
            
            if not self.current_video_path:
                raise ValueError("No video has been created yet. Please create a video first.")
            
            # Check if source video exists
            if not os.path.exists(self.current_video_path):
                raise FileNotFoundError(f"Source video file not found: {self.current_video_path}")
            
            # Get source file info
            source_size = os.path.getsize(self.current_video_path)
            print(f"DEBUG: Source video size: {source_size} bytes")
            
            if source_size == 0:
                raise ValueError("Source video file is empty (0 bytes)")
            
            # Ensure the destination directory exists
            save_dir = os.path.dirname(save_path)
            if save_dir and not os.path.exists(save_dir):
                print(f"DEBUG: Creating directory: {save_dir}")
                os.makedirs(save_dir, exist_ok=True)
            
            # Check if destination file already exists
            if os.path.exists(save_path):
                # Create a unique filename
                base, ext = os.path.splitext(save_path)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                save_path = f"{base}_{counter}{ext}"
                print(f"DEBUG: File exists, using new name: {save_path}")
            
            # Copy the actual video file
            print(f"DEBUG: Copying video from {self.current_video_path} to {save_path}")
            
            # Show copying progress
            self.update_status("Copying video file...")
            
            # Use shutil.copy2 to preserve metadata
            # Method 1: Use shutil.copy2 (recommended for files)
            try:
                shutil.copy2(self.current_video_path, save_path)
                print(f"DEBUG: Video copied successfully using shutil.copy2 to save_path={save_path}")
                
            except Exception as copy_error:
                print(f"DEBUG: shutil.copy2 failed: {copy_error} \n\n retry using _copy_file_with_progress")
                
                # Method 2: Manual copy with progress
                await self._copy_file_with_progress(self.current_video_path, save_path)
            
            # Verify the copy was successful
            if not os.path.exists(save_path):
                raise RuntimeError("Copy operation failed - destination file not created")
            
            dest_size = os.path.getsize(save_path)
            print(f"DEBUG: Destination video size: {dest_size} bytes")
            
            if dest_size == 0:
                raise RuntimeError("Destination video file is empty (0 bytes)")
            
            if dest_size != source_size:
                print(f"DEBUG: WARNING: Source size ({source_size}) != Destination size ({dest_size})")
                # Check if file is at least partially copied
                if dest_size < source_size * 0.9:  # Less than 90% of source size
                    raise RuntimeError(f"Incomplete copy: {dest_size} bytes vs {source_size} bytes")
            
            # Get video info for confirmation
            video_info = self._get_video_file_info(save_path)
            
            print(f"DEBUG: Video saved successfully:   - Path: {save_path}")
            print(f"  - Size: {dest_size} bytes ({await self._format_bytes(dest_size)})")
            print(f"  - Exists: {os.path.exists(save_path)}")
            print(f"  - Readable: {os.access(save_path, os.R_OK)}")
            
            # Store the saved path for reference
            self.last_saved_path = save_path
            
            return {
                'success': True,
                'save_path': save_path,
                'filename': os.path.basename(save_path),
                'size': dest_size,
                'formatted_size': await self._format_bytes(dest_size),
                'video_info': video_info
            }
            
        except Exception as e:
            error_msg = f"Failed to save video: {str(e)}"
            print(f"DEBUG ERROR in save_video_file: {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Clean up partially copied file if it exists
            if 'save_path' in locals() and os.path.exists(save_path):
                try:
                    os.remove(save_path)
                    print(f"DEBUG: Cleaned up incomplete file: {save_path}")
                except:
                    pass
            
            raise Exception(error_msg)
    
    async def _copy_file_with_progress(self, source_path, dest_path):
        """Copy file manually with progress updates"""
        try:
            print(f"DEBUG: Starting manual file copy: Source: {source_path}")
            print(f"DEBUG: Destination: {dest_path}")
            
            # Get total size
            total_size = os.path.getsize(source_path)
            print(f"DEBUG: Total size to copy: {total_size} bytes")
            
            # Open source file for reading
            with open(source_path, 'rb') as src_file:
                # Open destination file for writing
                with open(dest_path, 'wb') as dest_file:
                    # Copy in chunks to show progress
                    chunk_size = 1024 * 1024  # 1MB chunks
                    copied = 0
                    
                    while True:
                        # Read chunk
                        chunk = src_file.read(chunk_size)
                        if not chunk:
                            break
                        
                        # Write chunk
                        dest_file.write(chunk)
                        copied += len(chunk)
                        
                        # Update progress (if we're in a progress context)
                        progress_percent = (copied / total_size) * 100
                        print(f"DEBUG: Copy progress: {progress_percent:.1f}% ({await self._format_bytes(copied)}/{await self._format_bytes(total_size)})")
                        
                        # Small async yield to prevent blocking
                        await asyncio.sleep(0.001)
            
            print(f"DEBUG: Manual copy completed successfully from source_path {source_path}, \n dest_path {dest_path}")
            
        except Exception as e:
            print(f"DEBUG ERROR in _copy_file_with_progress: {e}")
            raise
    
    
    def _get_video_file_info(aelf, filepath):
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=width,height,avg_frame_rate,codec_name",
            "-of", "json", str(filepath)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout)
    
    
    def _get_video_file_info_slower(self, filepath):
        cap = cv2.VideoCapture(filepath)
    
        if not cap.isOpened():
            raise RuntimeError("Could not open video")
    
        info = {}
        info["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        info["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # ⚠ These may be slow:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    
        info["fps"] = fps
        info["frame_count"] = int(frames)
        info["duration"] = frames / fps if fps > 0 else 0
    
        cap.release()
        return info    
    
    
    def _get_video_file_info_sloweat(self, filepath):
        """Get information about the video file"""
        try:
            print(f"_get_video_file_info filepath={filepath}")
            info = {
                'path': filepath,
                'filename': os.path.basename(filepath),
                'size': os.path.getsize(filepath),
                'exists': os.path.exists(filepath),
                'created': datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
            }
            print(f"_get_video_file_info info={info}")
            
            # Try to get video properties using OpenCV
            try:
                cap = cv2.VideoCapture(filepath)
                print(f"_get_video_file_info cap.isOpened()={cap.isOpened()}")
                if cap.isOpened():
                    info['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    info['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    info['fps'] = cap.get(cv2.CAP_PROP_FPS)
                    info['frame_count'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    info['duration'] = info['frame_count'] / info['fps'] if info['fps'] > 0 else 0
                    info['fourcc'] = int(cap.get(cv2.CAP_PROP_FOURCC))
                    info['codec'] = self._fourcc_to_string(info['fourcc'])
                    cap.release()
                else:
                    info['error'] = "Could not open video with OpenCV"
                    raise RuntimeError(f"1 Could not open video with OpenCV cap.isOpened() return false, cap.isOpened()={cap.isOpened()}")
            except Exception as cv_error:
                info['cv_error'] = str(cv_error)
                raise RuntimeError(f"2 Could not open video with OpenCV cap.isOpened() return false, cap.isOpened()={cap.isOpened()}")
            
            # Try to get file type using magic
            try:
                import magic
                info['mime_type'] = magic.from_file(filepath, mime=True)
                info['file_type'] = magic.from_file(filepath)
            except:
                # Fallback to file extension
                _, ext = os.path.splitext(filepath)
                info['file_type'] = f"Video file ({ext})"
                raise RuntimeError(f"3 Could not open video with OpenCV Video file ({ext})")
            
            return info
            
        except Exception as e:
            print(f"DEBUG: Could not get detailed video info: {e}")
            return {
                'path': filepath,
                'filename': os.path.basename(filepath),
                'size': os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                'error': str(e)
            }
    
    def _fourcc_to_string(self, fourcc):
        """Convert FOURCC code to string"""
        try:
            return ''.join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
        except:
            return "Unknown"        

    async def show_download_success(self, save_path, save_result):
        """Show download success with file details"""
        try:
            filename = os.path.basename(save_path)
            folder = os.path.dirname(save_path)
            file_size = save_result.get('size', 0)
            video_info = save_result.get('video_info', {})
            
            # Build detailed message
            message_parts = [
                "✅ VIDEO DOWNLOADED SUCCESSFULLY!",
                "",
                f"📁 File: {filename}",
                f"📍 Location: {folder}",
                f"📊 Size: {await self._format_bytes(file_size)}",
                ""
            ]
            
            # Add video details if available
            if 'width' in video_info and 'height' in video_info:
                message_parts.append(f"📐 Resolution: {video_info['width']}x{video_info['height']}")
            
            if 'fps' in video_info:
                message_parts.append(f"🎞️ Frame rate: {video_info['fps']:.1f} FPS")
            
            if 'duration' in video_info:
                message_parts.append(f"⏱️ Duration: {video_info['duration']:.1f} seconds")
            
            if 'codec' in video_info and video_info['codec'] != 'Unknown':
                message_parts.append(f"🔧 Codec: {video_info['codec']}")
            
            message_parts.extend([
                "",
                "The video has been saved to your computer.",
                "You can now:",
                "• Play it in any media player",
                "• Share it with others",
                "• Edit it in video software",
                "",
                f"Full path:{save_path}"
            ])
            
            message = "\n".join(message_parts)
            
            # Show dialog
            if self.app and hasattr(self.app, 'main_window') and self.app.main_window:
                #self.app.main_window.info_dialog("🎬 Download Complete", message)
                asyncio.create_task(self.show_info_dialog("🎬 Download Complete", message))
            
            # Also print to console for debugging
            print("\n" + "="*60)
            print("VIDEO DOWNLOAD CONFIRMATION")
            print("="*60)
            print(f"File: {save_path}")
            print(f"Size: {file_size} bytes ({await self._format_bytes(file_size)})")
            print(f"Exists: {os.path.exists(save_path)}")
            print(f"Readable: {os.access(save_path, os.R_OK)}")
            
            if os.path.exists(save_path):
                # Try to play a sound or show notification
                self._play_success_sound()
            
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"DEBUG: Error showing success message: {e}")
    
    def _play_success_sound(self):
        """Play a success sound if possible"""
        try:
            # Windows
            if sys.platform == "win32":
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            # macOS
            elif sys.platform == "darwin":
                import os
                os.system('afplay /System/Library/Sounds/Glass.aiff 2>/dev/null')
            # Linux
            elif sys.platform.startswith('linux'):
                import os
                os.system('canberra-gtk-play -i complete 2>/dev/null || paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null')
        except:
            pass  # Sound is optional        
                
                
    async def _get_save_location_from_user(self):
        """Get save location from user via dialog"""
        try:
            # Generate default filename
            default_name = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            print(f"_get_save_location_from_user default_name: {default_name}")
            try:
                import tkinter as tk
                from tkinter import filedialog

                # Hide the main tkinter window
                root = tk.Tk()
                root.withdraw()

                # Show save dialog
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".mp4",
                    filetypes=[
                        ("MP4 files", "*.mp4"),
                        ("All files", "*.*")
                    ],
                    initialfile=default_name,
                    title="Save Video As"
                )

                root.destroy()

                if file_path:
                    return file_path

            except ImportError:
                print("tkinter not available, using fallback")

            # Fallback: Use default downloads folder
            downloads = self._get_windows_downloads_path()
            print(f"_get_save_location_from_user downloads: {downloads}")
            return os.path.join(downloads, default_name)

        except Exception as e:
            print(f"Error getting save location: {e}")
            # Ultimate fallback
            return os.path.join(os.getcwd(), default_name)

    def _get_windows_downloads_path(self):
        """Get the Downloads folder path for Windows"""
        try:
            # Method 1: Using os.path.join with USERPROFILE
            user_profile = os.environ.get('USERPROFILE')
            print(f"_get_windows_downloads_path Getting Downloads folder path for Windows user_profile={user_profile}")
            if user_profile:
                downloads = os.path.join(user_profile, 'Downloads')
                if os.path.exists(downloads):
                    return downloads

            # Method 2: Try known paths
            known_paths = [
                os.path.join(os.path.expanduser('~'), 'Downloads'),
                os.path.join('C:\\', 'Users', os.environ.get('USERNAME', ''), 'Downloads'),
                os.path.join('C:\\', 'Users', 'Public', 'Downloads'),
            ]

            for path in known_paths:
                if os.path.exists(path):
                    return path

            # Method 3: Use Desktop as fallback
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            return desktop

        except Exception as e:
            print(f"Error getting downloads path: {e}")
            # Fallback to current directory
            return os.getcwd()

    def _update_progress(self, value):
        """Update progress display"""
        if self.progress_bar:
            self.progress_bar.value = value

        if self.progress_label:
            self.progress_label.text = f"{int(value)}%"

    async def _perform_actual_save(self, save_path):
        """Actually save the file"""
        try:
            self.update_status("Saving video...")
            self.show_progress_container()

            steps = [
                (10, "Preparing video data..."),
                (40, "Writing to file..."),
                (80, "Finalizing..."),
                (100, "Save complete!")
            ]

            for progress, message in steps:
                self._update_progress(progress)
                self.update_status(message)
                await asyncio.sleep(0.5)

            # In a real app, copy the actual video file
            # For simulation, create a test file
            print(f"_perform_actual_save calling _create_test_video_file save_path={save_path}")            
            await self._create_test_video_file(save_path)

            # Show success message with actual path
            print(f"_perform_actual_save calling _show_success_message save_path={save_path}")            
            await self._show_success_message(save_path)

            # Open the folder containing the file
            print(f"_perform_actual_save calling _open_containing_folder save_path={save_path}")            
            await self._open_containing_folder(save_path)

        except Exception as e:
            raise Exception(f"Save operation failed: {str(e)}")

    async def _create_test_video_file(self, filepath):
        """Create a test file to simulate video saving"""
        try:
            # Create a file with some content
            content = f"""This is a simulated video file.

    Created by Image2Video App
    Timestamp: {datetime.now()}
    Total images processed: {len(self.selected_images)}
    Video settings applied: Yes

    NOTE: This is a simulation file.
    In the actual application, this would be a real MP4 video.

    To test file saving functionality:
    1. This file has been saved to: {filepath}
    2. You can check that it exists
    3. You can open the containing folder

    For actual video creation, implement:
    - Real video encoding using OpenCV or FFmpeg
    - Actual MP4 file creation
    - Proper video compression
    """

            # Write the file
            print(f"_create_test_video_file calling with.open f.write filepath={filepath}")            
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"Test file created at: {filepath}")
            print(f"File size: {os.path.getsize(filepath)} bytes")

        except Exception as e:
            print(f"Error creating test file: {e}")
            raise

    async def _show_success_message(self, filepath):
        """Show success message with file details"""
        filename = os.path.basename(filepath)
        folder = os.path.dirname(filepath)

        # Create detailed message
        message = f"""
    🎬 VIDEO SAVED SUCCESSFULLY!

    📁 File: {filename}
    📍 Location: {folder}

    📊 Details:
       • File path: {filepath}
       • File exists: {'Yes' if os.path.exists(filepath) else 'No'}
       • File size: {await self._get_formatted_size(filepath)}
       • Saved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

    The file has been saved to your Windows system.
    You can now:
    1. Open the folder to view the file
    2. Play the video in any media player
    3. Share or transfer the file as needed
    """

        # For longer messages, we might need a custom dialog
        # But Toga's dialog will handle it
        #if self.app and self.app.main_window:
        #    self.app.main_window.info_dialog("✅ Download Complete", message.strip())
        if self.app and self.app.main_window:
            # self.app.main_window.error_dialog("Error", message)
            print(f"DEBUG: _show_success_message self.app.main_window={self.app.main_window}")
            await self.show_info_dialog(
                    title="✅ Download Complete!",
                    message=f"✅ Download Complete: {message.strip()}"
                )            
        else:
            print("Error download: _show_success_message Cannot show success dialog - self.app.main_window not available")

    async def _get_formatted_size(self, filepath):
        """Get formatted file size"""
        try:
            size = os.path.getsize(filepath)
            return await self._format_bytes(size)
        except:
            return "Unknown"

    async def _format_bytes(self, size):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    async def _open_containing_folder(self, filepath):
        """Open the folder containing the saved file"""
        try:
            if sys.platform == "win32":
                # For Windows, use explorer
                folder = os.path.dirname(filepath)
                os.startfile(folder)
            elif sys.platform == "darwin":
                # For macOS
                import subprocess
                subprocess.Popen(["open", os.path.dirname(filepath)])
            else:
                # For Linux
                import subprocess
                subprocess.Popen(["xdg-open", os.path.dirname(filepath)])

            print(f"Opened folder: {os.path.dirname(filepath)}")

        except Exception as e:
            print(f"Could not open folder: {e}")

    async def _create_simulated_video(self):
        """Create a simulated video for demonstration"""
        try:
            print("_create_simulated_video...")
            self.update_status("Creating video file...")

            # Get save location
            save_path = await self._get_save_location_from_user()
            print(f'_create_simulated_video saved at: {save_path}')
            if save_path:
                # Show progress
                print("_create_simulated_video calling show_progress_container ...")
                self.show_progress_container()

                # Simulate video creation steps
                creation_steps = [
                    (15, "Initializing video encoder..."),
                    (35, "Processing image frames..."),
                    (60, "Applying transitions..."),
                    (85, "Encoding video stream..."),
                    (100, "Finalizing video file..."),
                ]

                for progress, message in creation_steps:
                    print(f'_create_simulated_video progress= {progress}, message= {message}')
                    self._update_progress(progress)
                    self.update_status(message)
                    await asyncio.sleep(0.8)

                # Create the actual file
                print(f'_create_simulated_video _create_test_video_file save_path={save_path}')
                await self._create_test_video_file(save_path)

                # Show completion
                print(f'_create_simulated_video _show_success_message save_path={save_path}')
                await self._show_success_message(save_path)

                # Ask if user wants to open the folder
                print(f'_create_simulated_video self.app={self.app}')
                print(f'_create_simulated_video self.app.main_window={self.app.main_window}')
                if self.app and self.app.main_window:
                    # You could add a Yes/No dialog here
                    print(f"Video file created at: {save_path}")
            else:
                self.update_status("Video creation cancelled")

        except Exception as e:
            self.show_error(f"Video creation failed: {str(e)}")

    def update_file_list(self):
        """Update the file list display"""
        if not self.selected_images:
            self.file_list.value = "No images selected\n\nClick 'Pick Images' or 'Pick Directory' to select images"
            return

        file_text = "Selected images:\n\n"
        file_text += "\n".join([Path(p).name for p in self.selected_images[:8]])

        if len(self.selected_images) > 8:
            file_text += f"\n... and {len(self.selected_images) - 8} more"

        self.file_list.value = file_text

    def update_progress(self, value):
        """Update progress bar"""
        print(f"DEBUG: update_progress assign self.progress_bar.value to value: {value}")
        self.progress_bar.value = value
        self.progress_label.text = f"{int(value)}%"

    def show_progress_container(self):
        """Show progress bar container"""
        print(f"DEBUG: show_progress_container progress_container.style.update {self.progress_container}")
        if self.progress_container is not None:
            # In Toga, use 'none' to hide and 'pack' to show
            self.progress_container.style.update(display='pack')
        else:
            print("ERROR: progress_container is None.")

    def hide_progress_container(self):
        """Hide progress bar container"""
        print(f"DEBUG: hide_progress_container progress_container.style.update {self.progress_container}")
        if self.progress_container is not None:
            # In Toga, use 'none' to hide and 'pack' to show
            self.progress_container.style.update(display='none')
        else:
            print("ERROR: progress_container is None and cannot be hidden.")

        self.progress_bar.value = 0
        self.progress_label.text = "0%"

    def show_download_section(self):
        """Show download section"""
        print(f"DEBUG: show_download_section progress_container.style.update {self.download_section}")
        if self.download_section is not None:
            # In Toga, use 'none' to hide and 'pack' to show
            self.download_section.style.update(display='pack')
        else:
            print("ERROR: download_section is None.")

    def hide_download_section(self):
        """Hide download section"""
        print(f"DEBUG: hide_download_section progress_container.style.update  {self.download_section}")
        if self.download_section is not None:
            # In Toga, use 'none' to hide and 'pack' to show
            self.download_section.style.update(display='none')
        else:
            print("ERROR: download_section is None and cannot be hidden.")

    def update_status(self, message):
        """Update status message"""
        """Update status message with null check"""
        if self.status_label:
            print(f"DEBUG: assign self.status_label.text = message: {message}")
            self.status_label.text = message
        else:
            print(f"DEBUG: Status update (label not ready): {message}")

    def show_error(self, message):
        print(f"ERROR: {message}")
        self.update_status(f"Error: {message}")
        
        try:
            if self.app and self.app.main_window:
                print(f"DEBUG: show_error self.app.main_window={self.app.main_window}")
                asyncio.create_task(self.show_error_dialog(message))
                """
                video_view.py:2097: DeprecationWarning: App.add_background_task is deprecated. 
                Use asyncio.create_task(), or set an App.on_running() handler self.app.add_background_task(
                """
            else:
                print(f"DEBUG: Cannot show error dialog - self.app.main_window not available. message={message}")
        except Exception as e:
            print(f"Cannot show error dialog: {message}, exception: {e}")
            
            
    async def show_error_dialog(self, message):
        await self.app.main_window.dialog(
            toga.ErrorDialog("Error!", message)
        )            
            
    async def show_warn_dialog(self, message):
        await self.app.main_window.dialog(
            toga.InfoDialog("Warning", message)
        )
            
    async def show_info_dialog(self, title, message):
        await self.app.main_window.dialog(
            toga.InfoDialog(title, message)
        )

    """🔥 The One-Line Summary
        Caller	Callee	What To Do
        Async	Async	await func()
        Async	Sync	func()
        Sync	Async	schedule task (BeeWare: add_background_task)
        Sync	Sync	func()
    🧠 Mental Model (Helpful)
    Think:
        Sync functions = buttons, UI callbacks, setup
        Async functions = network, disk, long tasks
    Sync can schedule async.
    Async can await async.        
    
    ✅ RULE 1 ✅ Async ➜ Async ✔ Allowed ✔ Must use await
    async def A():
        await B()
    async def B():

    ✅ RULE 2 ✅ Async ➜ Sync ✔ Always allowed ✔ Just call it normally
    ✅ RULE 3 (Most Important for UI Apps) ❌ Sync ➜ Async (Direct Call Not Allowed) 
    ❌ WRONG  - must use asyncio.run(long_run()) or add background task self.app.add_background_task(long_run())
    def on_click(self, widget):
        self.load_data()   # load_data is async    
    ✅ Correct Ways        
        ✅ Option A: Schedule background task (BeeWare/Toga)
        def on_click(self, widget):
            self.app.add_background_task(
                lambda app: self.load_data()
            )
        ✅ Option B: Use asyncio (non-UI apps)
        def main():
            on_press=lambda w, item=item: asyncio.create_task(self.play_recent_item(item))
            on_press=lambda w, item=item: self.run_async(self.play_recent_item(item)) - safest
            asyncio.run(load_data())
        ⚠ Not allowed inside BeeWare UI threads.
    ✅ RULE 4 ✅ Sync ➜ Sync        

    """            