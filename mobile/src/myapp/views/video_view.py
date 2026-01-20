import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import asyncio
import requests
import json
from datetime import datetime
from pathlib import Path
import os

from ..components.file_picker import FilePicker
from ..components.video_player import VideoPlayer
from ..components.progress_modal import ProgressModal

class Image2VideoApp(toga.Box):
    def __init__(self, formal_name=None):
        super().__init__(formal_name)
        
        # API Configuration
        #self.api_base_url = "http://192.168.1.100:8000/api/v1"  # Change to your server IP
        self.headers = {"Content-Type": "application/json"}
        
        # Current state
        self.selected_images = []
        self.current_job_id = None
        self.is_processing = False
        # Create UI
        self._create_player_ui()

    def _create_player_ui(self):
        """Build the UI"""
        #self.main_window = toga.MainWindow(title=self.formal_name)
        
        # Create main container
        self.main_box = toga.Box(style=Pack(direction=COLUMN, margin=20))
        
        # Header
        self.header_box = toga.Box(style=Pack(direction=ROW, padding=10, alignment=CENTER))
        self.icon = toga.Icon("resources/icon", system=False)
        self.icon_view = toga.ImageView(
            image=self.icon,
            style=Pack(width=50, height=50, margin_right=10)
        )
        self.title_label = toga.Label(
            "Image2Video",
            style=Pack(font_size=24, font_weight="bold")
        )
        self.header_box.add(self.icon_view)
        self.header_box.add(self.title_label)
        
        # File selection section
        self.selection_box = toga.Box(style=Pack(direction=COLUMN, margin=20))
        self.selection_label = toga.Label(
            "Select Images",
            style=Pack(font_size=18, margin_bottom=10)
        )
        
        # File picker buttons
        self.button_box = toga.Box(style=Pack(direction=ROW, margin=10))
        
        self.pick_images_btn = toga.Button(
            "📁 Pick Images",
            on_press=self.pick_images,
            style=Pack(flex=1, margin=5)
        )
        
        self.pick_directory_btn = toga.Button(
            "📂 Pick Directory",
            on_press=self.pick_directory,
            style=Pack(flex=1, margin=5)
        )
        
        self.clear_selection_btn = toga.Button(
            "🗑️ Clear",
            on_press=self.clear_selection,
            style=Pack(margin=5)
        )
        
        self.button_box.add(self.pick_images_btn)
        self.button_box.add(self.pick_directory_btn)
        self.button_box.add(self.clear_selection_btn)
        
        # Selected files list
        self.file_list = toga.MultilineTextInput(
            readonly=True,
            style=Pack(flex=1, height=100, margin=10)
        )
        
        self.selection_box.add(self.selection_label)
        self.selection_box.add(self.button_box)
        self.selection_box.add(self.file_list)
        
        # Video settings section
        self.settings_box = toga.Box(style=Pack(direction=COLUMN, margin=20))
        self.settings_label = toga.Label(
            "Video Settings",
            style=Pack(font_size=18, margin_bottom=10)
        )
        
        # FPS setting
        self.fps_box = toga.Box(style=Pack(direction=ROW, margin=5))
        self.fps_label = toga.Label("FPS:", style=Pack(width=100, margin_right=10))
        self.fps_input = toga.NumberInput(
            min_value=1,
            max_value=60,
            value=30,
            style=Pack(flex=1)
        )
        self.fps_box.add(self.fps_label)
        self.fps_box.add(self.fps_input)
        
        # Duration per image
        self.duration_box = toga.Box(style=Pack(direction=ROW, margin=5))
        self.duration_label = toga.Label("Seconds per image:", style=Pack(width=100, margin_right=10))
        self.duration_input = toga.NumberInput(
            min_value=0.5,
            max_value=10,
            value=2.0,
            step=0.5,
            style=Pack(flex=1)
        )
        self.duration_box.add(self.duration_label)
        self.duration_box.add(self.duration_input)
        
        # Transition type
        self.transition_box = toga.Box(style=Pack(direction=ROW, margin=5))
        self.transition_label = toga.Label("Transition:", style=Pack(width=100, margin_right=10))
        self.transition_select = toga.Selection(
            items=["none", "fade", "slide"],
            style=Pack(flex=1)
        )
        self.transition_box.add(self.transition_label)
        self.transition_box.add(self.transition_select)
        
        self.settings_box.add(self.settings_label)
        self.settings_box.add(self.fps_box)
        self.settings_box.add(self.duration_box)
        self.settings_box.add(self.transition_box)
        
        # Action buttons
        self.action_box = toga.Box(style=Pack(direction=ROW, margin=20, alignment=CENTER))
        
        self.create_video_btn = toga.Button(
            "🎬 Create Video",
            on_press=self.create_video,
            style=Pack(margin=10, flex=1)
        )
        
        self.download_btn = toga.Button(
            "📥 Download Latest",
            on_press=self.download_latest_video,
            style=Pack(margin=10, flex=1),
            enabled=False
        )
        
        self.action_box.add(self.create_video_btn)
        self.action_box.add(self.download_btn)
        
        # Status display
        self.status_label = toga.Label(
            "Ready",
            style=Pack(margin=10, text_align=CENTER)
        )
        
        # Progress bar
        self.progress_bar = toga.ProgressBar(
            max=100,
            value=0,
            style=Pack(margin=10, width=300)
        )
        
        # Assemble main box
        self.main_box.add(self.header_box)
        self.main_box.add(toga.Divider(style=Pack(margin=10)))
        self.main_box.add(self.selection_box)
        self.main_box.add(self.settings_box)
        self.main_box.add(self.action_box)
        self.main_box.add(self.status_label)
        self.main_box.add(self.progress_bar)
        
        # Add video player (initially hidden)
        #self.video_player = VideoPlayer(self.main_window)
        self.video_player = VideoPlayer(self.main_box)

        # Set content
        #self.main_window.content = main_box
        #self.main_window.show()

        # Add everything
        self.add(self.main_box, self.video_player)

        # Start polling for video list
        #asyncio.create_task(self.poll_video_list())
    
    async def pick_images(self, widget):
        """Pick multiple image files"""
        try:
            file_paths = await FilePicker.pick_images()
            if file_paths:
                self.selected_images = file_paths
                self.update_file_list()
                self.status_label.text = f"Selected {len(file_paths)} images"
        except Exception as e:
            self.show_error(f"Error picking images: {str(e)}")
    
    async def pick_directory(self, widget):
        """Pick a directory"""
        try:
            directory = await FilePicker.pick_directory()
            if directory:
                # Find all image files in directory
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}
                image_files = []
                
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if Path(file).suffix.lower() in image_extensions:
                            image_files.append(os.path.join(root, file))
                
                if image_files:
                    self.selected_images = image_files
                    self.update_file_list()
                    self.status_label.text = f"Found {len(image_files)} images"
                else:
                    self.show_error("No images found in selected directory")
        except Exception as e:
            self.show_error(f"Error picking directory: {str(e)}")
    
    def update_file_list(self):
        """Update the file list display"""
        file_text = "\n".join([Path(p).name for p in self.selected_images[:10]])
        if len(self.selected_images) > 10:
            file_text += f"\n... and {len(self.selected_images) - 10} more"
        self.file_list.value = file_text
    
    def clear_selection(self, widget):
        """Clear selected images"""
        self.selected_images = []
        self.file_list.value = ""
        self.status_label.text = "Selection cleared"
    
    async def create_video(self, widget):
        """Create video from selected images"""
        if not self.selected_images:
            self.show_error("Please select images first")
            return
        
        if self.is_processing:
            self.show_error("Already processing a video")
            return
        
        try:
            self.is_processing = True
            self.status_label.text = "Creating video..."
            self.progress_bar.value = 0
            
            # Prepare settings
            settings = {
                "fps": int(self.fps_input.value),
                "duration_per_image": float(self.duration_input.value),
                "transition_type": self.transition_select.value
            }
            
            # For mobile, we'll upload the files
            if len(self.selected_images) <= 50:  # Limit for upload
                # Upload files
                files = []
                for i, image_path in enumerate(self.selected_images):
                    files.append(('files', (Path(image_path).name, open(image_path, 'rb'), 'image/jpeg')))
                
                # Update progress
                self.progress_bar.value = 30
                
                # Send request
                response = requests.post(
                    f"{self.api_base_url}/process/upload",
                    files=files,
                    data={"settings": json.dumps(settings)},
                    timeout=30
                )
                
                # Close all files
                for _, (_, file_obj, _) in files:
                    file_obj.close()
                
            else:
                # For large number of files, use directory processing
                # This requires the files to be accessible from the server
                self.show_error("Too many files for upload. Please use directory picker instead.")
                return
            
            if response.status_code == 200:
                data = response.json()
                self.current_job_id = data['job_id']
                self.status_label.text = data['message']
                
                # Start polling for completion
                asyncio.create_task(self.poll_job_status(self.current_job_id))
                
            else:
                self.show_error(f"Failed to create video: {response.text}")
                
        except Exception as e:
            self.show_error(f"Error creating video: {str(e)}")
        finally:
            self.is_processing = False
    
    async def poll_job_status(self, job_id):
        """Poll for job completion"""
        while True:
            try:
                response = requests.get(f"{self.api_base_url}/status/{job_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Update progress
                    self.progress_bar.value = data['progress']
                    self.status_label.text = data['message']
                    
                    if data['status'] == 'completed':
                        # Video is ready
                        self.status_label.text = "Video created successfully!"
                        self.download_btn.enabled = True
                        
                        # Show video player
                        video_url = f"{self.api_base_url}/video/{job_id}.mp4"
                        self.video_player.show(video_url)
                        break
                        
                    elif data['status'] == 'failed':
                        self.show_error(f"Video creation failed: {data.get('error', 'Unknown error')}")
                        break
                
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                self.show_error(f"Error checking status: {str(e)}")
                break
    
    async def download_latest_video(self, widget):
        """Download the latest video"""
        try:
            # Get list of videos
            response = requests.get(f"{self.api_base_url}/videos")
            
            if response.status_code == 200:
                videos = response.json()['videos']
                if videos:
                    latest = max(videos, key=lambda x: x['created'])
                    
                    # Download the video
                    video_response = requests.get(latest['url'], stream=True)
                    
                    # Save to device
                    downloads_dir = Path.home() / "Downloads"
                    downloads_dir.mkdir(exist_ok=True)
                    
                    filename = latest['filename']
                    filepath = downloads_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        for chunk in video_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    self.status_label.text = f"Downloaded: {filename}"
                    
                    # Show success message
                    self.main_window.info_dialog(
                        "Download Complete",
                        f"Video saved to: {filepath}"
                    )
                else:
                    self.show_error("No videos available")
            else:
                self.show_error("Failed to get video list")
                
        except Exception as e:
            self.show_error(f"Download error: {str(e)}")
    
    async def poll_video_list(self):
        """Periodically check for available videos"""
        while True:
            try:
                response = requests.get(f"{self.api_base_url}/videos")
                if response.status_code == 200:
                    videos = response.json()['videos']
                    self.download_btn.enabled = len(videos) > 0
            except:
                pass
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    def show_error(self, message):
        """Show error message"""
        self.status_label.text = f"Error: {message}"
        self.main_window.error_dialog("Error", message)
    
    def show_info(self, title, message):
        """Show info message"""
        self.main_window.info_dialog(title, message)

def main():
    return Image2VideoApp("Image2Video")# -*- coding: utf-8 -*-

