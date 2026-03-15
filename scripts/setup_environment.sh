#!/bin/bash
# ============================================================
# Fake News Detection - Environment Setup Script
# This script creates virtual environment and installs all dependencies
# ============================================================

set -e  # Exit on error

echo ""
echo "============================================================"
echo "FAKE NEWS DETECTION - ENVIRONMENT SETUP"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
echo "[1/5] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}[ERROR] Python is not installed${NC}"
        echo "Please install Python 3.9 or higher"
        exit 1
    else
        PYTHON_CMD=python
    fi
else
    PYTHON_CMD=python3
fi

$PYTHON_CMD --version
echo -e "${GREEN}[SUCCESS] Python is installed${NC}"
echo ""

# Check if virtual environment already exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}[WARNING] Virtual environment already exists${NC}"
    read -p "Do you want to recreate it? (y/n): " recreate
    if [[ $recreate =~ ^[Yy]$ ]]; then
        echo "[2/5] Removing existing virtual environment..."
        rm -rf venv
        echo -e "${GREEN}[SUCCESS] Removed existing virtual environment${NC}"
    else
        echo "[INFO] Using existing virtual environment"
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[2/5] Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}[SUCCESS] Virtual environment created${NC}"
    echo ""
else
    echo "[2/5] Virtual environment already exists"
    echo ""
fi

# Activate virtual environment
echo "[3/5] Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}[SUCCESS] Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "[4/5] Upgrading pip..."
pip install --upgrade pip --quiet
echo -e "${GREEN}[SUCCESS] Pip upgraded${NC}"
echo ""

# Install requirements
echo "[5/5] Installing dependencies from requirements.txt..."
echo "This may take a few minutes..."
echo ""

if pip install -r requirements.txt; then
    echo ""
    echo "============================================================"
    echo "INSTALLATION COMPLETE"
    echo "============================================================"
    echo ""
    echo -e "${GREEN}[SUCCESS] All dependencies installed successfully!${NC}"
    echo ""
    echo "Virtual environment location: $(pwd)/venv"
    echo "Python version: $($PYTHON_CMD --version)"
    echo ""
    echo "Installed packages:"
    pip list | grep -E "torch|transformers|fastapi|supabase"
    echo ""
else
    echo ""
    echo -e "${RED}[ERROR] Failed to install some dependencies${NC}"
    echo "Please check the error messages above"
    echo ""
    echo "Common solutions:"
    echo "1. Make sure you have internet connection"
    echo "2. Check if requirements.txt exists"
    echo "3. Install build tools if needed"
    echo ""
    exit 1
fi

echo "============================================================"
echo "NEXT STEPS"
echo "============================================================"
echo ""
echo "1. Virtual environment is already activated"
echo ""
echo "2. Download models from Hugging Face:"
echo "   python scripts/download_models.py"
echo ""
echo "3. Setup Supabase database:"
echo "   - Open Supabase dashboard"
echo "   - Run scripts/setup_supabase.sql in SQL Editor"
echo ""
echo "4. Test connections:"
echo "   python scripts/test_connections.py"
echo ""
echo "5. Start the API server:"
echo "   uvicorn src.api.main:app --reload"
echo ""
echo "============================================================"
echo ""
echo "To activate virtual environment in future sessions:"
echo "   source venv/bin/activate"
echo ""
echo "To deactivate:"
echo "   deactivate"
echo ""
echo "============================================================"
echo ""
