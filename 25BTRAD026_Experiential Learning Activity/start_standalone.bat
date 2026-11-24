@echo off
setlocal
set "ROOT=%~dp0"

echo.
echo ============================================================
echo   StudyVerse Offline (Standalone App - No Backend Needed)
echo ============================================================
echo.
echo Starting standalone Streamlit on http://localhost:8501 ...

start "StudyVerse Standalone" /D "%ROOT%studyverse_offline" "%ROOT%backend\.venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 --server.headless false

echo.
echo Opened in your browser: http://localhost:8501
pause
