# mobile/app/api/endpoints/mobile.py
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Depends
import aiofiles
from pathlib import Path
import time

from mobile.app.core.config import settings

router = APIRouter(prefix="/mobile", tags=["mobile"])


@router.get("/debug/headers")
async def debug_headers(request: Request):
    """Debug endpoint to see all headers"""
    headers = dict(request.headers)

    # Hide sensitive headers
    sensitive = ['authorization', 'cookie', 'token', 'password', 'secret']
    for key in list(headers.keys()):
        if any(s in key.lower() for s in sensitive):
            headers[key] = "[REDACTED]"

    return {
        "headers": headers,
        "client": {
            "host": request.client.host if request.client else None,
            "port": request.client.port if request.client else None,
        },
        "url": str(request.url),
        "method": request.method,
    }


@router.post("/upload/chunk")
async def upload_chunk(
    request: Request,
    file: UploadFile = File(...),
    chunk_index: int = 0,
    total_chunks: int = 1,
    file_hash: str = ""
):
    """Upload file in chunks (for mobile large files)"""
    print(f"\nDEBUG: Mobile chunk upload:  Filename: {file.filename}")
    print(f"  Content-Type: {file.content_type}")
    print(f"  Chunk: {chunk_index + 1}/{total_chunks}")
    print(f"  File hash: {file_hash[:16]}...")

    # Create upload directory
    upload_dir = settings.UPLOAD_DIR or Path("mobile_uploads")
    upload_dir.mkdir(exist_ok=True)

    # Temporary chunk file
    chunk_filename = f"{file_hash}_chunk_{chunk_index}"
    chunk_path = upload_dir / chunk_filename

    # Save chunk
    content = await file.read()
    async with aiofiles.open(chunk_path, "wb") as f:
        await f.write(content)

    print(f"  Saved chunk to: {chunk_path}")

    # If this is the last chunk, assemble file
    if chunk_index == total_chunks - 1:
        print(f"  All chunks received, assembling file={file_hash}_{file.filename} ...")
        final_path = upload_dir / f"{file_hash}_{file.filename}"

        # Combine chunks
        async with aiofiles.open(final_path, "wb") as final_file:
            for i in range(total_chunks):
                chunk_path = upload_dir / f"{file_hash}_chunk_{i}"
                if chunk_path.exists():
                    async with aiofiles.open(chunk_path, "rb") as chunk_file:
                        content = await chunk_file.read()
                        await final_file.write(content)
                    # Clean up chunk
                    chunk_path.unlink()

        print(f"  File assembled: {final_path}")
        return {
            "status": "complete",
            "file_path": str(final_path),
            "file_size": final_path.stat().st_size,
        }

    return {"status": "chunk_received", "next_chunk": chunk_index + 1}


@router.get("/offline/data")
async def get_offline_data(request: Request):
    """Get data for offline use"""
    # Check cache for offline data
    cache_service = request.app.state.cache_service

    offline_data = await cache_service.get("offline_data")
    if offline_data:
        print("DEBUG: Returning cached offline data")
        return {
            "source": "cache",
            "timestamp": time.time(),
            "data": offline_data,
        }

    # If not in cache and backend is connected, fetch from backend
    if request.app.state.backend_connected:
        print("DEBUG: Fetching offline data from backend")
        import httpx

        async with httpx.AsyncClient() as client:
            backend_url = f"{settings.API_BASE_URL}{settings.API_V1_STR}/data/offline"
            response = await client.get(backend_url)

            if response.status_code == 200:
                data = response.json()

                # Cache for offline use
                await cache_service.set("offline_data", data, ttl=3600)  # 1 hour

                return {
                    "source": "backend",
                    "timestamp": time.time(),
                    "data": data,
                }

    # If offline and no cache
    raise HTTPException(
        status_code=503,
        detail="Offline data not available. Please connect to network."
    )

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    cache_dir: Path = Depends(get_cache_dir),
    downloads_dir: Path = Depends(get_downloads_dir)
):
    """Upload file to mobile server"""
    # Save to downloads
    download_path = downloads_dir / file.filename
    async with aiofiles.open(download_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Also cache metadata
    cache_file = cache_dir / f"{file.filename}.meta"
    async with aiofiles.open(cache_file, "w") as f:
        import json
        metadata = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "uploaded_at": time.time()
        }
        await f.write(json.dumps(metadata))

    return {
        "message": "File uploaded",
        "download_path": str(download_path),
        "cache_path": str(cache_file)
    }
# Include router in main app
# In mobile/main.py:
# from mobile.api.endpoints import mobile as mobile_endpoints
# app.include_router(mobile_endpoints.router)# -*- coding: utf-8 -*-

