@echo off
REM Quick Start Script for Windows
REM Fake News Detection System

echo ============================================================
echo FAKE NEWS DETECTION - QUICK START (Windows)
echo ============================================================
echo.

REM Check if .env exists
if not exist .env (
    echo [WARNING] .env file not found
    echo Creating .env from .env.example...
    copy .env.example .env
    echo [SUCCESS] Created .env file
    echo.
    echo [IMPORTANT] Edit .env file with your credentials before continuing
    echo    - SUPABASE_URL
    echo    - SUPABASE_KEY
    echo    - GNEWS_API_KEY
    echo.
    pause
)

REM Check Python
echo Checking Python version...
python --version
echo.

REM Create virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    echo [SUCCESS] Virtual environment created
) else (
    echo [SUCCESS] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo [SUCCESS] Virtual environment activated
echo.

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
echo [SUCCESS] Dependencies installed
echo.

REM Download models
echo ============================================================
echo DOWNLOADING MODELS FROM HUGGING FACE
echo ============================================================
echo.
echo This will download 3 models (~2GB total):
echo   - DistilBERT (66M parameters)
echo   - RoBERTa (125M parameters)
echo   - XLNet (110M parameters)
echo.
set /p download="Continue with model download? (y/n): "

if /i "%download%"=="y" (
    python scripts\download_models.py
    echo.
) else (
    echo [WARNING] Skipping model download
    echo    You can download models later with: python scripts\download_models.py
    echo.
)

REM Test connections
echo ============================================================
echo TESTING CONNECTIONS
echo ============================================================
echo.
python scripts\test_connections.py
echo.

REM Summary
echo ============================================================
echo SETUP COMPLETE
echo ============================================================
echo.
echo Next steps:
echo.
echo 1. Start the API server:
echo    uvicorn src.api.main:app --reload
echo.
echo 2. Test the API:
echo    curl http://localhost:8000
echo.
echo 3. View API docs:
echo    http://localhost:8000/docs
echo.
echo 4. Fine-tune models (optional):
echo    python src\models\train.py
echo.
echo ============================================================
pause
