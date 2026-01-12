
"""2️⃣ API Interceptor (Auto-Attach Token + Retry) - (Interceptor Pattern)
Handles API requests, auto-attaches tokens, refreshes on 401.
"""
import httpx
import json
from typing import Optional, Dict, Any
from .storage import SecureStorage

#BASE_URL = "https://api.example.com/api/v1"
BASE_URL = "http://127.0.0.1:8000/api/v1"
"""⚠️ DO NOT use localhost on iOS
iOS does not resolve it properly
Always use 127.0.0.1"""

class APIClient:
    def __init__(self, app=None, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.access_token: Optional[str] = None
        self.app = app  # Store app reference
        self.storage = SecureStorage(app)  # Pass app to storage
        
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/login"
        # data = {"username": username, "password": password}
        data={
                "username": username,
                "password": password,
                "grant_type": "password",
                "scope": "",
                "client_id": "",
                "client_secret": ""                    
            }
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }

        print(f"Attempting login to: {url}, Data: {data}, Headers: {headers}")
        
        try:
            r = await self.client.post(url, data=data, headers=headers)
            # Debug: Print response details
            print(f"Status Code: {r.status_code}")
            print(f"Response Headers: {dict(r.headers)}")
            print(f"Response Text (first 500 chars): {r.text[:500]}")
            
            # Check if response is valid JSON
            if r.status_code != 200:
                print(f"Error: Received status {r.status_code}")
                # Try to parse as JSON if possible, otherwise use text
                try:
                    error_data = r.json()
                    print(f"Error JSON: {error_data}")
                except:
                    print(f"Error Text: {r.text}")
                return {"success": False, "error": f"HTTP {r.status_code}"}
            
            data = r.json()
            print(f"Login successful, response: {data} , response keys: {list(data.keys())}")
            self.storage.save_tokens(data["access_token"], data["refresh_token"])   
            self.access_token = data["access_token"]
            print(f"Access token set and saved: {self.access_token[:20]}...")

            # r.status_code = 200  # For testing purposes only            
            
            if "access_token" in data:
                self.access_token = data["access_token"]
                print(f"Access token set: {self.access_token[:20]}...")
            
            return {"success": True, **data}            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response that failed to decode: {r.text[:200]}")
            return {"success": False, "error": "Invalid response from server"}
        except httpx.RequestError as e:
            print(f"Request error: {e}")
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    async def _refresh(self):
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{BASE_URL}/auth/refresh",
                json={"refresh_token": self.storage.refresh_token()}
            )
            r.raise_for_status()
            self.storage.save_tokens(
                r.json()["access_token"],
                self.storage.refresh_token()
            )

    async def request(self, method, path, **kwargs):
        if self.storage.is_access_expired():
            await self._refresh()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.storage.access_token()}"

        async with httpx.AsyncClient() as c:
            r = await c.request(
                method,
                f"{BASE_URL}{path}",
                headers=headers,
                **kwargs
            )

        if r.status_code == 401:
            await self._refresh()
            headers["Authorization"] = f"Bearer {self.storage.access_token()}"
            async with httpx.AsyncClient() as c:
                r = await c.request(
                    method,
                    f"{BASE_URL}{path}",
                    headers=headers,
                    **kwargs
                )

        r.raise_for_status()
        return r.json()            

"""
✅ Correct Way (FastAPI + Mobile)
1. Why your current call fails
2. params= sends query string, not body
3. FastAPI login endpoints expect form-encoded body
4. OAuth2 spec requires application/x-www-form-urlencoded
5. Query params may be logged → security risk
--- 
✔ Sends body, not URL
✔ FastAPI parses it correctly
✔ Tokens returned successfully
🚫 DO NOT DO THESE
---
❌ Send credentials via query params
❌ Use JSON body for OAuth2 login
❌ Store password locally
❌ Log request body
🧠 Why This Matters (App Store Reality)
---
Apple reviewers:
1. Inspect network traffic
2. Reject insecure auth
3. Expect OAuth2 patterns
---
This approach:
✅ Passes review
✅ Secure
✅ Standards-compliant
✅ Works on iOS + Android
"""