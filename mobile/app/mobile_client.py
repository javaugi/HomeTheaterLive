# mobile_client.py
import httpx
import asyncio
from typing import Optional

class MobileClient:
    """Client for mobile FastAPI server"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def health_check(self):
        """Check mobile server health"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def get_config(self):
        """Get mobile configuration"""
        response = await self.client.get(f"{self.base_url}/mobile/config")
        return response.json()
    
    async def upload_file(self, file_path: str, chunk_size: int = 1024 * 1024):
        """Upload file in chunks"""
        import hashlib
        from pathlib import Path
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Calculate file hash
        file_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                file_hash.update(chunk)
        file_hash_str = file_hash.hexdigest()
        
        # Upload in chunks
        total_size = path.stat().st_size
        total_chunks = (total_size + chunk_size - 1) // chunk_size
        
        print(f"Uploading {path.name} ({total_size} bytes) in {total_chunks} chunks...")
        
        with open(file_path, "rb") as f:
            for i in range(total_chunks):
                chunk_data = f.read(chunk_size)
                
                files = {"file": (path.name, chunk_data, "application/octet-stream")}
                data = {
                    "chunk_index": i,
                    "total_chunks": total_chunks,
                    "file_hash": file_hash_str,
                }
                
                response = await self.client.post(
                    f"{self.base_url}/mobile/upload/chunk",
                    files=files,
                    data=data
                )
                
                result = response.json()
                print(f"  Chunk {i+1}/{total_chunks}: {result.get('status', 'unknown')}")
                
                if i == total_chunks - 1:
                    return result
        
        return {"status": "complete"}
    
    async def close(self):
        """Close client"""
        await self.client.aclose()


async def main():
    """Test mobile client"""
    client = MobileClient()
    
    try:
        # Check health
        health = await client.health_check()
        print("Health:", health)
        
        # Get config
        config = await client.get_config()
        print("Config:", config)
        
        # Upload a test file
        # result = await client.upload_file("test_video.mp4")
        # print("Upload result:", result)
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())# -*- coding: utf-8 -*-

