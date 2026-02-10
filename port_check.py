# utils/port_check.py
import socket
import psutil

def check_port(port):
    """Check if port is in use and by what process"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('localhost', port)) == 0:
            print(f"Port {port} is in use!")
            
            # Try to find the process
            try:
                for conn in psutil.net_connections():
                    if conn.laddr.port == port:
                        proc = psutil.Process(conn.pid)
                        print(f"  Process: {proc.name()} (PID: {proc.pid})")
                        print(f"  Command: {' '.join(proc.cmdline())}")
                        return proc
            except:
                print("  Could not identify process")
            return True
        else:
            print(f"Port {port} is available")
            return False

if __name__ == "__main__":
    print("Checking ports...")
    check_port(8000)
    check_port(8001)# -*- coding: utf-8 -*-

"""
Solution 2: Check & Kill Process Using Port 8000
Windows:
bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F

# Or use PowerShell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess
Stop-Process -Id <PID> -Force
Linux/Mac:
bash
# Find process using port 8000
sudo lsof -i :8000

# Kill the process
kill -9 <PID>

# Or find and kill in one command
sudo kill -9 $(sudo lsof -t -i:8000)
"""