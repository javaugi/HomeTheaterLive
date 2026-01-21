import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER, LEFT, RIGHT
import asyncio
from pathlib import Path
from ..utils.icon_loader import load_icon

class VideoView:
    """Main video processing view"""

    def __init__(self, app, navigate_back_callback=None):
        self.app = app
        self.navigate_back_callback = navigate_back_callback
        from ..api import APIClient
        self.api = APIClient(app=self.app)

        # Current state
        self.selected_images = []
        self.current_job_id = None
        self.is_processing = False

        # Create UI
        self.container = None
        self.create_ui()

    def create_ui(self):
        """Create the video processing UI"""
        # Main container
        self.container = toga.Box(style=Pack(direction=COLUMN, padding=0, flex=1))

        # Header with back button
        self.create_header()

        # Content area
        self.create_content()

        # Status area
        self.create_status_area()

    def create_header(self):
        """Create the header with back button and title"""
        header_box = toga.Box(style=Pack(
            direction=ROW,
            padding=15,
            alignment=CENTER,
            background_color="#f0f0f0"
        ))

        # Back button (if we have a navigate back callback)
        if self.navigate_back_callback:
            back_btn = toga.Button(
                "← Back",
                on_press=self.go_back,
                style=Pack(padding_right=20, font_weight="bold")
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
        self.container.add(toga.Divider(style=Pack(padding=0)))

    def create_content(self):
        """Create the main content area"""
        # Scroll container for better mobile experience
        scroll_container = toga.ScrollContainer(style=Pack(flex=1))
        content_box = toga.Box(style=Pack(direction=COLUMN, padding=20, flex=1))

        # File selection section
        self.create_file_selection(content_box)

        # Settings section
        self.create_settings_section(content_box)

        # Action buttons
        self.create_action_buttons(content_box)

        scroll_container.content = content_box
        self.container.add(scroll_container)

    def create_file_selection(self, parent):
        """Create file selection section"""
        section_box = toga.Box(style=Pack(direction=COLUMN, padding=15))

        # Section title
        title_box = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
        folder_icon = load_icon("folder", size=24)
        title_label = toga.Label(
            "Select Images",
            style=Pack(font_size=18, font_weight="bold", padding_left=10)
        )
        title_box.add(folder_icon)
        title_box.add(title_label)
        section_box.add(title_box)

        # Button row
        button_row = toga.Box(style=Pack(direction=ROW, padding=10))

        # Pick Images button
        self.pick_images_btn = toga.Button(
            "📷 Pick Images",
            on_press=self.pick_images,
            style=Pack(flex=1, padding=12, background_color="#4CAF50")
        )

        # Pick Directory button
        self.pick_directory_btn = toga.Button(
            "📂 Pick Directory",
            on_press=self.pick_directory,
            style=Pack(flex=1, padding=12, margin_left=10, background_color="#2196F3")
        )

        button_row.add(self.pick_images_btn)
        button_row.add(self.pick_directory_btn)
        section_box.add(button_row)

        # Clear button
        #clear_box = toga.Box(style=Pack(direction=ROW, margin_top=10, alignment="RIGHT"))
        clear_box = toga.Box(style=Pack(direction=ROW, margin_top=10))
        self.clear_btn = toga.Button(
            "🗑️ Clear Selection",
            on_press=self.clear_selection,
            style=Pack(padding=8, background_color="#f44336")
        )
        clear_box.add(self.clear_btn)
        section_box.add(clear_box)

        # File list display
        self.file_list = toga.MultilineTextInput(
            readonly=True,
            placeholder="No images selected\n\nClick 'Pick Images' or 'Pick Directory' to select images",
            style=Pack(
                height=120,
                padding=10,
                margin_top=10,
                background_color="#fafafa",
                #border_color="#ddd",
                #border_width=1
            )
        )
        section_box.add(self.file_list)

        parent.add(section_box)
        parent.add(toga.Divider(style=Pack(padding=10)))

    def create_settings_section(self, parent):
        """Create video settings section"""
        section_box = toga.Box(style=Pack(direction=COLUMN, padding=15))

        # Section title
        title_box = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
        settings_icon = load_icon("settings", size=24)
        title_label = toga.Label(
            "Video Settings",
            style=Pack(font_size=18, font_weight="bold", padding_left=10)
        )
        title_box.add(settings_icon)
        title_box.add(title_label)
        section_box.add(title_box)

        # FPS Setting
        fps_box = toga.Box(style=Pack(direction=ROW, padding=8, alignment=CENTER))
        fps_label = toga.Label(
            "Frame Rate (FPS):",
            style=Pack(width=150, padding_right=10)
        )
        self.fps_input = toga.NumberInput(
            min=1,
            max=60,
            value=24,
            style=Pack(flex=1, padding=8)
        )
        fps_box.add(fps_label)
        fps_box.add(self.fps_input)
        section_box.add(fps_box)

        # Duration per image
        duration_box = toga.Box(style=Pack(direction=ROW, padding=8, alignment="center"))
        duration_label = toga.Label(
            "Seconds per image:",
            style=Pack(width=150, margin_right=10)
        )
        self.duration_input = toga.NumberInput(
            min=0.5,
            max=10,
            value=2.0,
            step=0.5,
            style=Pack(flex=1, padding=8)
        )
        duration_box.add(duration_label)
        duration_box.add(self.duration_input)
        section_box.add(duration_box)

        # Transition type
        transition_box = toga.Box(style=Pack(direction=ROW, padding=8, alignment=CENTER))
        transition_label = toga.Label(
            "Transition effect:",
            style=Pack(width=150, padding_right=10)
        )
        self.transition_select = toga.Selection(
            items=["None", "Fade", "Slide", "Zoom", "Crossfade"],
            style=Pack(flex=1, padding=8)
        )
        transition_box.add(transition_label)
        transition_box.add(self.transition_select)
        section_box.add(transition_box)

        # Video quality (simulated)
        quality_box = toga.Box(style=Pack(direction=ROW, padding=8, alignment="center"))
        quality_label = toga.Label(
            "Output Quality:",
            style=Pack(width=150, margin_right=10)
        )
        self.quality_select = toga.Selection(
            items=["Low (480p)", "Medium (720p)", "High (1080p)", "Ultra (4K)"],
            style=Pack(flex=1, padding=8)
        )
        quality_box.add(quality_label)
        quality_box.add(self.quality_select)
        section_box.add(quality_box)

        parent.add(section_box)
        parent.add(toga.Divider(style=Pack(padding=10)))

    def create_action_buttons(self, parent):
        """Create action buttons"""
        section_box = toga.Box(style=Pack(direction=COLUMN, padding=15))

        # Section title
        title_label = toga.Label(
            "Create Video",
            style=Pack(font_size=18, font_weight="bold", margin_bottom=15)
        )
        section_box.add(title_label)

        # Primary action button
        button_box = toga.Box(style=Pack(direction=ROW, padding=10, alignment="center"))

        self.create_video_btn = toga.Button(
            "🎬 CREATE VIDEO NOW",
            on_press=self.create_video,
            style=Pack(
                flex=1,
                padding=15,
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
            style=Pack(direction=COLUMN, padding=15, margin_top=20, display='none')
        )

        download_title = toga.Label(
            "Your Video is Ready!",
            style=Pack(font_size=16, font_weight="bold", margin_bottom=10, text_align="center")
        )
        self.download_section.add(download_title)

        download_btn_box = toga.Box(style=Pack(direction=ROW, padding=10, alignment="center"))
        self.download_btn = toga.Button(
            "📥 DOWNLOAD VIDEO",
            on_press=self.download_video,
            style=Pack(
                flex=1,
                padding=12,
                background_color="#4CAF50",
                color="white"
            )
        )
        download_btn_box.add(self.download_btn)
        self.download_section.add(download_btn_box)

        section_box.add(self.download_section)
        parent.add(section_box)

    def create_status_area(self):
        """Create status and progress area"""
        status_box = toga.Box(style=Pack(
            direction=COLUMN,
            padding=20,
            background_color="#f5f5f5"
        ))

        # Status label
        self.status_label = toga.Label(
            "Ready to create amazing videos from your images",
            style=Pack(padding=10, text_align=CENTER, font_size=14, color="#666")
        )
        status_box.add(self.status_label)

        # Progress bar container (initially hidden)
        self.progress_container = toga.Box(
            style=Pack(direction=COLUMN, padding=10, display='none')
        )

        # Progress bar
        self.progress_bar = toga.ProgressBar(
            max=100,
            value=0,
            style=Pack(padding=5, height=20)
        )
        self.progress_container.add(self.progress_bar)

        # Progress percentage label
        self.progress_label = toga.Label(
            "0%",
            style=Pack(padding=5, text_align="center", font_size=12)
        )
        self.progress_container.add(self.progress_label)

        status_box.add(self.progress_container)
        self.container.add(status_box)

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

            # Simulate delay for file picking
            await asyncio.sleep(0.5)

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
        """Pick a directory"""
        try:
            self.update_status("Opening directory picker...")

            await asyncio.sleep(0.5)

            # Simulate finding images in directory
            self.selected_images = [
                f"/Users/me/Pictures/Event/image_{i}.jpg" for i in range(1, 16)
            ]

            self.update_file_list()
            self.update_status(f"Found {len(self.selected_images)} images in directory")

        except Exception as e:
            self.show_error(f"Error picking directory: {str(e)}")

    def clear_selection(self, widget):
        """Clear selected images"""
        self.selected_images = []
        self.update_file_list()
        self.update_status("Selection cleared")
        self.hide_download_section()

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
            self.update_status("Starting video creation...")
            self.show_progress_container()
            self.update_progress(0)
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
            await self.simulate_video_processing(settings)

            # Enable buttons after processing
            self.pick_images_btn.enabled = True
            self.pick_directory_btn.enabled = True
            self.create_video_btn.enabled = True
            self.clear_btn.enabled = True

        except Exception as e:
            self.show_error(f"Error creating video: {str(e)}")
            self.is_processing = False
            self.pick_images_btn.enabled = True
            self.pick_directory_btn.enabled = True
            self.create_video_btn.enabled = True
            self.clear_btn.enabled = True

    async def simulate_video_processing(self, settings):
        """Simulate the video processing steps"""
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
            self.update_progress(progress)
            self.update_status(message)

            if progress == 100:
                # Show download button when complete
                self.show_download_section()
                self.app.main_window.info_dialog(
                    "Success!",
                    f"Video created from {len(self.selected_images)} images!\n\n"
                    f"Settings: {settings['fps']} FPS, {settings['duration_per_image']}s per image"
                )
                self.is_processing = False

    async def download_video(self, widget):
        """Download the created video"""
        try:
            self.update_status("Preparing download...")

            # Simulate download process
            steps = [
                (10, "Connecting to server..."),
                (30, "Preparing video file..."),
                (60, "Downloading..."),
                (90, "Saving to device..."),
                (100, "Download complete!")
            ]

            for progress, message in steps:
                await asyncio.sleep(0.8)
                self.update_progress(progress)
                self.update_status(message)

            # Show completion message
            self.app.main_window.info_dialog(
                "Download Complete",
                "Video saved to your device's gallery/downloads folder."
            )

            # Reset progress
            self.hide_progress_container()
            self.update_status("Ready to create another video")

        except Exception as e:
            self.show_error(f"Download error: {str(e)}")

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

    def update_status(self, message):
        """Update status message"""
        self.status_label.text = message

    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.value = value
        self.progress_label.text = f"{int(value)}%"

    def show_progress_container(self):
        """Show progress bar container"""
        self.progress_container.style.update(display='flex')

    def hide_progress_container(self):
        """Hide progress bar container"""
        self.progress_container.style.update(display='none')
        self.progress_bar.value = 0
        self.progress_label.text = "0%"

    def show_download_section(self):
        """Show download section"""
        self.download_section.style.update(display='flex')

    def hide_download_section(self):
        """Hide download section"""
        self.download_section.style.update(display='none')

    def show_error(self, message):
        """Show error message"""
        self.update_status(f"Error: {message}")
        self.app.main_window.error_dialog("Error", message)