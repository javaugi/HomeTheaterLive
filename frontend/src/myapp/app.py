
"""
My Home Theater Application to manipulate photos, images, videos and films with integated AI functions
"""
import toga
from .storage import SecureStorage
from .views.login import LoginView
from .views.home import HomeView

class MyHomeTheater(toga.App):
    def startup(self):
        print("App starting up...")
        self.main_window = toga.MainWindow(title=self.formal_name)

        # Set the app instance BEFORE creating storageif the singleton pattern is used
        # SecureStorage.set_app(self)

        # 👇 PASS self (the App instance)
        # storage = SecureStorage()
        storage = SecureStorage(self)
        print(f"Checking for tokens... token exists: {bool(storage.access_token())} expired: {storage.is_access_expired()}")

        if storage.access_token() and not storage.is_access_expired():
            print("User authenticated, loading HomeView")
            self.main_window.content = HomeView(self)
        else:
            print("User not authenticated, loading LoginView")
            self.main_window.content = LoginView(self)

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