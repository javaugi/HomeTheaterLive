#!/usr/bin/env python
"""
run_backend.py Run backend server from HomeTheaterLive/backend directory
"""
import subprocess
import sys

if __name__ == "__main__":
    print("🚀 Starting Backend Server from HomeTheaterLive/backend ...")
    # Run uvicorn from backend directory
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])
