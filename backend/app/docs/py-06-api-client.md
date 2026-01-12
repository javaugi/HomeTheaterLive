6️⃣ API Client (Shared Python)
import httpx
from myhometheater.storage import SecureStorage

BASE_URL = "https://api.myhometheater.com/api/v1"

class APIClient:

    def __init__(self):
        self.storage = SecureStorage()

    async def login(self, username, password):
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BASE_URL}/login/access-token",
                data={"username": username, "password": password}
            )
            r.raise_for_status()
            self.storage.save_token(r.json()["access_token"])

    async def get(self, path):
        token = self.storage.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            return await client.get(f"{BASE_URL}{path}", headers=headers)
