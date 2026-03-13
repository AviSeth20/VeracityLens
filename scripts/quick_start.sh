#!/bin/bash

# Quick Start Script for Fake News Detection System
# This script automates the setup process

set -e  # Exit on error

echo "============================================================"
echo "FAKE NEWS DETECTION - QUICK START"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env file with your credentials before continuing${NC}"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_KEY"
    echo "   - GNEWS_API_KEY"
    echo ""
    read -p "Press Enter after you've updated .env file..."
fi

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python $python_version${NC}"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Download models
echo "============================================================"
echo "DOWNLOADING MODELS FROM HUGGING FACE"
echo "============================================================"
echo ""
echo "This will download 3 models (~2GB total):"
echo "  - DistilBERT (66M parameters)"
echo "  - RoBERTa (125M parameters)"
echo "  - XLNet (110M parameters)"
echo ""
read -p "Continue with model download? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    python scripts/download_models.py
    echo ""
else
    echo -e "${YELLOW}⚠️  Skipping model download${NC}"
    echo "   You can download models later with: python scripts/download_models.py"
    echo ""
fi

# Test connections
echo "============================================================"
echo "TESTING CONNECTIONS"
echo "============================================================"
echo ""
python scripts/test_connections.py
echo ""

# Summary
echo "============================================================"
echo "SETUP COMPLETE"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Start the API server:"
echo "   uvicorn src.api.main:app --reload"
echo ""
echo "2. Test the API:"
echo "   curl http://localhost:8000"
echo ""
echo "3. View API docs:"
echo "   http://localhost:8000/docs"
echo ""
echo "4. Fine-tune models (optional):"
echo "   python src/models/train.py"
echo ""
echo "============================================================"
