#mobile/src/myapp/api.py
"""2️⃣ API Interceptor (Auto-Attach Token + Retry) - (Interceptor Pattern)
Handles API requests, auto-attaches tokens, refreshes on 401.
"""
import httpx
import json
from typing import Dict, Any, List, Optional
import asyncio
from pathlib import Path
from .storage import SecureStorage

import aiohttp
import os


#BASE_URL = "https://api.example.com/api/v1"
BASE_URL = "http://127.0.0.1:8000/api/v1"
"""⚠️ DO NOT use localhost on iOS
iOS does not resolve it properly
Always use 127.0.0.1"""

""" Why aiohttp.ClientSession over requests.Session:
1. Async Compatibility: aiohttp is async/await compatible, which works better with BeeWare/Toga's async event loop
2. Better Performance: aiohttp doesn't block the main thread during network calls
3. Mobile-Friendly: Async operations prevent UI freezing during network calls
4. Modern Approach: aiohttp is designed for async Python applications
"""

class APIClient:
    def __init__(self, app=None, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient()
        self.app = app  # Store app reference
        self.storage = SecureStorage(self.app)  # Pass app to storage
        self.access_token = self.storage.access_token()
        #self.session = requests.Session()
        self.session: Optional[aiohttp.ClientSession] = None
        #self.session.timeout = 30
        self.is_closed = False
        self.access_token = None        
        print(f"mobile/src/myapp/api.py APIClient init self.access_token= {self.access_token}")
                    
    async def ensure_session(self):
        """Ensure we have an active aiohttp session"""
        print(f"DEBUG: ensure_session - session={self.session}, is_closed={self.is_closed}")        
        if self.session is None or self.is_closed or self.session.closed:
            try:
                # Close old session if it exists
                if self.session and not self.session.closed:
                    await self.session.close()
                
                # Create new session with appropriate timeout
                timeout = aiohttp.ClientTimeout(
                    total=300,      # 5 minutes total timeout
                    connect=10,     # 10 seconds to connect
                    sock_read=60    # 60 seconds to read data
                )
                
                self.session = aiohttp.ClientSession(
                    timeout=timeout,
                    headers={
                        'User-Agent': 'Image2Video-Mobile/1.0',
                        'Accept': 'application/json'
                    }
                )
                self.is_closed = False
                print("DEBUG: Created new aiohttp session")
                
            except Exception as e:
                print(f"DEBUG ERROR: Failed to create session: {e}")
                raise
                    
                    
    async def test_connection(self) -> bool:
        """Test connection to the backend"""
        await self.ensure_session()
        
        try:            
            url = f"{self.base_url}/health"
            print(f"mobile/src/myapp/api.py APIClient test_connection {url}")
            
            print(f"Calling URL: /api/v1/videos/create={self.base_url}/api/v1/videos/create")
            
            """
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.session.get(url, timeout=5)
            )
            return response.status_code == 200
            """
            async with self.session.get(url, timeout=5) as response:
                print(f"mobile/src/myapp/api.py APIClient test_connection {url}, response.status={response.status}")
                return response.status == 200
                
        except Exception as e:
            print(f"DEBUG: Connection test failed: {e}")
            return False
            
        
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

        print(f"mobile/src/myapp/api.py Attempting login to: {url}, Data: {data}, Headers: {headers}")
        
        try:
            r = await self.client.post(url, data=data, headers=headers)
            # Debug: Print response details
            print(f"Status Code: {r.status_code}")
            print(f"Response Headers: {dict(r.headers)}")
            print(f"Response Text (first 500 chars): {r.text[:500]}")
            
            # Check if response is valid JSON
            if r.status_code != 200:
                print(f"mobile/src/myapp/api.py Error: Received status {r.status_code}")
                # Try to parse as JSON if possible, otherwise use text
                try:
                    error_data = r.json()
                    print(f"mobile/src/myapp/api.py Error JSON: {error_data}")
                except:
                    print(f"mobile/src/myapp/api.py Error Text: {r.text}")
                return {"success": False, "error": f"HTTP {r.status_code}"}
            
            data = r.json()
            print(f"mobile/src/myapp/api.py Login successful, response: {data} , response keys: {list(data.keys())}")

            # r.status_code = 200  # For testing purposes only                        
            if "access_token" in data:
                self.storage.save_tokens(data["access_token"], data["refresh_token"])   
                self.access_token = data["access_token"]
                print(f"mobile/src/myapp/api.py Access token set and saved: {self.access_token[:20]}...")
            
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
        print(f"*** APIClient.request: {method} {path} with kwargs: {kwargs.keys()}")

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
        print(f"mobile/src/myapp/api.py APIClient get_user_profile self.access_token= {self.access_token}")
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
            print(f"mobile/src/myapp/api.py api get_continue_watching Bearer {self.access_token} ")
            response = await self.client.get(
                f"{self.base_url}/watch/continue",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            print(f"mobile/src/myapp/api.py api get_continue_watching response.status_code={response.status_code} ")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting continue watching: {e}")
        return []
    
    async def get_recommendations(self, limit=10):
        """Get content recommendations"""
        try:
            print(f"mobile/src/myapp/api.py api get_recommendations Bearer {self.access_token} ")
            response = await self.client.get(
                f"{self.base_url}/recommendations/",
                params={"limit": limit},
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            print(f"mobile/src/myapp/api.py api get_recommendations response.status_code={response.status_code} ")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting recommendations: {e}")
        return []
    

    async def search_content(self, query, limit=20):
        """Search for content"""
        try:
            print(f"mobile/src/myapp/api.py api search_content Bearer {self.access_token} ")
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

    """ Move dthe front end code to the backend called from this api 
    """
    async def create_video(
        self,
        image_paths: List[str],
        fps: int = 24,
        duration_per_image: float = 2.0,
        transition_type: str = "none",
        resolution: Optional[tuple] = None,
        quality: str = "high"
    ) -> Dict[str, Any]:
        """Create video by uploading images to backend"""
        print(f"mobile/src/myapp/api.py create_video fps={fps}, image_paths={len(image_paths)}")
        await self.ensure_session()
        
        try:
            print(f"DEBUG: create_video - Uploading {len(image_paths)} images")
            # Prepare form data
            form_data = aiohttp.FormData()
            form_data.add_field('fps', str(fps))
            form_data.add_field('duration_per_image', str(duration_per_image))
            form_data.add_field('transition_type', transition_type)
            form_data.add_field('quality', quality)
            
            if resolution:
                form_data.add_field('resolution_width', str(resolution[0]))
                form_data.add_field('resolution_height', str(resolution[1]))
            
            # Add image files
            """
            for img_path in image_paths:
                if Path(img_path).exists():
                    with open(img_path, 'rb') as f:
                        form_data.add_field(
                            'files',
                            f.read(),
                            filename=Path(img_path).name,
                            content_type='image/jpeg'
                        )
                    print(f"DEBUG: Added image: {Path(img_path).name}")
            """
            
            for img_path in image_paths:
                if isinstance(img_path, str) and Path(img_path).exists():
                    with open(img_path, 'rb') as f:
                        img_data = f.read()
                    
                    # Determine content type
                    content_type = self._get_image_content_type(img_path)
                    
                    form_data.add_field(
                        'files',
                        img_data,
                        filename=Path(img_path).name,
                        content_type=content_type
                    )
                    print(f"DEBUG: Added image: {Path(img_path).name}")
                else:
                    print(f"DEBUG WARNING: Image not found: {img_path}")
                    
            
            print(f"mobile/src/myapp/api.py create_video calling /videos/create, \n form_data={form_data}")
            # Send request
            # Send request
            url = f"{self.base_url}/videos/create"
            print(f"DEBUG: POST to {url}")
            async with self.session.post(url, data=form_data) as response:
                print(f"DEBUG: response.status from POST {response.status}")
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f"Server error: {response.status}",
                        'details': error_text
                    }
        except aiohttp.ClientError as e:
            print(f"ERROR: aiohttp.ClientError {str(e)}")
            return {
                'success': False,
                'error': f"Network error: {str(e)}"
            }                    
        except Exception as e:
            print(f"ERROR: Exception {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        
    def _get_image_content_type(self, filepath: str) -> str:
        print(f"_get_image_content_type Determine content type based on file extension filepath={filepath}")
        ext = Path(filepath).suffix.lower()
        
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.webp': 'image/webp'
        }
        
        return content_types.get(ext, 'application/octet-stream')        
    
    async def get_video_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of video processing job"""
        await self.ensure_session()
        print(f"mobile/src/myapp/api.py get_video_status job_id={job_id} calling /videos/{job_id}/status")
        
        try:
            url = f"{self.base_url}/videos/{job_id}/status"
            print(f"DEBUG: GET {url}")
            
            async with self.session.get(url) as response:
                print(f"mobile/src/myapp/api.py get_video_status job_id={job_id} response.status={response.status}")
                if response.status == 200:
                    return await response.json()
                else:
                    return {
                        'success': False,
                        'status': 'error',                        
                        'error': f"Server error: {response.status}"
                    }
        except aiohttp.ClientError as e:
            print(f"mobile/src/myapp/api.py get_video_status job_id={job_id} aiohttp.ClientError=str(e)")
            return {
                'success': False,
                'status': 'error',
                'error': f"Network error: {str(e)}"
            }                
        except Exception as e:
            print(f"mobile/src/myapp/api.py get_video_status job_id={job_id} exception=str(e)")
            return {
                'success': False,
                'status': 'error',                        
                'error': f"Unexpected error: {str(e)}"
            }
    
    async def download_video(self, filename: str, save_path: str) -> bool:
        print("Download video file from backend")
        try:
            await self.ensure_session()
            print(f"mobile/src/myapp/api.py download_video filename={filename}, save_path={save_path}")
            
            url = f"{self.base_url}/videos/download/{filename}"
            print(f"DEBUG: Downloading from {url} to {save_path}")
            
            async with self.session.get(url) as response:
                print(f"mobile/src/myapp/api.py download_video return status={response.status}")
                if response.status == 200:
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    
                    # Download with progress
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    with open(save_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Optional: Report progress
                                if total_size > 0:
                                    progress = (downloaded / total_size) * 100
                                    print(f"DEBUG: Download progress: {progress:.1f}%")                                        
                    # Verify download
                    if os.path.exists(save_path):
                        file_size = os.path.getsize(save_path)
                        print(f"DEBUG: Download complete: {file_size} bytes")
                        
                        return {
                            'success': True,
                            'path': save_path,
                            'size': file_size
                        }
                    else:
                        print(f"DEBUG: Download failed and File was not saved save_path={save_path}")
                        return {
                            'success': False,
                            'error': 'File was not saved'
                        }
                else:
                    response_text = await response.text()
                    print(f"DEBUG: Download failed response_text={response_text}")
                    return {
                        'success': False,
                        'error': f"Download failed: HTTP {response.status}",
                        'details': response_text
                    }
                    
        except aiohttp.ClientError as e:
            print(f"DEBUG: Download aiohttp.ClientError {str(e)}")
            return {
                'success': False,
                'error': f"Network error: {str(e)}"
            }
        except Exception as e:
            print(f"Download error: {e}")
            return {
                'success': False,
                'error': f"Download error: {str(e)}"
            }            
    
    async def poll_status(self, job_id: str, interval: float = 2.0, max_attempts: int = 300) -> Dict[str, Any]:
        print("poll_status Poll for job completion job_id={job_id}")
        attempts = 0
        
        while attempts < max_attempts:
            try:
                status = await self.get_video_status(job_id)
                print("poll_status job_id={job_id} \n status={status}")
                
                if not status.get('success', True):  # Handle API error
                    return {'status': 'failed', 'error': status.get('error')}
                
                if status['status'] in ['completed', 'failed']:
                    return status
                
                # Still processing
                await asyncio.sleep(interval)
                attempts += 1
                
            except Exception as e:
                return {'status': 'error', 'error': str(e)}
        
        return {'status': 'timeout', 'error': 'Processing timeout'}
    
    async def poll_status_new(
        self, 
        job_id: str, 
        on_progress=None, 
        interval: float = 2.0,
        timeout: float = 600.0,
        max_attempts: int = 300
    ) -> Dict[str, Any]:
        print("Poll for job completion with callback support")
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                return {
                    'success': False,
                    'status': 'timeout',
                    'error': f'Processing timeout after {timeout} seconds'
                }
            
            # Get status
            status_data = await self.get_video_status(job_id)
            
            if not status_data.get('success', True):
                return status_data
            
            current_status = status_data.get('status')
            progress = status_data.get('progress', 0)
            message = status_data.get('message', '')
            
            # Call progress callback if provided
            if on_progress:
                await on_progress(progress, message, current_status)
            
            # Check if processing is complete
            if current_status == 'completed':
                return status_data
            elif current_status == 'failed':
                return {
                    'success': False,
                    'status': 'failed',
                    'error': status_data.get('message', 'Processing failed'),
                    'details': status_data
                }
            
            # Wait before next poll
            await asyncio.sleep(interval)
            
    
    async def close(self):
        """Close the session"""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
                self.is_closed = True
                print("DEBUG: Session closed")
        except Exception as e:
            print(f"DEBUG: Error closing session: {e}")
            
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