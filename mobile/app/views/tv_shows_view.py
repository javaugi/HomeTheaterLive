import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import asyncio

class TVShowsView(toga.Box):
    def __init__(self, app, media_item=None):
        super().__init__(style=Pack(direction=COLUMN, flex=1))
        self.app = app
        self.media_item = media_item or {}
        
        # Create UI
        self._create_tv_shows_ui()
        
        # Schedule layout update
        asyncio.create_task(self._wait_for_layout())
        # Start playback simulation

    async def _wait_for_layout(self):
        """Wait for layout to be ready to get actual dimensions"""
        await asyncio.sleep(0.1)  # Small delay for layout        

    async def _create_tv_shows_ui(self):
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