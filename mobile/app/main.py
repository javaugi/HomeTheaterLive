# mobile/app/main.py
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Startup
    print("\n=== MOBILE SERVER STARTUP ===")
    print("\n" + "="*60)
    print("Starting HomeTheaterLive Mobile API Server...")
    print(f"DEBUG: Current Working Directory: {os.getcwd()}")
    print(f"DEBUG: Python Executable: {os.sys.executable}")
    print(f"DEBUG: Python Path: {os.sys.path}")

    # Setup directories in app state
    app.state.directories = {
        "cache": settings.CACHE_DIR,
        "downloads": settings.DOWNLOADS_DIR,
        "logs": settings.LOGS_DIR,
        "data": settings.DATA_DIR,
        "temp": Path("/tmp/hometheaterlive") if os.name == "posix" else Path(os.getenv("TEMP", "")) / "hometheaterlive"
    }

    # Create directories
    for name, path in app.state.directories.items():
        if path:
            path.mkdir(parents=True, exist_ok=True)
            print(f"DEBUG: Created {name} directory: {path}")

    # Store directory paths in app state for easy access
    app.state.cache_dir = settings.CACHE_DIR
    app.state.downloads_dir = settings.DOWNLOADS_DIR

    # Configuration dump
    print(f"\nDEBUG: Mobile Configuration:  API_BASE_URL: {settings.API_BASE_URL}")
    print(f"  API_TIMEOUT_SECONDS: {settings.API_TIMEOUT_SECONDS}")
    print(f"  OFFLINE_MODE_ENABLED: {settings.OFFLINE_MODE_ENABLED}")
    print(f"  MOBILE_CACHE_SIZE: {settings.MOBILE_CACHE_SIZE}")
    print(f"  PUSH_NOTIFICATIONS_ENABLED: {settings.PUSH_NOTIFICATIONS_ENABLED}")

    # Initialize mobile services
    print("\nDEBUG: Initializing mobile services...")
    from .services.cache import init_cache_service
    #from .services.auth import init_auth_service
    #from .services.sync import init_sync_service

    app.state.cache_service = await init_cache_service(settings.MOBILE_CACHE_SIZE)
    #app.state.auth_service = await init_auth_service()
    #app.state.sync_service = await init_sync_service()

    print("DEBUG: Mobile services initialized")

    # Health check backend connection
    backend_url = settings.BACKEND_URL + settings.API_V1_STR + "/health"
    print(f"\nDEBUG: Checking backend connectivity from url={backend_url}...")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(backend_url)
            print(f"\nDEBUG: Health check from url={backend_url} with return value={response}")
            print(f"DEBUG: Backend URL: {backend_url}, Connectivity Status: ✓ (HTTP {response.status_code})")
            if response.status_code == 200:
                app.state.backend_connected = True
            else:
                app.state.backend_connected = False
                print(f"DEBUG: Backend returned non-200: {response.text}")
    except Exception as e:
        print(f"DEBUG: Backend connectivity: ✗ ({type(e).__name__}: {str(e)}) from uri={backend_url}")
        app.state.backend_connected = False

    print("\n" + "="*60)
    print("Mobile API Server startup complete!")
    print("="*60 + "\n")

    yield

    # Shutdown
    print("\n" + "="*60)
    print("Shutting down Mobile API Server...")

    # Cleanup services
    if hasattr(app.state, 'cache_service'):
        await app.state.cache_service.cleanup()
        print("DEBUG: Cache service cleaned up")

    if hasattr(app.state, 'sync_service'):
        await app.state.sync_service.cleanup()
        print("DEBUG: Sync service cleaned up")

    print("Mobile API Server shutdown complete!")
    print("="*60)


# Create FastAPI app with lifespan
app = FastAPI(
    title=f"{settings.PROJECT_NAME} - Mobile API",
    description="Mobile API server for Home Theater Live",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.ENVIRONMENT == "local"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "local" else [
        "http://localhost:3000",
        "http://localhost:8080",
        # Add your mobile app origins
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware (similar to backend)
@app.middleware("http")
async def log_mobile_requests(request: Request, call_next):
    # Log request info
    print(f"\n{'='*50}")
    print(f"MOBILE REQUEST:  URL: {request.url}")
    print(f"  Method: {request.method}")
    print(f"  Path: {request.url.path}")
    print(f"  Client: {request.client.host if request.client else 'Unknown'}")

    # Log headers (excluding sensitive ones)
    headers = dict(request.headers)
    sensitive = ['authorization', 'cookie', 'token', 'password']
    safe_headers = {k: v for k, v in headers.items()
                   if not any(s in k.lower() for s in sensitive)}
    print(f"  Headers: {safe_headers}")

    # Log query params
    if request.query_params:
        print(f"  Query Params: {dict(request.query_params)}")

    # Time the request
    import time
    start_time = time.time()

    try:
        response = await call_next(request)
        elapsed = time.time() - start_time

        print(f"  Response: HTTP {response.status_code}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"{'='*50}")

        # Add custom header with response time
        response.headers["X-Response-Time"] = f"{elapsed:.3f}s"

        return response
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  Error: {type(e).__name__}: {str(e)}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"{'='*50}")
        raise


# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for mobile server"""
    status = {
        "status": "healthy",
        "service": "mobile-api",
        "environment": settings.ENVIRONMENT,
        "backend_connected": app.state.backend_connected if hasattr(app.state, 'backend_connected') else False,
        "cache_ready": hasattr(app.state, 'cache_service'),
        "sync_ready": hasattr(app.state, 'sync_service'),
        "timestamp": time.time()
    }
    return status


# Mobile-specific endpoints
@app.get("/mobile/config")
async def get_mobile_config():
    """Get mobile configuration (safe fields only)"""
    safe_config = {
        "project_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "api_base_url": str(settings.API_BASE_URL),
        "api_timeout": settings.API_TIMEOUT_SECONDS,
        "offline_mode": settings.OFFLINE_MODE_ENABLED,
        "push_enabled": settings.PUSH_NOTIFICATIONS_ENABLED,
        "default_page_size": settings.DEFAULT_PAGE_SIZE,
        "upload_chunk_size": settings.MOBILE_UPLOAD_CHUNK_SIZE,
        "max_image_size": settings.MOBILE_MAX_IMAGE_SIZE,
    }
    return safe_config


@app.get("/mobile/debug")
async def debug_info():
    """Debug endpoint for mobile server"""
    import sys
    import psutil

    # System info
    process = psutil.Process()

    debug_info = {
        "system": {
            "python_version": sys.version,
            "platform": sys.platform,
            "cwd": os.getcwd(),
            "pid": os.getpid(),
        },
        "memory": {
            "rss_mb": process.memory_info().rss / 1024 / 1024,
            "vms_mb": process.memory_info().vms / 1024 / 1024,
            "percent": process.memory_percent(),
        },
        "app_state": {
            "backend_connected": app.state.backend_connected if hasattr(app.state, 'backend_connected') else False,
            "cache_service": "active" if hasattr(app.state, 'cache_service') else "inactive",
            "auth_service": "active" if hasattr(app.state, 'auth_service') else "inactive",
            "sync_service": "active" if hasattr(app.state, 'sync_service') else "inactive",
        },
        "paths": {
            "cache_dir": str(settings.CACHE_DIR) if settings.CACHE_DIR else None,
            "downloads_dir": str(settings.DOWNLOADS_DIR) if settings.DOWNLOADS_DIR else None,
        }
    }

    return debug_info


# Example mobile API endpoints
@app.post("/mobile/upload")
async def mobile_upload():
    """Handle mobile file uploads"""
    return {"message": "Mobile upload endpoint"}


@app.get("/mobile/sync")
async def sync_data():
    """Sync data between mobile and backend"""
    if not app.state.backend_connected:
        return {"status": "offline", "message": "Cannot sync: backend not connected"}

    # Your sync logic here
    return {"status": "sync_started"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("MOBILE_PORT", "8001"))  # Different port than backend

    uvicorn.run(
        "mobile.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.ENVIRONMENT == "local",
        log_level="debug" if settings.ENVIRONMENT == "local" else "info",
    )# -*- coding: utf-8 -*-

