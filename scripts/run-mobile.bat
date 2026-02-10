@echo off
call C:\ProgramData\anaconda3\Scripts\activate.bat
conda activate htl-mobile
uvicorn mobile.app.main:app --reload
