7️⃣ Secure Token Storage (CRITICAL)
storage.py
import toga

class SecureStorage:

    def save_token(self, token):
        toga.App.app.preferences["token"] = token

    def get_token(self):
        return toga.App.app.preferences.get("token")
