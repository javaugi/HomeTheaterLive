#frontend/src/myapp/views/home_view.py
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
from datetime import datetime
import asyncio

class HomeView(toga.Box):
    def __init__(self, app):
        super().__init__(style=Pack(direction=COLUMN, flex=1))
        self.app = app
        
        # Initialize services
        from ..api import APIClient
        from ..storage import SecureStorage
        self.api = APIClient(app=self.app)
        self.storage = SecureStorage(self.app)
        
        self.access_token = self.storage.access_token()        
        print(f"#frontend/src/myapp/home_view.py HomeView token: {self.access_token}")
        
        # Create UI components
        self._create_header()
        self._create_quick_actions()
        self._create_content_sections()
        self._create_bottom_nav()
        
        # Load data
        asyncio.create_task(self._load_initial_data())
    
    def _create_header(self):
        """Create the header section with user info and search"""
        header_box = toga.Box(style=Pack(
            direction=ROW, 
            margin=(20, 25, 15, 25),
            background_color="#1a1a2e"
        ))
        
        # User info
        user_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self.greeting_label = toga.Label(
            "Good morning!",
            style=Pack(color="white", font_size=16)
        )
        self.username_label = toga.Label(
            "Guest",
            style=Pack(color="#8a8d93", font_size=14)
        )
        user_box.add(self.greeting_label, self.username_label)
        
        # Icons (using text emojis for cross-platform)
        icons_box = toga.Box(style=Pack(direction=ROW))

        # Search button
        search_btn = toga.Button(
            "🔍",
            on_press=self.show_search,
            style=Pack(
                width=40, 
                height=40,
                background_color="#2d3047",
                color="white",
                margin=10
            )
        )
        
        # Notifications
        notif_btn = toga.Button(
            "🔔",
            on_press=self.show_notifications,
            style=Pack(
                width=40,
                height=40,
                background_color="#2d3047",
                color="white",
                margin=10,
                margin_left=10
            )
        )
        
        icons_box.add(search_btn, notif_btn)
        header_box.add(user_box, search_btn, notif_btn)
        self.add(header_box)
    
    def _create_quick_actions(self):
        """Create quick action buttons"""
        actions_box = toga.Box(style=Pack(
            direction=ROW,
            margin=(0, 25, 20, 25),
            background_color="#1a1a2e"
        ))
        
        actions = [
            {"icon": "▶️", "label": "Play", "action": self.play_content},
            {"icon": "🎬", "label": "Movies", "action": self.show_movies},
            {"icon": "📺", "label": "TV Shows", "action": self.show_tv_shows},
            {"icon": "📱", "label": "Devices", "action": self.manage_devices},
        ]
        
        for action in actions:
            action_btn = self._create_action_button(
                action["icon"], 
                action["label"], 
                action["action"]
            )
            actions_box.add(action_btn)
        
        self.add(actions_box)
    
    def _create_action_button(self, icon, label, on_press):
        """Helper to create an action button"""
        btn_box = toga.Box(style=Pack(direction=COLUMN, margin=(0, 10, 0, 0)))
        
        icon_btn = toga.Button(
            icon,
            on_press=on_press,
            style=Pack(
                width=60,
                height=60,
                background_color="#2d3047",
                color="white",
                font_size=24,
                margin=15,
                #border_radius=30
            )
        )
        """Summary of Supported Pack Properties
        As of 2026, the Pack engine primarily supports layout and basic visual properties: 
        Layout: width, height, flex, padding, margin, gap.
        Visuals: background_color, color, visibility.
        Text: font_family, font_size, font_style, text_align. 
        """
        
        label_widget = toga.Label(
            label,
            style=Pack(color="white", font_size=12, text_align=CENTER, margin_top=5)
        )
        
        btn_box.add(icon_btn, label_widget)
        return btn_box
    
    def _create_content_sections(self):
        """Create scrollable content sections"""
        # Create a scroll container
        scroll_container = toga.ScrollContainer(style=Pack(flex=1))
        content_box = toga.Box(style=Pack(direction=COLUMN))
        
        # Continue Watching section
        self._create_section(
            content_box, 
            "Continue Watching", 
            "See All",
            self.show_continue_watching,
            self.continue_watching_section
        )
        
        # Recently Added section
        self._create_section(
            content_box,
            "Recently Added",
            "Browse All",
            self.show_recently_added,
            self.recently_added_section
        )
        
        # Recommended For You
        self._create_section(
            content_box,
            "Recommended For You",
            "Refresh",
            self.refresh_recommendations,
            self.recommendations_section
        )
        
        # Your Playlists
        self._create_section(
            content_box,
            "Your Playlists",
            "Manage",
            self.manage_playlists,
            self.playlists_section
        )
        
        scroll_container.content = content_box
        self.add(scroll_container)
    
    def _create_section(self, parent, title, action_text, action_callback, content_container):
        """Helper to create a content section"""
        section_box = toga.Box(style=Pack(direction=COLUMN, margin=20))
        
        # Section header
        header_box = toga.Box(style=Pack(direction=ROW, margin_bottom=15))
        title_label = toga.Label(
            title,
            style=Pack(flex=1, font_size=18, font_weight="bold", color="white")
        )
        action_btn = toga.Button(
            action_text,
            on_press=action_callback,
            style=Pack(color="#4dabf7", font_size=14)
        )
        header_box.add(title_label, action_btn)
        
        # Content container (will be populated later)
        content_container = toga.Box(style=Pack(direction=ROW))
        
        # Add placeholder items
        for i in range(3):
            placeholder = self._create_content_card(f"Item {i+1}")
            content_container.add(placeholder)
        
        section_box.add(header_box, content_container)
        parent.add(section_box)
    
    def _create_content_card(self, title):
        """Create a content card (movie/show poster)"""
        card = toga.Box(style=Pack(
            direction=COLUMN,
            width=120,
            margin_right=15,
            background_color="#2d3047",
            #border_radius=10
        ))
        
        # Poster placeholder
        poster = toga.Box(style=Pack(
            width=120,
            height=180,
            background_color="#3a3e5c",
            #border_radius=(10, 10, 0, 0)
        ))
        
        # Title
        title_label = toga.Label(
            title,
            style=Pack(
                padding=10,
                color="white",
                font_size=12
            )
        )
        
        card.add(poster, title_label)
        return card
    
    def _create_bottom_nav(self):
        """Create bottom navigation bar"""
        nav_box = toga.Box(style=Pack(
            direction=ROW,
            margin=(10, 25, 20, 25),
            background_color="#1a1a2e"
        ))
        
        nav_items = [
            {"icon": "🏠", "label": "Home", "active": True},
            {"icon": "🎬", "label": "Library", "active": True},
            {"icon": "🔍", "label": "Search", "active": True},
            {"icon": "👤", "label": "Profile", "active": True},
            {"icon": "🔒", "label": "Logout", "active": True},
        ]
        
        for item in nav_items:
            nav_btn = self._create_nav_item(item["icon"], item["label"], item.get("active", False))
            nav_box.add(nav_btn)
        
        self.add(nav_box)
    
    def _create_nav_item(self, icon, label, active=False):
        """Create a bottom navigation item"""
        nav_item = toga.Box(style=Pack(direction=COLUMN, flex=1, margin=(0, 5)))
        
        icon_color = "#4dabf7" if active else "#8a8d93"
        label_color = "#4dabf7" if active else "#8a8d93"
        
        # Inside your loop where you create buttons:
        target_label = label.lower()
        async def on_nav_press(widget):
            await self._handle_nav_click(target_label)

        icon_btn = toga.Button(
            icon,
            on_press=on_nav_press,
            #on_press=lambda w: self._handle_nav_click(label.lower()),
            style=Pack(
                background_color="transparent",
                color=icon_color,
                font_size=20
            )
        )
        
        label_widget = toga.Label(
            label,
            style=Pack(
                color=label_color,
                font_size=10,
                text_align=CENTER,
                margin_top=2
            )
        )
        
        nav_item.add(icon_btn, label_widget)
        return nav_item
    
    # ====== DATA LOADING METHODS ======
    
    async def _load_initial_data(self):
        """Load initial data from API"""
        if not self.access_token:
            print("WARNING: #frontend/src/myapp/home_view.py _load_initial_data NO self.access_token !")
            return
        
        try:
            print(f"#frontend/src/myapp/home_view.py _load_initial_data HomeView token: {self.access_token}")
            # Load user profile
            user_data = await self.api.get_user_profile()
            print(f"#frontend/src/myapp/home_view.py _load_initial_data get_user_profile: {user_data}")
            if user_data:
                self.username_label.text = user_data.get("username", "Guest")
                self._update_greeting()
            
            # Load continue watching
            continue_data = await self.api.get_continue_watching()
            print(f"#frontend/src/myapp/home_view.py _load_initial_data get_continue_watching: {continue_data}")
            if continue_data:
                self._populate_continue_watching(continue_data)
            
            # Load recommendations
            recommendations = await self.api.get_recommendations()
            print(f"#frontend/src/myapp/home_view.py _load_initial_data get_recommendations: {recommendations}")
            if recommendations:
                self._populate_recommendations(recommendations)
                
        except Exception as e:
            print(f"Error loading home data: {e}")
    
    def _update_greeting(self):
        """Update greeting based on time of day"""
        hour = datetime.now().hour
        if hour < 12:
            self.greeting_label.text = "Good morning!"
        elif hour < 18:
            self.greeting_label.text = "Good afternoon!"
        else:
            self.greeting_label.text = "Good evening!"
    
    def _populate_continue_watching(self, items):
        """Populate continue watching section"""
        # Implementation depends on your API response structure
        pass
    
    def _populate_recommendations(self, items):
        """Populate recommendations section"""
        # Implementation depends on your API response structure
        pass
    
    # ====== EVENT HANDLERS ======
    
    async def play_content(self, widget):
        """Handle play button press"""
        from .player_view import PlayerView
        # You might want to pass actual media data here
        media_item = {
            'title': 'Demo Movie',
            'duration': 3600,  # 1 hour
            'current_time': 0
        }
        self.app.main_window.content = PlayerView(self.app, media_item)

    async def show_movies(self, widget):
        """Show movies library"""
        from .movies_view import MoviesView
        self.app.main_window.content = MoviesView(self.app)
    
    async def show_tv_shows(self, widget):
        """Show TV shows library"""
        print("Show TV Shows")
        #from .tv_shows_view import TVShowsView
        #self.app.main_window.content = TVShowsView(self.app)
    
    async def manage_devices(self, widget):
        """Manage connected devices"""
        print("Manage Devices")
        #from .devices_view import DevicesView
        #self.app.main_window.content = DevicesView(self.app)
    
    async def show_search(self, widget):
        """Show search view"""
        from .search_view import SearchView
        self.app.main_window.content = SearchView(self.app)
    
    async def show_notifications(self, widget):
        """Show notifications"""
        print("Show Notifications")
        #from .notifications_view import NotificationsView
        #self.app.main_window.content = NotificationsView(self.app)
    
    async def show_continue_watching(self, widget):
        """Show all continue watching items"""
        print("Show all continue watching")

    async def continue_watching_section(self, widget):
        """Populate continue watching section"""
        print("Populating continue watching section")   
    
    async def show_recently_added(self, widget):
        """Show all recently added items"""
        print("Show all recently added")

    async def recently_added_section(self, widget):
        """Populate recently added section"""
        print("Populating recently added section")  
    
    async def refresh_recommendations(self, widget):
        """Refresh recommendations"""
        print("Refreshing recommendations...")

    async def recommendations_section(self, widget):
        """Populate recommendations section"""
        print("Populating recommendations section") 
    
    async def manage_playlists(self, widget):
        """Manage playlists"""
        print("Managing playlists")

    async def playlists_section(self, widget):
        """Populate playlists section"""
        print("Populating playlists section")
    
    async def _handle_nav_click(self, destination):
        """Handle bottom navigation clicks"""
        print(f"Navigate to: {destination}")
        if destination == "logout":
                await self.logout(None)        
    
    async def logout(self, widget):
        """Handle logout"""
        self.storage.clear()
        from .login import LoginView
        self.app.main_window.content = LoginView(self.app)



