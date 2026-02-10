@echo off
call C:\ProgramData\anaconda3\Scripts\activate.bat
conda env create -f ..\environments\environment-backend.yml
pause
