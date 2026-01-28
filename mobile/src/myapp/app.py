#mobile/src/myapp/app.py
"""
My Home Theater Application to manipulate photos, images, videos and films with integated AI functions
"""
print(">>> importing mobile/src/myapp/app.py")
import toga
from .storage import SecureStorage
from .views.login import LoginView
from .views.home_view import HomeView
import asyncio
print(">>> importing mobile/src/myapp/app.py done")

class MyHomeTheater(toga.App):
    def __init__(self, formal_name=None):
        super().__init__(formal_name)

        # API Configuration - update with your server IP
        #self.api_base_url = "http://192.168.1.100:8000/api/v1"
        self.headers = {"Content-Type": "application/json"}
        # Views
        self.home_view = None
        self.login_view = None

    def startup(self):
        print("mobile/src/myapp/app.py App starting up...")
        SecureStorage.app = self   # 🔥 REQUIRED
        self._tokens = {}        
        self.home_view = HomeView(self)
        self.login_view = LoginView(self)
        self.main_window = toga.MainWindow(title=self.formal_name)

        # Set the app instance BEFORE creating storageif the singleton pattern is used
        # SecureStorage.set_app(self)

        # 👇 PASS self (the App instance)
        # storage = SecureStorage()
        storage = SecureStorage(self)
        print(f"Checking for tokens... token exists: {bool(storage.access_token())} expired: {storage.is_access_expired()}")

        if storage.access_token() and not storage.is_access_expired():
            print("mobile/src/myapp/app.py User authenticated, loading HomeView at mobile/src/myapp/views/home_view.py")
            self.main_window.content = self.home_view
            # Start background tasks if needed
            asyncio.create_task(self.background_tasks())
        else:
            print("User not authenticated, loading LoginView")
            self.main_window.content = self.login_view

        self.main_window.show()

def main():
    return MyHomeTheater()

"""
4️⃣ Security & App Store Checklist (IMPORTANT)

✅ HTTPS only
✅ OAuth2 form login
✅ Silent refresh
✅ Secure token storage
✅ Biometric unlock optional
✅ No credentials logged

Apple reviewers like this flow.

5️⃣ Common Failure Modes (Avoid These)

❌ JSON login instead of form-encoded
❌ Storing JWT in plain files
❌ Forcing login on every launch
❌ Refresh loop on 401
❌ Biometrics before user consent

🎯 Final Result

You now have:

✔ Seamless login
✔ Silent refresh
✔ Secure interceptor
✔ Biometric unlock
✔ App Store–approved auth flow

This is exactly how real production iOS/Android apps work."""