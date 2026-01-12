# views/home.py
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER

class HomeView(toga.Box):
    def __init__(self, app):
        # Base style for the container
        super().__init__(style=Pack(direction=COLUMN, padding=30))
        self.app = app
        
        # Import here to avoid circular imports
        from ..api import APIClient
        from ..storage import SecureStorage
        
        self.api = APIClient()
        self.storage = SecureStorage(self.app)
        
        # Define spacing styles
        header_style = Pack(font_size=28, padding_bottom=30, text_align=CENTER, font_weight="bold")
        button_style = Pack(padding=15, width=250)
        spaced_button_style = Pack(padding=15, width=250, padding_bottom=10)
        
        # Create UI elements
        self.welcome_label = toga.Label(
            f"Welcome to MyHomeTheater!",
            style=header_style
        )
        
        self.user_info_label = toga.Label(
            "You are logged in",
            style=Pack(padding_bottom=30, text_align=CENTER)
        )
        
        # Create buttons with spacing
        self.movies_btn = toga.Button(
            "🎬 Browse Movies",
            on_press=self.show_movies,
            style=spaced_button_style
        )
        
        self.tv_btn = toga.Button(
            "📺 TV Shows",
            on_press=self.show_tv_shows,
            style=spaced_button_style
        )
        
        self.playlists_btn = toga.Button(
            "📋 My Playlists",
            on_press=self.show_playlists,
            style=spaced_button_style
        )
        
        self.settings_btn = toga.Button(
            "⚙️ Settings",
            on_press=self.show_settings,
            style=spaced_button_style
        )
        
        self.logout_btn = toga.Button(
            "🚪 Logout",
            on_press=self.logout,
            style=Pack(
                padding=15,
                width=250,
                background_color="#dc3545",
                color="white",
                padding_top=20
            )
        )
        
        # Add all elements to the box
        self.add(
            self.welcome_label,
            self.user_info_label,
            self.movies_btn,
            self.tv_btn,
            self.playlists_btn,
            self.settings_btn,
            self.logout_btn
        )
    
    async def show_movies(self, widget):
        print("Browse Movies clicked")
        # Implement movies view
    
    async def show_tv_shows(self, widget):
        print("TV Shows clicked")
        # Implement TV shows view
    
    async def show_playlists(self, widget):
        print("My Playlists clicked")
        # Implement playlists view
    
    async def show_settings(self, widget):
        print("Settings clicked")
        # Implement settings view
    
    async def logout(self, widget):
        print("Logging out...")
        self.storage.clear()
        
        # Switch back to login view
        from .login import LoginView
        self.app.main_window.content = LoginView(self.app)