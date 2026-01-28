# views/search_view.py
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import asyncio

class SearchView(toga.Box):
    def __init__(self, app):
        super().__init__(style=Pack(direction=COLUMN, flex=1))
        self.app = app
        
        # Initialize API
        from ..api import APIClient
        self.api = APIClient(app=self.app)
        
        self._create_search_ui()
    
    def _create_search_ui(self):
        # Search header
        header = toga.Box(style=Pack(direction=ROW, margin=20, background_color="#1a1a2e"))
        
        back_btn = toga.Button(
            "←",
            on_press=lambda w: self._go_back(),
            style=Pack(color="white", font_size=20)
        )
        
        self.search_input = toga.TextInput(
            placeholder="Search movies, shows, actors...",
            style=Pack(flex=1, margin_left=15, margin=10)
        )
        
        search_btn = toga.Button(
            "🔍",
            on_press=lambda w: self._perform_search(),
            style=Pack(color="white", margin_left=10, font_size=20)
        )
        
        header.add(back_btn, self.search_input, search_btn)
        self.add(header)
        
        # Results container
        self.results_container = toga.ScrollContainer(style=Pack(flex=1))
        self.results_content = toga.Box(style=Pack(direction=COLUMN, margin=20))
        self.results_container.content = self.results_content
        self.add(self.results_container)
    
    async def _perform_search(self):
        query = self.search_input.value.strip()
        if not query:
            return
        
        # Clear previous results
        self.results_content.children.clear()
        
        # Show loading
        loading = toga.Label("Searching...", style=Pack(margin=20, text_align="center"))
        self.results_content.add(loading)
        
        # Perform search
        results = await self.api.search_content(query)
        
        # Clear loading
        self.results_content.children.clear()
        
        if results:
            for item in results:
                result_item = self._create_result_item(item)
                self.results_content.add(result_item)
        else:
            no_results = toga.Label(
                "No results found",
                style=Pack(margin=20, text_align="center", color="#8a8d93")
            )
            self.results_content.add(no_results)
    
    def _create_result_item(self, item):
        # Create result item UI
        pass
    
    def _go_back(self):
        from .home_view import HomeView
        self.app.main_window.content = HomeView(self.app)