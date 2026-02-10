@echo off
call C:\ProgramData\anaconda3\Scripts\activate.bat
conda activate htl-backend
uvicorn backend.app.main:app --reload
