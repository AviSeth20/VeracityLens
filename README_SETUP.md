# Setup Guide - Fake News Detection System

Complete setup instructions for downloading models and configuring backend services.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Download Models from Hugging Face](#download-models)
4. [Configure Supabase](#configure-supabase)
5. [Configure GNews API](#configure-gnews)
6. [Test Connections](#test-connections)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Git
- Internet connection (for downloading models)
- Supabase account (free tier)
- GNews API key (free tier)

---

## Environment Setup

### 1. Clone and Install Dependencies

```bash
# Navigate to project directory
cd fake-news-detection

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# Use your preferred text editor
```

---

## Download Models from Hugging Face

### Automatic Download (Recommended)

Run the download script to fetch all three models:

```bash
python scripts/download_models.py
```

This will download:

- **DistilBERT** (distilbert-base-uncased) - 66M parameters
- **RoBERTa** (roberta-base) - 125M parameters
- **XLNet** (xlnet-base-cased) - 110M parameters

**Expected output:**

```
============================================================
FAKE NEWS DETECTION - MODEL DOWNLOADER
============================================================

Project root: /path/to/fake-news-detection
Models directory: /path/to/fake-news-detection/models

Models to download: 3
  - distilbert: distilbert-base-uncased
  - roberta: roberta-base
  - xlnet: xlnet-base-cased

============================================================
Downloading: distilbert
Model: distilbert-base-uncased
Description: Lightweight BERT variant (66M parameters)
Save path: /path/to/models/distilbert
============================================================

[1/3] Downloading tokenizer...
✅ Tokenizer saved to /path/to/models/distilbert
[2/3] Downloading config...
✅ Config saved to /path/to/models/distilbert
[3/3] Downloading model (this may take a few minutes)...
✅ Model saved to /path/to/models/distilbert
✅ Successfully downloaded distilbert!

... (similar output for roberta and xlnet)

============================================================
DOWNLOAD SUMMARY
============================================================
distilbert      ✅ SUCCESS
roberta         ✅ SUCCESS
xlnet           ✅ SUCCESS

Total: 3/3 models downloaded successfully

🎉 All models downloaded successfully!

Models are saved in: /path/to/models

Next steps:
1. Fine-tune models on your dataset using src/models/train.py
2. Update API to load models from models/ directory
3. Test predictions with the API
============================================================
```

### Manual Download (Alternative)

If the script fails, you can download models manually:

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# DistilBERT
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
model = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=4
)
tokenizer.save_pretrained("./models/distilbert")
model.save_pretrained("./models/distilbert")

# Repeat for roberta-base and xlnet-base-cased
```

### Verify Models

Check that models are downloaded:

```bash
ls -la models/
```

Expected structure:

```
models/
├── distilbert/
│   ├── config.json
│   ├── model.safetensors
│   ├── tokenizer_config.json
│   ├── vocab.txt
│   └── model_info.txt
├── roberta/
│   ├── config.json
│   ├── model.safetensors
│   ├── tokenizer_config.json
│   ├── vocab.json
│   ├── merges.txt
│   └── model_info.txt
└── xlnet/
    ├── config.json
    ├── model.safetensors
    ├── tokenizer_config.json
    ├── spiece.model
    └── model_info.txt
```

---

## Configure Supabase

### 1. Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up or log in
3. Click "New Project"
4. Fill in project details:
   - Name: `fake-news-detection`
   - Database Password: (save this securely)
   - Region: Choose closest to you
5. Wait for project to be created (~2 minutes)

### 2. Get API Credentials

1. In your Supabase dashboard, go to **Settings** → **API**
2. Copy the following:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJ...`)
   - **service_role key** (starts with `eyJ...`)

### 3. Update .env File

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here
```

### 4. Create Database Tables

1. In Supabase dashboard, go to **SQL Editor**
2. Click **New Query**
3. Copy contents of `scripts/setup_supabase.sql`
4. Paste and click **Run**

This creates:

- `predictions` table - stores model predictions
- `feedback` table - stores user feedback for active learning
- `news_articles` table - caches fetched news articles
- `model_performance` table - tracks model metrics
- Views for analytics
- Row Level Security policies

### 5. Verify Tables

Go to **Table Editor** in Supabase dashboard and verify these tables exist:

- predictions
- feedback
- news_articles
- model_performance
- user_sessions

---

## Configure GNews API

### 1. Get API Key

1. Go to [https://gnews.io](https://gnews.io)
2. Click **Get API Key** or **Sign Up**
3. Create a free account
4. Copy your API key from the dashboard

**Free Tier Limits:**

- 100 requests per day
- Access to articles from last 7 days
- Max 10 articles per request

### 2. Update .env File

```bash
GNEWS_API_KEY=your_gnews_api_key_here
GNEWS_API_URL=https://gnews.io/api/v4
```

### 3. Test API

```python
# Quick test in Python
from src.utils.gnews_client import get_gnews_client

client = get_gnews_client()
articles = client.search_news(query="technology", max_results=3)

for article in articles:
    print(f"Title: {article['title']}")
    print(f"Source: {article['source']}")
    print(f"URL: {article['url']}\n")
```

---

## Test Connections

Run the comprehensive test script:

```bash
python scripts/test_connections.py
```

**Expected output:**

```
============================================================
FAKE NEWS DETECTION - CONNECTION TESTS
============================================================

============================================================
Checking Environment Variables
============================================================
✅ SUPABASE_URL: https://xx...
✅ SUPABASE_KEY: eyJhbGciO...
✅ GNEWS_API_KEY: 1234567890...

============================================================
Testing Supabase Connection
============================================================
✅ Supabase client initialized successfully
✅ Successfully connected to Supabase
   URL: https://xxxxx.supabase.co
   Tables accessible: predictions, feedback, news_articles

============================================================
Testing GNews API Connection
============================================================
✅ GNews client initialized successfully
✅ Successfully fetched 3 articles from GNews
   API Key: 1234567890...
   Base URL: https://gnews.io/api/v4

   Sample article:
   - Title: Latest Technology Breakthrough...
   - Source: TechCrunch
   - Published: 2024-03-14T10:30:00Z

============================================================
TEST SUMMARY
============================================================
Environment Variables: ✅ PASS
Supabase Connection:   ✅ PASS
GNews API Connection:  ✅ PASS

🎉 All tests passed! Your backend is ready.

============================================================
```

---

## Troubleshooting

### Models Not Downloading

**Problem:** `ConnectionError` or timeout during download

**Solutions:**

1. Check internet connection
2. Try downloading one model at a time
3. Use a VPN if Hugging Face is blocked
4. Download manually and place in `models/` directory

### Supabase Connection Failed

**Problem:** `ValueError: SUPABASE_URL and SUPABASE_KEY must be set`

**Solutions:**

1. Verify `.env` file exists in project root
2. Check credentials are correct (no extra spaces)
3. Ensure you're using the `anon` key, not `service_role` for client
4. Restart your terminal/IDE after updating `.env`

**Problem:** `Table 'predictions' does not exist`

**Solutions:**

1. Run `scripts/setup_supabase.sql` in Supabase SQL Editor
2. Check for SQL errors in Supabase logs
3. Verify you're connected to the correct project

### GNews API Failed

**Problem:** `ValueError: GNEWS_API_KEY must be set`

**Solutions:**

1. Verify API key in `.env` file
2. Check key is valid at <https://gnews.io/dashboard>
3. Ensure no extra quotes around the key

**Problem:** `429 Too Many Requests`

**Solutions:**

1. You've exceeded free tier limit (100 requests/day)
2. Wait 24 hours for limit to reset
3. Upgrade to paid plan if needed
4. Use cached articles from database

**Problem:** `No articles returned`

**Solutions:**

1. This is normal - query might not match recent news
2. Try different search terms
3. Check date range parameters
4. Verify API key has access to search endpoint

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'supabase'`

**Solutions:**

```bash
pip install -r requirements.txt
# or specifically:
pip install supabase
```

### Permission Errors

**Problem:** Can't write to `models/` directory

**Solutions:**

```bash
# Create directory with proper permissions
mkdir -p models
chmod 755 models

# Or run with appropriate permissions
sudo python scripts/download_models.py
```

---

## Next Steps

After successful setup:

1. **Fine-tune models** on your dataset:

   ```bash
   python src/models/train.py
   ```

2. **Start the API server**:

   ```bash
   uvicorn src.api.main:app --reload
   ```

3. **Test predictions**:

   ```bash
   curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{"text": "Breaking news article text here"}'
   ```

4. **Set up frontend** (see main README.md)

---

## Additional Resources

- [Hugging Face Transformers Docs](https://huggingface.co/docs/transformers)
- [Supabase Documentation](https://supabase.com/docs)
- [GNews API Documentation](https://gnews.io/docs/v4)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## Support

If you encounter issues not covered here:

1. Check the main [README.md](README.md)
2. Review error logs in terminal
3. Check Supabase logs in dashboard
4. Open an issue on GitHub with error details
