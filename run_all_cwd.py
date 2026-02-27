#!/usr/bin/env python
import subprocess
import sys
import time
import os
import signal
from pathlib import Path


"""
Development launcher for HomeTheaterLive
Starts both backend server and mobile UI
"""


# Get the project root directory
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
MOBILE_DIR = PROJECT_ROOT / "mobile"

# Store processes for cleanup
processes = []


def run_backend():
    """Start the backend FastAPI server"""
    print("🚀 Starting Backend Server...")
    proc = subprocess.Popen(
        [sys.executable, "run_backend.py"],
        cwd=BACKEND_DIR,
        env={**os.environ, "PYTHONPATH": str(BACKEND_DIR)}
    )
    return ("Backend", proc)


def run_mobile_ui():
    """Start the mobile UI (Toga app)"""
    print("📱 Starting Mobile UI...")
    # Run the mobile app main.py directly
    """
    mobile_main = MOBILE_DIR / "app" / "main.py"
    
    if not mobile_main.exists():
        print(f"❌ Mobile main.py not found at {mobile_main}")
        # Try alternative locations
        mobile_main = MOBILE_DIR / "src" / "app" / "main.py"
        
    proc = subprocess.Popen(
        [sys.executable, str(mobile_main)],
        cwd=MOBILE_DIR,
        env={**os.environ, "PYTHONPATH": str(MOBILE_DIR)}
    )
    """
    proc = subprocess.Popen(
        [sys.executable, "run_mobile.py"],
        cwd=MOBILE_DIR,
        env={**os.environ, "PYTHONPATH": str(MOBILE_DIR)}
    )

    return ("Mobile UI", proc)

def kill_process_on_port(port):
    """Kill process running on specified port"""
    print(f"🔍 kill_process_on_port Checking port {port}...")

    system = sys.platform

    try:
        if system == "win32":  # Windows
            # Find PID using netstat
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True,
                capture_output=True,
                text=True
            )

            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if f':{port}' in line:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            print(f"  Found process with PID: {pid}")
                            # Kill the process
                            subprocess.run(
                                f'taskkill /F /PID {pid}', shell=True)
                            print(f"  ✅ Killed process {pid} on port {port}")

        else:  # Linux/Mac
            # Find PID using lsof
            result = subprocess.run(
                f'lsof -ti :{port}',
                shell=True,
                capture_output=True,
                text=True
            )

            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        print(f"  Found process with PID: {pid}")
                        # Kill the process
                        subprocess.run(f'kill -9 {pid}', shell=True)
                        print(f"  ✅ Killed process {pid} on port {port}")
            else:
                print(f"  ✅ No process found on port {port}")

    except Exception as e:
        print(f"  ❌ Error kill_process_on_port {port}: {e}")


def check_port(port):
    """Check if a port is available"""
    print(f"🔍 check_port Checking port {port}...")
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('localhost', port)) != 0


def wait_for_backend(timeout=10):
    """Wait for backend to be ready"""
    import requests
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get("http://localhost:8000/api/v1/health")
            if response.status_code == 200:
                print("✅ Backend is ready!")
                return True
        except:
            pass
        time.sleep(0.5)
    return False


def print_status():
    """Print status of all services"""
    print("\n" + "="*60)
    print("🏠 HomeTheaterLive Development Environment")
    print("="*60)
    print("   Backend API:  http://localhost:8000")
    print("   Backend Docs: http://localhost:8000/docs")
    print("   Mobile UI:    Running in separate window")
    print("="*60)
    print("\n📋 Press Ctrl+C to stop all services")
    print("="*60 + "\n")


def cleanup(signum=None, frame=None):
    """Clean up all processes on exit"""
    print("\n\n🛑 Shutting down services...")

    for name, proc in processes:
        if proc and proc.poll() is None:
            print(f"  Stopping {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
                print(f"  ✅ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"  ⚠️  {name} not responding, forcing...")
                proc.kill()
                proc.wait()
                print(f"  ✅ {name} killed")

    print("\n✅ All services stopped.")
    sys.exit(0)


def main():
    """Main function"""
    print("🔧 HomeTheaterLive Development Launcher")
    print("-" * 40)

    """
    print("🔧 HomeTheaterLive Development Launcher checking port 8000")
    # Check if ports are available
    if not check_port(8000):
        print("❌ Port 8000 is already in use!")
        # print("   Please free up port 8000 and try again.")
        # sys.exit(1)
        kill_process_on_port(8000)

    print("🔧 HomeTheaterLive Development Launcher checking port 8001")
    # Check if ports are available
    if not check_port(8001):
        print("❌ Port 8001 is already in use!")
        # print("   Please free up port 8000 and try again.")
        # sys.exit(1)
        kill_process_on_port(8001)
    """


    print("🔧 HomeTheaterLive Development Launcher checking ports 8000, 8001 ...")
    # Kill processes on ports 8000 and 8001
    kill_process_on_port([8000, 8001])
    time.sleep(1)


    # Register cleanup handler
    print("🔧 HomeTheaterLive Development Launcher Register cleanup handler ...")
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        # Start backend
        print("\n HomeTheaterLive Development Launcher adding run_backend ... " + "-" * 40)
        processes.append(run_backend())

        # Wait for backend to initialize
        print("⏳ Waiting for backend to be ready...")
        if not wait_for_backend():
            print("❌ Backend failed to start properly")
            cleanup()
            return

        # Start mobile UI
        print("\n HomeTheaterLive Development Launcher adding run_mobile_ui ... " + "-" * 40)
        print("\n" + "-" * 40)
        processes.append(run_mobile_ui())

        # Print status
        print_status()

        # Keep running until interrupted
        while True:
            # Check if any process died
            all_running = True
            for name, proc in processes:
                if proc.poll() is not None:
                    print(
                        f"❌ {name} stopped unexpectedly (code: {proc.returncode})")
                    all_running = False

            if not all_running:
                print("⚠️  One or more services stopped. Shutting down...")
                cleanup()
                break

            time.sleep(2)

    except KeyboardInterrupt as e:
        print(f"❌ Error running main with KeyboardInterrupt : {e}")
        cleanup()
    except Exception as e:
        print(f"❌ Error running main with Exception : {e}")
        cleanup()


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == "__main__":
    clear_screen()
    print("Screen cleared! Starting servers ...")
    main()  # -*- coding: utf-8 -*-
