@echo off
REM ============================================================
REM Fake News Detection - Environment Setup
REM Run from project root: scripts\setup_environment.bat
REM ============================================================

REM Move to project root (one level up from scripts/)
cd /d "%~dp0.."

echo.
echo ============================================================
echo FAKE NEWS DETECTION - ENVIRONMENT SETUP
echo ============================================================
echo.

REM Check Python
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from https://www.python.org/
    pause & exit /b 1
)
python --version
echo.

REM Handle existing venv
if exist venv (
    echo [INFO] Virtual environment already exists.
    set /p recreate="Recreate it? (y/n): "
    if /i "%recreate%"=="y" (
        echo Removing old venv...
        rmdir /s /q venv
    ) else (
        goto :activate_venv
    )
)

REM Create venv
echo [2/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 ( echo [ERROR] Failed to create venv & pause & exit /b 1 )
echo [OK] venv created at %CD%\venv
echo.

:activate_venv
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 ( echo [ERROR] Failed to activate venv & pause & exit /b 1 )
echo [OK] Activated
echo.

REM Upgrade pip
echo [4/5] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip upgraded
echo.

REM Install requirements
echo [5/5] Installing requirements.txt...
echo (This takes a few minutes on first run)
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Some packages failed. Common fixes:
    echo   - Run as Administrator
    echo   - Install Visual C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo   - Check internet connection
    pause & exit /b 1
)

echo.
echo ============================================================
echo DONE - Virtual environment ready
echo ============================================================
echo.
echo Location : %CD%\venv
python --version
echo.
echo Key packages installed:
pip list --format=columns | findstr /C:"torch" /C:"transformers" /C:"fastapi" /C:"supabase" /C:"wandb"
echo.
echo ============================================================
echo NEXT STEPS
echo ============================================================
echo.
echo 1. Download base models (run once):
echo    python scripts\download_models.py
echo.
echo 2. Run Supabase SQL schema:
echo    Open Supabase dashboard ^> SQL Editor ^> paste scripts\setup_supabase.sql
echo.
echo 3. Test connections:
echo    python scripts\test_connections.py
echo.
echo 4. Start API:
echo    uvicorn src.api.main:app --reload
echo.
echo To activate venv in future sessions:
echo    venv\Scripts\activate
echo.
pause
