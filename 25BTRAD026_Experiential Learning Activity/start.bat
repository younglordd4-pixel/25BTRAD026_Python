@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"

echo.
echo ============================================================
echo   StudyVerse Offline - Launching Application
echo ============================================================
echo.

echo [1/2] Starting FastAPI backend on http://127.0.0.1:8000 ...
start "StudyVerse Backend" /D "%ROOT%backend" "%ROOT%backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir "%ROOT%backend" --host 127.0.0.1 --port 8000 --reload

echo [2/2] Loading AI models and initializing backend (approx. 5 seconds)...
ping 127.0.0.1 -n 6 > nul

echo Starting Streamlit web interface on http://localhost:8501 ...
start "StudyVerse UI" /D "%ROOT%" "%ROOT%backend\.venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 --server.headless false

timeout /t 3 > nul
start http://localhost:8501

echo.
echo ============================================================
echo   StudyVerse is now active!
echo.
echo   - Web Interface: http://localhost:8501
echo   - Backend API:   http://127.0.0.1:8000
echo   - API Swagger:   http://127.0.0.1:8000/docs
echo.
echo   Keep this window and the two spawned terminal windows open.
echo   Close them when you want to stop the application.
echo ============================================================
echo.
pause
