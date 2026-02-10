import toga
from toga.style import Pack
import requests
import tempfile
import os

class VideoPlayer:
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.video_window = None
        self.current_video_path = None
    
    def show(self, video_url):
        """Show video player with the given URL"""
        if self.video_window is None:
            self.create_window()
        
        # Download video to temp file
        self.download_video(video_url)
        
        if self.current_video_path:
            # Update video source
            # Note: Toga doesn't have a native video player yet
            # This would need platform-specific implementation
            self.show_video_info()
    
    def create_window(self):
        """Create video player window"""
        self.video_window = toga.Window(title="Video Player")
        
        content = toga.Box(style=Pack(direction='column', margin=10))
        
        # Video placeholder (would be replaced with actual video player)
        self.video_label = toga.Label(
            "Video would play here",
            style=Pack(margin=20, text_align='center')
        )
        
        # Control buttons
        button_box = toga.Box(style=Pack(direction='row', margin=10))
        
        close_btn = toga.Button(
            "Close",
            on_press=self.close,
            style=Pack(flex=1, margin=5)
        )
        
        save_btn = toga.Button(
            "Save to Device",
            on_press=self.save_to_device,
            style=Pack(flex=1, margin=5)
        )
        
        button_box.add(close_btn)
        button_box.add(save_btn)
        
        content.add(self.video_label)
        content.add(button_box)
        
        self.video_window.content = content
        self.parent_window.app.add_window(self.video_window)
    
    def download_video(self, video_url):
        """Download video to temporary file"""
        try:
            response = requests.get(video_url, stream=True)
            
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                self.current_video_path = f.name
            
            self.video_label.text = f"Video downloaded: {os.path.basename(self.current_video_path)}"
            
        except Exception as e:
            self.video_label.text = f"Error downloading video: {str(e)}"
    
    def show_video_info(self):
        """Show video info (placeholder for actual video playback)"""
        if self.current_video_path:
            file_size = os.path.getsize(self.current_video_path) / (1024 * 1024)  # MB
            self.video_label.text = f"Video ready!\nSize: {file_size:.2f} MB\n\n(Actual playback requires platform-specific implementation)"
    
    def save_to_device(self, widget):
        """Save video to device storage"""
        if self.current_video_path:
            # This would need platform-specific implementation
            # For iOS, use UIDocumentPickerViewController
            # For Android, use Intent.ACTION_CREATE_DOCUMENT
            self.parent_window.info_dialog(
                "Save Video",
                "Video save functionality requires platform-specific implementation"
            )
    
    def close(self, widget):
        """Close video player"""
        if self.video_window:
            self.video_window.close()
        
        # Clean up temp file
        if self.current_video_path and os.path.exists(self.current_video_path):
            try:
                os.unlink(self.current_video_path)
            except:
                pass
            self.current_video_path = None# -*- coding: utf-8 -*-

