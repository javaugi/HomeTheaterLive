# views/movies_view.py
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

class MoviesView(toga.Box):
    def __init__(self, app):
        super().__init__(style=Pack(direction=COLUMN, flex=1))
        self.app = app
        
        # Create movies grid
        self._create_header()
        self._create_movies_grid()
    
    def _create_header(self):
        header = toga.Box(style=Pack(direction=ROW, margin=20, background_color="#1a1a2e"))
        
        back_btn = toga.Button(
            "← Back",
            on_press=lambda w: self._go_back(),
            style=Pack(color="white")
        )
        
        title = toga.Label(
            "Movies Library",
            style=Pack(flex=1, color="white", font_size=24, text_align="center")
        )
        
        header.add(back_btn, title)
        self.add(header)
    
    def _create_movies_grid(self):
        # Create scrollable grid of movies
        scroll = toga.ScrollContainer(style=Pack(flex=1))
        grid = toga.Box(style=Pack(direction=COLUMN, margin=20))
        
        # Add movie cards (would be populated from API)
        for i in range(20):
            movie_card = self._create_movie_card(f"Movie {i+1}")
            grid.add(movie_card)
        
        scroll.content = grid
        self.add(scroll)
    
    def _create_movie_card(self, title):
        card = toga.Box(style=Pack(
            direction=ROW,
            margin=10,
            background_color="#2d3047",
            margin_bottom=10, 
            # border_radius=10
        ))
        
        # Poster placeholder
        poster = toga.Box(style=Pack(
            width=80,
            height=120,
            background_color="#3a3e5c",
            #border_radius=5
        ))
        
        # Info
        info_box = toga.Box(style=Pack(direction=COLUMN, margin_left=15, flex=1))
        
        title_label = toga.Label(
            title,
            style=Pack(color="white", font_size=16, font_weight="bold")
        )
        
        details = toga.Label(
            "2024 • 2h 15m • Action",
            style=Pack(color="#8a8d93", font_size=12, margin_top=5)
        )
        
        play_btn = toga.Button(
            "Play",
            on_press=lambda w: self._play_movie(title),
            style=Pack(
                background_color="#ff3366",
                color="white",
                margin=5,
                width=80,
                margin_top=10
            )
        )
        
        info_box.add(title_label, details, play_btn)
        card.add(poster, info_box)
        
        return card
    
    def _play_movie(self, title):
        from .player_view import PlayerView
        media_item = {
            'title': title,
            'duration': 8100,  # 2h 15m in seconds
            'current_time': 0
        }
        self.app.main_window.content = PlayerView(self.app, media_item)
    
    def _go_back(self):
        from .home_view import HomeView
        self.app.main_window.content = HomeView(self.app)