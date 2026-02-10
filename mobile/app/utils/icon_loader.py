import os
from pathlib import Path
import toga
from toga.style import Pack


def get_icon_path(icon_name):
    """
    Get the absolute path to an icon file.

    Args:
        icon_name: Name of the icon file (without extension)

    Returns:
        Path object if found, None otherwise
    """
    # Get the project root directory
    current_dir = Path(__file__).parent.parent

    # Check in icons directory
    icon_dir = current_dir / "icons"

    # Try different extensions
    extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg']

    for ext in extensions:
        icon_path = icon_dir / f"{icon_name}{ext}"
        if icon_path.exists():
            return icon_path

    return None


def load_icon(icon_name, size=40, fallback_emoji="📱"):
    """
    Load an icon from the icons directory with fallback to emoji.

    Args:
        icon_name: Name of the icon file (without extension)
        size: Desired size of the icon
        fallback_emoji: Emoji to use if icon file doesn't exist

    Returns:
        Toga widget (ImageView or Label)
    """
    icon_path = get_icon_path(icon_name)

    if icon_path:
        try:
            # Load the image
            image = toga.Image(str(icon_path))
            return toga.ImageView(
                image=image,
                style=Pack(width=size, height=size)
            )
        except Exception as e:
            print(f"Failed to load icon {icon_name} from {icon_path}: {e}")
            # Fall through to emoji

    # Use emoji as fallback
    emoji_map = {
        'video': '🎬',
        'camera': '📷',
        'folder': '📁',
        'image': '🖼️',
        'settings': '⚙️',
        'play': '▶️',
        'download': '📥',
        'upload': '📤',
        'delete': '🗑️',
        'back': '←',
        'default': fallback_emoji
    }

    emoji = emoji_map.get(icon_name, emoji_map['default'])
    return toga.Label(
        emoji,
        style=Pack(
            font_size=size // 2 if size > 30 else size,
            width=size,
            height=size,
            text_align="center"
        )
    )


def create_icon_button(icon_name, text, on_press, size=30):
    """
    Create a button with an icon.

    Args:
        icon_name: Name of the icon
        text: Button text
        on_press: Button press handler
        size: Icon size

    Returns:
        Toga Box containing icon and label
    """
    box = toga.Box(style=Pack(direction='column', alignment='center'))

    # Add icon
    icon = load_icon(icon_name, size=size)
    box.add(icon)

    # Add label
    label = toga.Label(
        text,
        style=Pack(text_align='center', margin_top=5)
    )
    box.add(label)

    return box