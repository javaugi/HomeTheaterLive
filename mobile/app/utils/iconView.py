import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
from pathlib import Path

class IconView(toga.Box):
    def __init__(self, icon_name=None, size=50, **kwargs):
        #super().__init__(style=Pack(width=size, height=size, **kwargs))
        #super().__init__(style=Pack(direction=COLUMN, flex=1, **kwargs))

        self.icon_name = icon_name
        self.size = size

        # Try to load different icon formats
        self.icon = self._load_icon()
        if self.icon:
            self.add(self.icon)
        else:
            # Fallback to text icon
            self._create_fallback()

    def _load_icon(self):
        """Try to load icon from various sources"""
        if not self.icon_name:
            return None

        icon_paths = [
            # Check in resources directory
            Path(__file__).parent / "resources" / f"{self.icon_name}.png",
            Path(__file__).parent / "resources" / f"{self.icon_name}.jpg",
            Path(__file__).parent / "resources" / "icons" / f"{self.icon_name}.png",
            # Check in current directory
            Path.cwd() / f"{self.icon_name}.png",
        ]

        for path in icon_paths:
            if path.exists():
                try:
                    image = toga.Image(str(path))
                    return toga.ImageView(
                        image=image,
                        style=Pack(width=self.size, height=self.size)
                    )
                except:
                    continue

        return None

    def _create_fallback(self):
        """Create fallback icon using text"""
        # Map common icon names to emojis
        icon_map = {
            'video': '🎬',
            'camera': '📷',
            'folder': '📁',
            'image': '🖼️',
            'settings': '⚙️',
            'play': '▶️',
            'download': '📥',
            'upload': '📤',
            'delete': '🗑️',
            'default': '📱'
        }

        emoji = icon_map.get(self.icon_name, icon_map['default'])
        self.add(toga.Label(
            emoji,
            style=Pack(font_size=self.size // 2)
        ))
