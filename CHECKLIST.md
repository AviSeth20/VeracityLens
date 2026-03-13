# 📋 Setup Checklist

Use this checklist to track your setup progress.

---

## Phase 1: Initial Setup ⚙️

- [ ] Clone repository
- [ ] Create virtual environment
  ```bash
  python -m venv venv
  ```
- [ ] Activate virtual environment
  ```bash
  source venv/bin/activate  # macOS/Linux
  venv\Scripts\activate     # Windows
  ```
- [ ] Install dependencies
  ```bash
  pip install -r requirements.txt
  ```

---

## Phase 2: Get API Credentials 🔑

### Supabase

- [ ] Create account at [supabase.com](https://supabase.com)
- [ ] Create new project
- [ ] Copy Project URL
- [ ] Copy anon/public key
- [ ] Copy service_role key (optional)

### GNews API

- [ ] Create account at [gnews.io](https://gnews.io)
- [ ] Get API key from dashboard
- [ ] Note free tier limits (100 requests/day)

---

## Phase 3: Configure Environment 🌍

- [ ] Copy `.env.example` to `.env`
  ```bash
  cp .env.example .env
  ```
- [ ] Add Supabase URL to `.env`
- [ ] Add Supabase key to `.env`
- [ ] Add GNews API key to `.env`
- [ ] Verify no extra spaces in `.env`

---

## Phase 4: Setup Database 🗄️

- [ ] Open Supabase dashboard
- [ ] Go to SQL Editor
- [ ] Open `scripts/setup_supabase.sql`
- [ ] Copy SQL content
- [ ] Paste in SQL Editor
- [ ] Click "Run"
- [ ] Verify tables created:
  - [ ] predictions
  - [ ] feedback
  - [ ] news_articles
  - [ ] model_performance
  - [ ] user_sessions

---

## Phase 5: Download Models 🤖

- [ ] Run download script
  ```bash
  python scripts/download_models.py
  ```
- [ ] Wait for downloads to complete (~5-10 minutes)
- [ ] Verify models downloaded:
  - [ ] models/distilbert/
  - [ ] models/roberta/
  - [ ] models/xlnet/
- [ ] Check model files exist:
  - [ ] config.json
  - [ ] model.safetensors
  - [ ] tokenizer files

---

## Phase 6: Test Connections 🔌

- [ ] Run test script
  ```bash
  python scripts/test_connections.py
  ```
- [ ] Verify results:
  - [ ] ✅ Environment Variables: PASS
  - [ ] ✅ Supabase Connection: PASS
  - [ ] ✅ GNews API Connection: PASS

---

## Phase 7: Start API Server 🚀

- [ ] Start server
  ```bash
  uvicorn src.api.main:app --reload
  ```
- [ ] Verify server started
- [ ] Open browser to http://localhost:8000
- [ ] Check API docs at http://localhost:8000/docs

---

## Phase 8: Test API Endpoints 🧪

### Health Check

- [ ] Test root endpoint
  ```bash
  curl http://localhost:8000
  ```
- [ ] Test health endpoint
  ```bash
  curl http://localhost:8000/health
  ```

### Predictions

- [ ] Test prediction endpoint
  ```bash
  curl -X POST "http://localhost:8000/predict" \
    -H "Content-Type: application/json" \
    -d '{"text": "Test article", "model": "distilbert"}'
  ```
- [ ] Verify response received
- [ ] Check article_id returned

### News Fetching

- [ ] Test news endpoint
  ```bash
  curl "http://localhost:8000/news?query=technology&max_results=3"
  ```
- [ ] Verify articles returned
- [ ] Check article structure

### Feedback

- [ ] Test feedback endpoint
  ```bash
  curl -X POST "http://localhost:8000/feedback" \
    -H "Content-Type: application/json" \
    -d '{
      "article_id": "test-123",
      "predicted_label": "True",
      "actual_label": "Fake"
    }'
  ```
- [ ] Verify feedback stored

### Statistics

- [ ] Test stats endpoint
  ```bash
  curl http://localhost:8000/stats
  ```
- [ ] Verify statistics returned

---

## Phase 9: Verify Database 📊

- [ ] Open Supabase dashboard
- [ ] Go to Table Editor
- [ ] Check predictions table
  - [ ] Verify test prediction stored
- [ ] Check feedback table
  - [ ] Verify test feedback stored
- [ ] Check news_articles table

---

## Phase 10: Next Steps 🎯

### Immediate

- [ ] Read [QUICK_START.md](QUICK_START.md)
- [ ] Read [README_SETUP.md](README_SETUP.md)
- [ ] Bookmark [COMMANDS.md](COMMANDS.md)

### Model Training

- [ ] Prepare training dataset
- [ ] Review `src/models/train.py`
- [ ] Configure training parameters
- [ ] Start training
- [ ] Monitor with Weights & Biases

### Frontend Development

- [ ] Setup React + Vite
- [ ] Install Tailwind CSS
- [ ] Install shadcn/ui
- [ ] Create components
- [ ] Connect to API

### Deployment

- [ ] Choose hosting platform
  - [ ] Backend: Render / Railway / Fly.io
  - [ ] Frontend: Vercel / Netlify
- [ ] Setup environment variables
- [ ] Deploy backend
- [ ] Deploy frontend
- [ ] Test production

---

## Troubleshooting Checklist 🔧

If something doesn't work:

### Environment Issues

- [ ] Virtual environment activated?
- [ ] All dependencies installed?
- [ ] `.env` file exists?
- [ ] No typos in `.env`?

### Connection Issues

- [ ] Internet connection working?
- [ ] API keys valid?
- [ ] Supabase project active?
- [ ] Free tier limits not exceeded?

### Model Issues

- [ ] Models fully downloaded?
- [ ] Enough disk space (~2GB)?
- [ ] Model files not corrupted?
- [ ] Correct directory structure?

### API Issues

- [ ] Port 8000 not in use?
- [ ] Server started successfully?
- [ ] No Python errors in terminal?
- [ ] CORS configured correctly?

### Database Issues

- [ ] SQL script ran successfully?
- [ ] Tables created?
- [ ] RLS policies enabled?
- [ ] Connection string correct?

---

## Optional Enhancements ✨

- [ ] Add SHAP explainability
- [ ] Add LIME explainability
- [ ] Implement model ensemble
- [ ] Add caching layer
- [ ] Setup monitoring
- [ ] Add logging
- [ ] Implement rate limiting
- [ ] Add authentication
- [ ] Create admin dashboard
- [ ] Setup CI/CD pipeline
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Setup error tracking
- [ ] Add performance monitoring

---

## Documentation Checklist 📚

- [ ] Read QUICK_START.md
- [ ] Read README_SETUP.md
- [ ] Read COMMANDS.md
- [ ] Read SETUP_COMPLETE.md
- [ ] Bookmark API docs (http://localhost:8000/docs)
- [ ] Review Supabase docs
- [ ] Review GNews API docs
- [ ] Review Hugging Face docs

---

## Success Criteria ✅

You're ready when:

- [x] All Phase 1-8 items checked
- [x] API server running
- [x] All endpoints responding
- [x] Database storing data
- [x] News fetching working
- [x] Models downloaded
- [x] Tests passing

---

## Quick Reference 📝

### Start Development

```bash
# Activate environment
source venv/bin/activate

# Start API
uvicorn src.api.main:app --reload

# Run tests
python scripts/test_connections.py
```

### Common Commands

```bash
# Download models
python scripts/download_models.py

# Test connections
python scripts/test_connections.py

# Run tests
pytest

# View API docs
open http://localhost:8000/docs
```

### Get Help

1. Check [README_SETUP.md](README_SETUP.md)
2. Review error messages
3. Test connections individually
4. Check service dashboards
5. Open GitHub issue

---

## Progress Tracking

**Started:** ******\_\_\_******

**Completed Phase 1:** ******\_\_\_******
**Completed Phase 2:** ******\_\_\_******
**Completed Phase 3:** ******\_\_\_******
**Completed Phase 4:** ******\_\_\_******
**Completed Phase 5:** ******\_\_\_******
**Completed Phase 6:** ******\_\_\_******
**Completed Phase 7:** ******\_\_\_******
**Completed Phase 8:** ******\_\_\_******

**Fully Operational:** ******\_\_\_******

---

## Notes

Use this space for notes, issues encountered, or reminders:

```
_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________
```

---

**Good luck with your setup!** 🚀

Once everything is checked off, you'll have a fully functional fake news detection system ready to classify articles and learn from user feedback!
