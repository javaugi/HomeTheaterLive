# run_servers.py
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

def run_backend():
    """Run backend server - returns Popen object"""
    print("🚀 Starting Backend Server...")
    proc = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ], cwd=Path(__file__).parent)
    return proc

def run_mobile():
    """Run mobile server - returns Popen object"""
    print("📱 Starting Mobile Server...")
    # Wait a bit for backend to initialize
    time.sleep(2)

    proc = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8001",
        "--reload"
    ], cwd=Path(__file__).parent)
    return proc

def check_ports():
    """Check if ports are available"""
    import socket

    def port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(('localhost', port)) == 0

    print("🔍 Checking ports...")
    if port_in_use(8000):
        print("❌ Port 8000 is already in use!")
        return False

    if port_in_use(8001):
        print("❌ Port 8001 is already in use!")
        return False

    print("✅ Ports 8000 and 8001 are available")
    return True

def print_server_info():
    """Print server information"""
    print("\n" + "="*60)
    print("🏠 HomeTheaterLive Servers")
    print("="*60)
    print("   Backend API:  http://localhost:8000")
    print("   API Docs:     http://localhost:8000/docs")
    print("   Mobile API:   http://localhost:8001")
    print("   Mobile Docs:  http://localhost:8001/docs")
    print("="*60)
    print("\n📋 Press Ctrl+C to stop all servers")
    print("="*60 + "\n")

def main():
    print("Main function to run both servers")

    if not check_ports():
        print("\n⚠️  Please free up ports 8000 and 8001 before continuing.")
        sys.exit(1)

    processes = []

    try:
        # Start backend
        print("\n" + "-"*40)
        backend_proc = run_backend()
        processes.append(backend_proc)

        # Give backend time to start
        print("⏳ Waiting for backend to initialize...")
        time.sleep(3)

        # Start mobile
        print("\n" + "-"*40)
        mobile_proc = run_mobile()
        processes.append(mobile_proc)

        # Wait a moment for mobile to start
        time.sleep(2)

        # Print server info
        print_server_info()

        # Monitor processes
        while True:
            all_running = True

            # Check if any process has died
            for i, proc in enumerate(processes):
                if proc.poll() is not None:  # Process has terminated
                    server_name = "Backend" if i == 0 else "Mobile"
                    print(f"❌ {server_name} server stopped unexpectedly (exit code: {proc.returncode})")
                    all_running = False

            if not all_running:
                print("⚠️  One or more servers stopped. Shutting down...")
                break

            time.sleep(2)  # Check every 2 seconds

    except KeyboardInterrupt:
        print("\n\n🛑 Received shutdown signal...")

    finally:
        # Cleanup all processes
        print("\n" + "="*60)
        print("🧹 Cleaning up processes...")

        for i, proc in enumerate(processes):
            if proc and proc.poll() is None:  # Process is still running
                server_name = "Backend" if i == 0 else "Mobile"
                print(f"  Stopping {server_name} server...")

                # Try graceful shutdown first
                proc.terminate()

                # Wait for termination
                try:
                    proc.wait(timeout=5)
                    print(f"  ✅ {server_name} server stopped gracefully")
                except subprocess.TimeoutExpired:
                    print(f"  ⚠️  {server_name} server not responding, forcing kill...")
                    proc.kill()
                    proc.wait()
                    print(f"  ✅ {server_name} server killed")

        print("\n✅ All servers stopped.")
        print("="*60)

if __name__ == "__main__":
    print("Starting up both servers main entered ...")
    main()