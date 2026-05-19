# Disk Space Cleanup

## What Was Removed

The following large files/folders have been removed from the local repository to save disk space. All of these are hosted elsewhere and can be re-downloaded when needed.

### Deleted Folders

1. **`venv/`** - Python virtual environment
   - **Size**: ~500MB - 2GB
   - **Reason**: Can be recreated with `python -m venv venv` and `pip install -r requirements.txt`

2. **`models/`** - Fine-tuned model weights
   - **Size**: ~2-5GB
   - **Hosted on**: HuggingFace Hub
     - [aviseth/distilbert-fakenews](https://huggingface.co/aviseth/distilbert-fakenews)
     - [aviseth/roberta-fakenews](https://huggingface.co/aviseth/roberta-fakenews)
     - [aviseth/xlnet-fakenews](https://huggingface.co/aviseth/xlnet-fakenews)
   - **How to restore**: Run `python scripts/download_models.py`

3. **`data/raw/`** - Original datasets
   - **Size**: ~500MB - 1GB
   - **Hosted on**: Various sources (ISOT, LIAR, BuzzFeed, etc.)
   - **Not needed**: Raw data was already preprocessed

4. **`data/processed/`** - Cleaned training data
   - **Size**: ~100-300MB
   - **Hosted on**: [Kaggle Dataset](https://www.kaggle.com/datasets/aviseth20/multi-class-fake-news-dataset)
   - **How to restore**: Download from Kaggle or re-run `notebooks/Dataset_Cleaning.ipynb`

5. **`frontend/node_modules/`** - Node.js dependencies
   - **Size**: ~200-500MB
   - **Reason**: Can be reinstalled with `npm install`

### Cache Files Removed

- `__pycache__/` directories
- `.pytest_cache/` directories
- `.hypothesis/` directories
- `*.pyc` files

---

## How to Restore

### 1. Python Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### 2. Model Weights

```bash
python scripts/download_models.py
```

This will download all 3 models from HuggingFace Hub to the `models/` directory.

### 3. Dataset (Optional)

Only needed if you want to retrain models:

**Option A: Download from Kaggle**

```python
import kagglehub
df = kagglehub.load_dataset(
    kagglehub.KaggleDatasetAdapter.PANDAS,
    "aviseth20/multi-class-fake-news-dataset"
)
```

**Option B: Re-run preprocessing**

```bash
jupyter notebook notebooks/Dataset_Cleaning.ipynb
```

### 4. Frontend Dependencies

```bash
cd frontend
npm install
```

---

## Current Disk Usage

After cleanup, the repository should be:

- **Before**: ~5-10 GB
- **After**: ~50-200 MB (just code and configs)

---

## What's Still Included

✅ All source code (`src/`, `fake-news-api/src/`, `frontend/src/`)
✅ Configuration files (`.env.example`, `requirements.txt`, `package.json`)
✅ Documentation (`README.md`, `PROJECT_DOCUMENTATION.md`)
✅ Notebooks (`notebooks/`)
✅ Scripts (`scripts/`)
✅ Git history (`.git/`)

---

## Production Deployment

The production deployment doesn't need any of the deleted files:

- **Backend (HuggingFace Spaces)**: Downloads models at build time
- **Frontend (Vercel)**: Installs dependencies during build
- **Models**: Loaded from HuggingFace Hub at runtime
- **Data**: Not needed in production

---

## Notes

- The `.gitignore` file already excludes these folders from version control
- Models are automatically downloaded when the API starts if not present
- All deleted content is backed up on cloud services (HuggingFace, Kaggle, npm)
- This cleanup is safe and reversible
