@echo off
REM ============================================================
REM Fake News Detection - Environment Setup Script
REM This script creates virtual environment and installs all dependencies
REM ============================================================

echo.
echo ============================================================
echo FAKE NEWS DETECTION - ENVIRONMENT SETUP
echo ============================================================
echo.

REM Check if Python is installed
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://www.python.org/
    pause
    exit /b 1
)

python --version
echo [SUCCESS] Python is installed
echo.

REM Check if virtual environment already exists
if exist venv (
    echo [WARNING] Virtual environment already exists
    set /p recreate="Do you want to recreate it? (y/n): "
    if /i "%recreate%"=="y" (
        echo [2/5] Removing existing virtual environment...
        rmdir /s /q venv
        echo [SUCCESS] Removed existing virtual environment
    ) else (
        echo [INFO] Using existing virtual environment
        goto :activate_venv
    )
)

REM Create virtual environment
echo [2/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    echo Make sure you have venv module installed
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment created
echo.

:activate_venv
REM Activate virtual environment
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment activated
echo.

REM Upgrade pip
echo [4/5] Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip, continuing anyway...
) else (
    echo [SUCCESS] Pip upgraded
)
echo.

REM Install requirements
echo [5/5] Installing dependencies from requirements.txt...
echo This may take a few minutes...
echo.

pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install some dependencies
    echo Please check the error messages above
    echo.
    echo Common solutions:
    echo 1. Make sure you have internet connection
    echo 2. Try running as administrator
    echo 3. Check if requirements.txt exists
    echo 4. Install Visual C++ Build Tools if needed
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo INSTALLATION COMPLETE
echo ============================================================
echo.
echo [SUCCESS] All dependencies installed successfully!
echo.
echo Virtual environment location: %CD%\venv
echo Python version: 
python --version
echo.
echo Installed packages:
pip list --format=columns | findstr /C:"torch" /C:"transformers" /C:"fastapi" /C:"supabase"
echo.
echo ============================================================
echo NEXT STEPS
echo ============================================================
echo.
echo 1. Virtual environment is already activated
echo.
echo 2. Download models from Hugging Face:
echo    python scripts\download_models.py
echo.
echo 3. Setup Supabase database:
echo    - Open Supabase dashboard
echo    - Run scripts\setup_supabase.sql in SQL Editor
echo.
echo 4. Test connections:
echo    python scripts\test_connections.py
echo.
echo 5. Start the API server:
echo    uvicorn src.api.main:app --reload
echo.
echo ============================================================
echo.
echo To activate virtual environment in future sessions:
echo    venv\Scripts\activate
echo.
echo To deactivate:
echo    deactivate
echo.
echo ============================================================
echo.
pause
