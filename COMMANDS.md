# Command Reference

Quick reference for all commands in the Fake News Detection project.

---

## Setup Commands

### Initial Setup

```bash
# Automated setup (recommended)
./scripts/quick_start.sh          # Unix/macOS
scripts\quick_start.bat           # Windows

# Manual setup
python -m venv venv
source venv/bin/activate          # Unix/macOS
venv\Scripts\activate             # Windows
pip install -r requirements.txt
```

### Download Models

```bash
# Download all models (DistilBERT, RoBERTa, XLNet)
python scripts/download_models.py

# Check downloaded models
ls -la models/                    # Unix/macOS
dir models\                       # Windows
```

### Database Setup

```bash
# Run in Supabase SQL Editor
# Copy contents from: scripts/setup_supabase.sql
```

### Test Connections

```bash
# Test Supabase and GNews API
python scripts/test_connections.py
```

---

## Running the Application

### Start API Server

```bash
# Development mode (auto-reload)
uvicorn src.api.main:app --reload

# Production mode
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# With custom port
uvicorn src.api.main:app --port 8080 --reload
```

### Start Frontend (when ready)

```bash
cd frontend
npm install
npm run dev
```

---

## API Testing Commands

### Health Check

```bash
curl http://localhost:8000
curl http://localhost:8000/health
```

### Make Prediction

```bash
# Predict with text
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"text": "Your news article text here", "model": "distilbert"}'

# Predict with URL
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "model": "roberta"}'
```

### Fetch News

```bash
# Search news
curl "http://localhost:8000/news?query=politics&max_results=10"

# Get top headlines
curl "http://localhost:8000/news?category=technology&max_results=5"

# Analyze recent news
curl "http://localhost:8000/news/analyze?topic=breaking%20news&max_articles=5"
```

### Submit Feedback

```bash
curl -X POST "http://localhost:8000/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": "abc-123",
    "predicted_label": "True",
    "actual_label": "Fake",
    "user_comment": "This was misinformation"
  }'
```

### Get Statistics

```bash
curl http://localhost:8000/stats
```

### List Models

```bash
curl http://localhost:8000/models
```

---

## Model Training Commands

### Train Model

```bash
# Train with default settings
python src/models/train.py

# Train specific model
python src/models/train.py --model distilbert

# Train with custom parameters
python src/models/train.py \
  --model roberta \
  --epochs 5 \
  --batch-size 16 \
  --learning-rate 2e-5
```

### Evaluate Model

```bash
python src/models/evaluate.py --model distilbert
```

---

## Data Processing Commands

### Clean Dataset

```bash
# Run Jupyter notebook
jupyter notebook src/data/Dataset_Cleaning.ipynb

# Or use JupyterLab
jupyter lab src/data/Dataset_Cleaning.ipynb
```

### Preprocess Data

```bash
python src/data/preprocessing.py
```

---

## Testing Commands

### Run All Tests

```bash
pytest

# With coverage
pytest --cov=src tests/

# Verbose output
pytest -v

# Run specific test file
pytest tests/test_preprocessing.py

# Run specific test
pytest tests/test_preprocessing.py::test_clean_text_removes_urls
```

### Run Connection Tests

```bash
python scripts/test_connections.py
```

---

## Docker Commands

### Build and Run

```bash
# Build image
docker build -t fake-news-detection .

# Run container
docker run -p 8000:8000 fake-news-detection

# Run with environment file
docker run --env-file .env -p 8000:8000 fake-news-detection
```

### Docker Compose

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild
docker-compose up --build
```

---

## Database Commands (Supabase)

### Using Supabase CLI (optional)

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link project
supabase link --project-ref your-project-ref

# Run migrations
supabase db push

# Generate types
supabase gen types typescript --local > src/types/database.ts
```

### Direct SQL Queries

```bash
# Connect via psql (get connection string from Supabase)
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"

# Example queries
SELECT COUNT(*) FROM predictions;
SELECT predicted_label, COUNT(*) FROM predictions GROUP BY predicted_label;
SELECT * FROM feedback ORDER BY created_at DESC LIMIT 10;
```

---

## Git Commands

### Initial Commit

```bash
git init
git add .
git commit -m "Initial commit: Fake news detection system"
git branch -M main
git remote add origin https://github.com/your-username/fake-news-detection.git
git push -u origin main
```

### Regular Workflow

```bash
# Create feature branch
git checkout -b feature/add-xlnet-support

# Stage changes
git add .

# Commit
git commit -m "feat: add XLNet model support"

# Push
git push origin feature/add-xlnet-support

# Merge to main
git checkout main
git merge feature/add-xlnet-support
git push origin main
```

---

## Environment Management

### Virtual Environment

```bash
# Create
python -m venv venv

# Activate
source venv/bin/activate          # Unix/macOS
venv\Scripts\activate             # Windows

# Deactivate
deactivate

# Delete
rm -rf venv                       # Unix/macOS
rmdir /s venv                     # Windows
```

### Dependencies

```bash
# Install all
pip install -r requirements.txt

# Install specific package
pip install transformers

# Update requirements
pip freeze > requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt
```

---

## Monitoring & Logs

### View API Logs

```bash
# API logs (when running with uvicorn)
# Logs appear in terminal

# Save logs to file
uvicorn src.api.main:app --log-config logging.conf > api.log 2>&1
```

### Monitor Supabase

```bash
# View in Supabase Dashboard
# https://app.supabase.com/project/[PROJECT]/logs

# Query logs
SELECT * FROM predictions ORDER BY created_at DESC LIMIT 100;
```

---

## Cleanup Commands

### Clean Python Cache

```bash
# Remove __pycache__
find . -type d -name __pycache__ -exec rm -r {} +    # Unix/macOS
for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"    # Windows

# Remove .pyc files
find . -name "*.pyc" -delete      # Unix/macOS
del /s /q *.pyc                   # Windows
```

### Clean Models (to re-download)

```bash
rm -rf models/*                   # Unix/macOS
rmdir /s /q models                # Windows
```

### Reset Database

```bash
# Run in Supabase SQL Editor
DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS news_articles CASCADE;
DROP TABLE IF EXISTS model_performance CASCADE;

# Then re-run setup_supabase.sql
```

---

## Deployment Commands

### Deploy to Render

```bash
# Connect GitHub repo in Render dashboard
# Or use Render CLI
render deploy
```

### Deploy to Vercel (Frontend)

```bash
cd frontend
vercel
```

### Deploy to Railway

```bash
railway login
railway init
railway up
```

---

## Useful Aliases (Optional)

Add to your `.bashrc` or `.zshrc`:

```bash
# API shortcuts
alias api-start="uvicorn src.api.main:app --reload"
alias api-test="python scripts/test_connections.py"

# Model shortcuts
alias models-download="python scripts/download_models.py"
alias models-train="python src/models/train.py"

# Testing shortcuts
alias test-all="pytest"
alias test-cov="pytest --cov=src tests/"

# Docker shortcuts
alias dc-up="docker-compose up"
alias dc-down="docker-compose down"
alias dc-logs="docker-compose logs -f"
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│  FAKE NEWS DETECTION - QUICK COMMANDS                   │
├─────────────────────────────────────────────────────────┤
│  Setup:                                                  │
│    ./scripts/quick_start.sh                             │
│    python scripts/download_models.py                    │
│    python scripts/test_connections.py                   │
│                                                          │
│  Run:                                                    │
│    uvicorn src.api.main:app --reload                    │
│                                                          │
│  Test:                                                   │
│    curl http://localhost:8000                           │
│    pytest                                                │
│                                                          │
│  Docs:                                                   │
│    http://localhost:8000/docs                           │
└─────────────────────────────────────────────────────────┘
```

---

For more details, see:

- [QUICK_START.md](QUICK_START.md) - Getting started guide
- [README_SETUP.md](README_SETUP.md) - Detailed setup instructions
- [README.md](README.md) - Project overview
