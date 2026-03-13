# 🚀 Quick Start Guide

Get your Fake News Detection system up and running in minutes!

## Prerequisites

- Python 3.9+
- Internet connection
- [Supabase account](https://supabase.com) (free)
- [GNews API key](https://gnews.io) (free)

---

## Option 1: Automated Setup (Recommended)

### Windows

```bash
scripts\quick_start.bat
```

### macOS/Linux

```bash
chmod +x scripts/quick_start.sh
./scripts/quick_start.sh
```

The script will:

1. ✅ Create virtual environment
2. ✅ Install dependencies
3. ✅ Download models from Hugging Face
4. ✅ Test Supabase and GNews connections

---

## Option 2: Manual Setup

### Step 1: Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your credentials
```

Required variables:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
GNEWS_API_KEY=your_gnews_key
```

### Step 3: Setup Supabase Database

1. Go to your [Supabase Dashboard](https://app.supabase.com)
2. Open **SQL Editor**
3. Run the SQL from `scripts/setup_supabase.sql`

### Step 4: Download Models

```bash
python scripts/download_models.py
```

This downloads:

- DistilBERT (66M params) - ~250MB
- RoBERTa (125M params) - ~500MB
- XLNet (110M params) - ~450MB

**Total:** ~1.2GB

### Step 5: Test Connections

```bash
python scripts/test_connections.py
```

---

## Start the API Server

```bash
uvicorn src.api.main:app --reload
```

API will be available at:

- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Test the API

### Health Check

```bash
curl http://localhost:8000/health
```

### Make a Prediction

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Breaking: Scientists discover new planet in solar system",
    "model": "distilbert"
  }'
```

### Fetch Recent News

```bash
curl "http://localhost:8000/news?query=technology&max_results=5"
```

### Submit Feedback

```bash
curl -X POST "http://localhost:8000/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": "your-article-id",
    "predicted_label": "True",
    "actual_label": "Fake",
    "user_comment": "This was actually fake news"
  }'
```

---

## Available Endpoints

| Endpoint        | Method | Description               |
| --------------- | ------ | ------------------------- |
| `/`             | GET    | Health check              |
| `/health`       | GET    | Detailed health status    |
| `/predict`      | POST   | Classify news article     |
| `/feedback`     | POST   | Submit user feedback      |
| `/news`         | GET    | Fetch recent news         |
| `/news/analyze` | GET    | Fetch and analyze news    |
| `/stats`        | GET    | Get prediction statistics |
| `/models`       | GET    | List available models     |

---

## Project Structure

```
fake-news-detection/
├── models/                    # Downloaded models (created by script)
│   ├── distilbert/
│   ├── roberta/
│   └── xlnet/
├── scripts/
│   ├── download_models.py    # Download models from HF
│   ├── test_connections.py   # Test Supabase & GNews
│   ├── setup_supabase.sql    # Database schema
│   ├── quick_start.sh        # Automated setup (Unix)
│   └── quick_start.bat       # Automated setup (Windows)
├── src/
│   ├── api/
│   │   └── main.py           # FastAPI application
│   ├── utils/
│   │   ├── supabase_client.py  # Supabase integration
│   │   └── gnews_client.py     # GNews API integration
│   ├── models/
│   │   └── train.py          # Model training
│   └── data/
│       └── preprocessing.py  # Data preprocessing
├── .env                      # Your credentials (create this)
├── .env.example              # Template
├── requirements.txt          # Python dependencies
└── README_SETUP.md          # Detailed setup guide
```

---

## Common Issues

### Models not downloading?

- Check internet connection
- Try downloading one at a time
- Ensure ~2GB free disk space

### Supabase connection failed?

- Verify credentials in `.env`
- Check you ran `setup_supabase.sql`
- Ensure using `anon` key, not `service_role`

### GNews API not working?

- Verify API key at https://gnews.io/dashboard
- Check free tier limit (100 requests/day)
- Wait 24 hours if limit exceeded

### Import errors?

- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

---

## Next Steps

1. **Fine-tune models** on your dataset:

   ```bash
   python src/models/train.py
   ```

2. **Set up frontend** (React + Vite):

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Deploy to production**:
   - Backend: Render, Railway, or Fly.io
   - Frontend: Vercel or Netlify
   - Database: Already on Supabase

4. **Add explainability**:
   - Implement SHAP/LIME in `src/explainability/`

---

## Resources

- 📖 [Full Setup Guide](README_SETUP.md)
- 📚 [API Documentation](http://localhost:8000/docs)
- 🤗 [Hugging Face Models](https://huggingface.co/models)
- 🗄️ [Supabase Docs](https://supabase.com/docs)
- 📰 [GNews API Docs](https://gnews.io/docs)

---

## Support

Need help? Check:

1. [README_SETUP.md](README_SETUP.md) for detailed instructions
2. [GitHub Issues](https://github.com/your-repo/issues)
3. Error logs in terminal

---

**Ready to detect fake news!** 🎉
