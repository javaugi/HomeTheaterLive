5️⃣ BeeWare App Code
app.py

import toga
from myhometheater.views.login import LoginView

class MyApp(toga.App):

    def startup(self):
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = LoginView(self)
        self.main_window.show()

def main():
    return MyApp()

Login View

import toga
from toga.style import Pack
from toga.style.pack import COLUMN
from myhometheater.api import APIClient

class LoginView(toga.Box):

    def __init__(self, app):
        super().__init__(style=Pack(direction=COLUMN, padding=20))
        self.app = app
        self.api = APIClient()

        self.username = toga.TextInput(placeholder="Email")
        self.password = toga.PasswordInput(placeholder="Password")
        self.button = toga.Button("Login", on_press=self.login)

        self.add(self.username, self.password, self.button)

    async def login(self, widget):
        await self.api.login(
            self.username.value,
            self.password.value
        )
