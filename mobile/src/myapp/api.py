#frontend/src/myapp/api.py
"""2️⃣ API Interceptor (Auto-Attach Token + Retry) - (Interceptor Pattern)
Handles API requests, auto-attaches tokens, refreshes on 401.
"""
import requests
import httpx
import json
from typing import Dict, Any, List, Optional
import asyncio
from pathlib import Path
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
        self.app = app  # Store app reference
        self.storage = SecureStorage(self.app)  # Pass app to storage
        self.access_token = self.storage.access_token()
        self.session = requests.Session()
        self.session.timeout = 30
        print(f"frontend/src/myapp/api.py APIClient init self.access_token= {self.access_token}")
        
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

        print(f"frontend/src/myapp/api.py Attempting login to: {url}, Data: {data}, Headers: {headers}")
        
        try:
            r = await self.client.post(url, data=data, headers=headers)
            # Debug: Print response details
            print(f"Status Code: {r.status_code}")
            print(f"Response Headers: {dict(r.headers)}")
            print(f"Response Text (first 500 chars): {r.text[:500]}")
            
            # Check if response is valid JSON
            if r.status_code != 200:
                print(f"frontend/src/myapp/api.py Error: Received status {r.status_code}")
                # Try to parse as JSON if possible, otherwise use text
                try:
                    error_data = r.json()
                    print(f"frontend/src/myapp/api.py Error JSON: {error_data}")
                except:
                    print(f"frontend/src/myapp/api.py Error Text: {r.text}")
                return {"success": False, "error": f"HTTP {r.status_code}"}
            
            data = r.json()
            print(f"frontend/src/myapp/api.py Login successful, response: {data} , response keys: {list(data.keys())}")

            # r.status_code = 200  # For testing purposes only                        
            if "access_token" in data:
                self.storage.save_tokens(data["access_token"], data["refresh_token"])   
                self.access_token = data["access_token"]
                print(f"frontend/src/myapp/api.py Access token set and saved: {self.access_token[:20]}...")
            
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
                f"{self.base_url}/auth/refresh",
                json={"refresh_token": self.storage.refresh_token()}
            )
            r.raise_for_status()
            self.storage.save_tokens(
                r.json()["access_token"],
                self.storage.refresh_token()
            )

    async def request(self, method, path, **kwargs):
        print(f"APIClient.request: {method} {path} with kwargs: {kwargs.keys()}")

        if self.storage.is_access_expired():
            await self._refresh()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.storage.access_token()}"

        async with httpx.AsyncClient() as c:
            r = await c.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                **kwargs
            )

        if r.status_code == 401:
            await self._refresh()
            headers["Authorization"] = f"Bearer {self.storage.access_token()}"
            async with httpx.AsyncClient() as c:
                r = await c.request(
                    method,
                    f"{self.base_url}{path}",
                    headers=headers,
                    **kwargs
                )

        r.raise_for_status()
        return r.json()            

    async def get_user_profile(self):
        """Get user profile info"""
        print(f"frontend/src/myapp/api.py APIClient get_user_profile self.access_token= {self.access_token}")
        if not self.access_token:
            return None
            
        try:
            response = await self.client.get(
                f"{self.base_url}/users/me",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting user profile: {e}")
        return None
    
    async def get_continue_watching(self):
        """Get continue watching items"""
        try:
            print(f"frontend/src/myapp/api.py api get_continue_watching Bearer {self.access_token} ")
            response = await self.client.get(
                f"{self.base_url}/watch/continue",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            print(f"frontend/src/myapp/api.py api get_continue_watching response.status_code={response.status_code} ")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting continue watching: {e}")
        return []
    
    async def get_recommendations(self, limit=10):
        """Get content recommendations"""
        try:
            print(f"frontend/src/myapp/api.py api get_recommendations Bearer {self.access_token} ")
            response = await self.client.get(
                f"{self.base_url}/recommendations/",
                params={"limit": limit},
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            print(f"frontend/src/myapp/api.py api get_recommendations response.status_code={response.status_code} ")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting recommendations: {e}")
        return []
    

    async def search_content(self, query, limit=20):
        """Search for content"""
        try:
            print(f"frontend/src/myapp/api.py api search_content Bearer {self.access_token} ")
            response = await self.client.get(
                f"{self.base_url}/search",
                params={"q": query, "limit": limit},
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error searching: {e}")
        return []

    async def upload_images(self, image_paths: List[str], settings: Dict) -> Dict:
        """Upload images and create video"""
        try:
            # Prepare files for upload
            files = []
            for image_path in image_paths:
                if Path(image_path).exists():
                    files.append(
                        ('files', (Path(image_path).name, open(image_path, 'rb'), 'image/jpeg'))
                    )

            # Prepare settings
            data = {'settings': json.dumps(settings)}

            # Make the request
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.session.post(
                    f"{self.base_url}/process/upload",
                    files=files,
                    data=data
                )
            )

            # Close all files
            for _, (_, file_obj, _) in files:
                file_obj.close()

            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f"Server error: {response.status_code}", 'details': response.text}

        except Exception as e:
            return {'error': str(e)}

    async def get_status(self, job_id: str) -> Dict:
        """Get processing status for a job"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.session.get(f"{self.base_url}/status/{job_id}")
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f"Server error: {response.status_code}"}

        except Exception as e:
            return {'error': str(e)}

    async def list_videos(self) -> List[Dict]:
        """Get list of available videos"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.session.get(f"{self.base_url}/videos")
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('videos', [])
            else:
                return []

        except Exception as e:
            print(f"Error listing videos: {e}")
            return []

    async def download_video(self, filename: str, save_path: str) -> bool:
        """Download a video file"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.session.get(
                    f"{self.base_url}/video/{filename}",
                    stream=True
                )
            )

            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            else:
                return False

        except Exception as e:
            print(f"Error downloading video: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test connection to the API"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.session.get(f"{self.base_url}/health", timeout=5)
            )
            return response.status_code == 200
        except:
            return False

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