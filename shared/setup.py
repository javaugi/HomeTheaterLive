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
├── pyproject.toml
├── src/
│   ├── shared/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   └── core/
│   │   │       ├── __init__.py
│   │   │       └── config.py
│   └── mobile/
│       ├── __init__.py
│       └── config.py
└── .env

Solution 1: Install Shared Module as Editable Package (Recommended): shared/setup.py
# From project root
pip install -e ./shared

Solution 2: Modify Python Path at Runtime: see # backend/app/main.py (or your entry point)
Solution 3: Use Relative Imports with Package Structure: see the file structure above
Solution 4: Quick Fix - Use Absolute Import Path: see # backend/app/core/config.py
"""

