1. run create-app-win
2. To run your application, type:
    $ cd myhometheater
    $ briefcase dev
3. Python pip related
    See this message but got upgrade error
    [notice] A new release of pip is available: 25.2 -> 25.3
    [notice] To update, run: python.exe -m pip install --upgrade pip

    $ python.exe -m pip install --upgrade pip
    Defaulting to user installation because normal site-packages is not writeable
    Requirement already satisfied: pip in c:\users\javau\appdata\local\packages\pythonsoftwarefoundation.python.3.13_qbz5n2kfra8p0\localcache\local-packages\python313\site-packages (25.3)

(1). Check the actual pip version first:
    python.exe -m pip --version 
(2). Clear the pip cache if needed:
    python.exe -m pip cache purge  
(3). If you still see the notice, try these options:
    Option A: Force reinstall pip:
        python.exe -m pip install --upgrade --force-reinstall pip
    Option B: Use pip to upgrade itself with --no-cache-dir:
        python.exe -m pip install --upgrade pip --no-cache-dir
    Option C: Run as administrator (if you have admin rights):
        python.exe -m pip install --upgrade pip
(4). Check if you have multiple Python installations:    
    where python or where python.exe

    $ where python
    C:\Users\javau\AppData\Local\Microsoft\WindowsApps\python.exe
(5). For Windows 11 specifically, you might want to:
    Disable Windows Defender temporarily (sometimes it blocks pip updates)
    Try using the --user flag explicitly:
        python -m pip install --upgrade pip --user
(6). If all else fails, try the get-pip.py method:
    Download: https://bootstrap.pypa.io/get-pip.py
    python.exe get-pip.py --user

4. briefcase related
    briefcase dev 
    bash: briefcase: command not found
(1). Install Briefcase:
    Using pip (install it for your user):
        python.exe -m pip install briefcase
    Or if you prefer to install it globally (requires admin):
        python.exe -m pip install --user briefcase
(2). If installed but not found, check these:
    Add Python Scripts to PATH:
    The Briefcase executable is likely in:
    C:\Users\javau\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts\    
(3). Verify installation:
    python.exe -m pip show briefcase
    This should show that Briefcase is installed.
(4). For Bash on Windows (WSL/Git Bash):
If you're using Git Bash or WSL, you might need to:
Install Briefcase in the Windows Python (not WSL Python)
Use the Windows Python executable:

bash
/c/Users/javau/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/LocalCache/local-packages/Python313/Scripts/briefcase.exe dev

add the following to C:\Program Files\Git\etc\bash.bashrc
export PATH=$PATH:"/c/Users/javau/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/LocalCache/local-packages/Python313/Scripts"

(5). Common Briefcase commands after installation: Once installed, you can use:
    briefcase --help
    briefcase new              # Create a new project
    briefcase dev              # Run in development mode
    briefcase create           # Create app packaging
    briefcase build            # Build the app
    briefcase run              # Run the packaged app

    Quick fix: The easiest solution is usually:
        python.exe -m briefcase dev
    This runs Briefcase as a Python module, bypassing PATH issues.
5. import toga, time, jwt
ModuleNotFoundError: No module named 'jwt'
(1). pip install pyjwt or pip install PyJWT or pip install python-jwt
(2) If you need support for digital signature algorithms like RSA or ECDSA, you should install the optional cryptography dependency:

pip install "PyJWT[crypto]"

(2) check 
python --version
pip --version
pip list | grep -i jwt

6. pip install python-multipart - needed from backend