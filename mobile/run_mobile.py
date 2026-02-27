#!/usr/bin/env python
"""
run_mobile.py - Run Mobile Toga app from HomeTheaterLive/mobile directory
"""

if __name__ == "__main__":
    print("🚀 Starting Mobile Toga App from HomeTheaterLive/mobile ...")
    import subprocess
    import sys

    # Option 1: Run the main Python file directly
    # mobile_main = Path(__file__).parent / "app" / "main.py"
    # proc = subprocess.Popen([
    #     sys.executable, str(mobile_main)
    # ])

    # Option 2: If it's a Briefcase app, you might need:
    # proc = subprocess.Popen([
    #     sys.executable, "-m", "briefcase", "run"
    # ], cwd=Path(__file__).parent)

    # Run uvicorn from backend directory
    subprocess.run([
        sys.executable, "-m", "briefcase", "dev"
    ])
