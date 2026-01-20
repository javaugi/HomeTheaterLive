# views/player_view.py - Updated with compatible styling
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import asyncio

class PlayerView(toga.Box):
    def __init__(self, app, media_item=None):
        super().__init__(style=Pack(direction=COLUMN, flex=1))
        self.app = app
        self.media_item = media_item or {}
        
        # Player state
        self.is_playing = False
        self.current_time = self.media_item.get('current_time', 0)
        self.duration = self.media_item.get('duration', 0)
        
        # Progress bar container width (will be set when layout is ready)
        self.progress_container_width = 300  # Default, will update

        # Create UI
        self._create_player_ui()
        
        # Schedule layout update
        asyncio.create_task(self._wait_for_layout())
        # Start playback simulation
        asyncio.create_task(self._initialize_playback())

    async def _wait_for_layout(self):
        """Wait for layout to be ready to get actual dimensions"""
        await asyncio.sleep(0.1)  # Small delay for layout
        # In a real app, you'd use actual layout events
        # For now, we'll use a fixed width or calculate based on window
        # Here we just set a default width
        #self.progress_container_width = self.progress_bg.layout.width or 300
        self.progress_container_width = self.progress_container.layout.width or 300

    def _create_player_ui(self):
        """Create player UI with pixel-based progress bar"""
        # Top bar with back button
        top_bar = toga.Box(style=Pack(
            direction=ROW,
            margin=20,
            background_color="#000000"
        ))
        
        back_btn = toga.Button(
            "← Back",
            on_press=self.go_back,
            style=Pack(color="white")
        )
        
        title_label = toga.Label(
            self.media_item.get('title', 'Now Playing'),
            style=Pack(
                flex=1,
                color="white",
                font_size=18,
                text_align="center"
            )
        )
        
        top_bar.add(back_btn, title_label)
        
        # Video area (placeholder)
        video_area = toga.Box(style=Pack(
            flex=1,
            background_color="#000000",
            direction=COLUMN,
            alignment="center"
        ))
        
        # Play button in center
        self.play_center_btn = toga.Button(
            "▶",
            on_press=self.toggle_play_pause,
            style=Pack(
                font_size=48,
                color="white",
                background_color="transparent"
            )
        )
        
        video_area.add(self.play_center_btn)
        
        # Progress bar section
        progress_section = toga.Box(style=Pack(
            direction=COLUMN,
            margin=20,
            background_color="#000000"
        ))
        
        # Time labels
        time_labels = toga.Box(style=Pack(direction=ROW, margin_bottom=10))
        self.current_time_label = toga.Label(
            "0:00",
            style=Pack(color="white", font_size=14)
        )
        self.total_time_label = toga.Label(
            self._format_time(self.duration),
            style=Pack(color="white", font_size=14, margin_left=12)
        )
        time_labels.add(self.current_time_label, self.total_time_label)
        
        # Progress bar container - fixed width
        self.progress_container = toga.Box(style=Pack(
            height=6,
            background_color="#555555",
            width=300  # Fixed width in pixels
        ))
        
        # Progress fill - starts at 0 width
        self.progress_fill = toga.Box(style=Pack(
            height=6,
            background_color="#ff3366",
            width=0  # Start at 0
        ))
        
        self.progress_container.add(self.progress_fill)
        progress_section.add(time_labels, self.progress_container)
        
        # Control buttons
        controls = toga.Box(style=Pack(
            direction=ROW,
            margin=20,
            background_color="#1a1a1a",
            alignment=CENTER
        ))
        
        # Rewind
        rewind_btn = toga.Button(
            "⏪ 10s",
            on_press=lambda w: self.seek(-10),
            style=Pack(color="white", margin=10)
        )
        
        # Play/Pause
        self.play_pause_btn = toga.Button(
            "⏸",
            on_press=self.toggle_play_pause,
            style=Pack(
                color="white",
                margin=15,
                font_size=20,
                margin_left=20,
                margin_right=20
            )
        )
        
        # Forward
        forward_btn = toga.Button(
            "⏩ 10s",
            on_press=lambda w: self.seek(10),
            style=Pack(color="white", margin=10)
        )
        
        controls.add(rewind_btn, self.play_pause_btn, forward_btn)
        
        # Add everything
        self.add(top_bar, video_area, progress_section, controls)
        
    def _format_time(self, seconds):
        """Format seconds to HH:MM:SS or MM:SS"""
        if not seconds:
            return "0:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
            
    def _calculate_progress_width(self):
        """Calculate pixel width for progress bar"""
        if self.duration == 0:
            return 0
        
        container_width = 300  # Fixed container width
        progress_pct = self.current_time / self.duration
        return int(container_width * progress_pct)
    
    async def seek(self, seconds):
        """Seek forward or backward"""
        new_time = self.current_time + seconds
        self.current_time = max(0, min(new_time, self.duration))
        
        # Update time label
        self.current_time_label.text = self._format_time(self.current_time)
        
        # Update progress bar width
        progress_width = self._calculate_progress_width()
        self.progress_fill.style.width = progress_width
    
    async def _update_progress(self):
        """Update progress while playing"""
        while True:
            await asyncio.sleep(1)
            
            if self.is_playing and self.current_time < self.duration:
                self.current_time += 1
                self.current_time_label.text = self._format_time(self.current_time)
                
                # Update progress bar
                progress_width = self._calculate_progress_width()
                self.progress_fill.style.width = progress_width
                
            elif self.current_time >= self.duration:
                self.pause()
                print("Playback finished")
                break    
    
    async def _initialize_playback(self):
        """Initialize playback"""
        print(f"Playing: {self.media_item.get('title', 'Unknown')}")
        await asyncio.sleep(1)
        self.play()
        asyncio.create_task(self._update_progress())
    
    def play(self):
        self.is_playing = True
        self.play_pause_btn.label = "⏸"
        self.play_center_btn.label = "⏸"
    
    def pause(self):
        self.is_playing = False
        self.play_pause_btn.label = "▶"
        self.play_center_btn.label = "▶"
    
    async def toggle_play_pause(self, widget):
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    async def seek(self, seconds):
        new_time = self.current_time + seconds
        self.current_time = max(0, min(new_time, self.duration))
        self.current_time_label.text = self._format_time(self.current_time)
        
        # Update progress bar width
        if self.duration > 0:
            #progress_pct = (self.current_time / self.duration) * 100
            #self.progress_fill.style.width = f"{progress_pct}%"
            # Update progress bar
            progress_width = self._calculate_progress_width()
            self.progress_fill.style.width = progress_width

    async def go_back(self, widget):
        from .home_view import HomeView
        self.app.main_window.content = HomeView(self.app)
    
    async def _update_progress(self):
        while True:
            await asyncio.sleep(1)
            if self.is_playing and self.current_time < self.duration:
                self.current_time += 1
                self.current_time_label.text = self._format_time(self.current_time)
                
                if self.duration > 0:
                    #progress_pct = (self.current_time / self.duration) * 100
                    #self.progress_fill.style.width = f"{progress_pct}%"
                    # Update progress bar
                    progress_width = self._calculate_progress_width()
                    self.progress_fill.style.width = progress_width

            elif self.current_time >= self.duration:
                self.pause()
                break