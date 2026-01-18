#frontend/src/myapp/views/login.py
import toga
from toga.style import Pack
from toga.style.pack import COLUMN
from myapp.api import APIClient

class LoginView(toga.Box):
    def __init__(self, app):
        super().__init__(style=Pack(direction=COLUMN, padding=20))
        self.app = app
        #self.api = APIClient()
        # Create API client with app instance
        self.api = APIClient(app=self.app)     
        from .home_view import HomeView
        self.home_view = HomeView(self.app)

        # Create UI elements
        self.label = toga.Label("Login to MyHomeTheater", style=Pack(font_size=20, padding_bottom=20))
        self.user = toga.TextInput(placeholder="Username", style=Pack(padding_bottom=10, width=200))
        self.pwd = toga.PasswordInput(placeholder="Password", style=Pack(padding_bottom=20, width=200))
        self.btn = toga.Button("Login", on_press=self.login, style=Pack(padding_bottom=10))
        self.error_label = toga.Label("", style=Pack(color="red"))
        
        self.add(
            self.label,
            self.user,
            self.pwd,
            self.btn,
            self.error_label
        )
    
    async def login(self, widget):
        username = self.user.value.strip()
        password = self.pwd.value.strip()
        print(f"frontend/src/myapp/views/login.py Attempting login with username: {username}")
        
        if not username or not password:
            self.error_label.text = "Please enter username and password"
            return
        
        self.btn.enabled = False
        self.btn.label = "Logging in..."
        
        result = await self.api.login(username, password)
        
        if result.get("success"):
            print("frontend/src/myapp/views/login.py Login successful, switching to HomeView")
            # Switch to HomeView
            self.app.main_window.content = self.home_view
            #from .. import views
            #self.app.main_window.content = views.get_home_view(self.app)
        else:
            self.error_label.text = f"frontend/src/myapp/views/login.py Login failed: {result.get('error', 'Unknown error')}"
            self.btn.enabled = True
            self.btn.label = "Login"