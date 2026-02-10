# shared/setup.py
from setuptools import setup, find_packages

setup(
    name="hometheaterlive-shared",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0",
        "pydantic-settings>=2.0",
    ],
)

"""
hometheaterlive/
├── backend/
│   ├── app/
│   │   ├── core/          # Config, dependencies
│   │   ├── api/           # API endpoints
│   │   ├── models/
│   │   ├── services/
│   │   ├── db/
│   │   └── main.py        # FastAPI app
│   └── requirements.txt
├── mobile/
│   ├── app/               # Changed from src/myapp/
│   │   ├── core/          # Mobile config
│   │   ├── ui/            # Kivy UI components
│   │   ├── services/      # Mobile services (cache, auth, etc.)
│   │   ├── api/           # API client for backend
│   │   └── main.py        # Kivy app entry point
│   ├── mobile_api/        # Optional: FastAPI server for mobile
│   │   ├── app/
│   │   │   └── main.py
│   │   └── requirements.txt
│   └── requirements.txt
└── shared/
    ├── config/
    └── utils/

Solution 1: Install Shared Module as Editable Package (Recommended): shared/setup.py
# From project root
pip install -e ./shared

Solution 2: Modify Python Path at Runtime: see # backend/app/main.py (or your entry point)
Solution 3: Use Relative Imports with Package Structure: see the file structure above
Solution 4: Quick Fix - Use Absolute Import Path: see # backend/app/core/config.py
"""

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