# ��� Fake News Detection System

Multi-class fake news detection using Deep Learning, XAI, and Real-Time API

## ��� Project Overview

This system classifies news articles into four categories:
- ✅ **True**: Verified factual news
- ❌ **Fake**: Fabricated or misleading content
- ��� **Satire**: Humorous or satirical content
- ⚖️ **Bias**: Politically or ideologically biased reporting

## ���️ Architecture

- **Models**: DistilBERT, RoBERTa, XLNet
- **Backend**: FastAPI + PostgreSQL
- **Frontend**: React + Tailwind CSS
- **XAI**: SHAP and LIME explanations
- **MLOps**: Weights & Biases tracking

## ��� Team Members

| Name | Role | GitHub | Contact |
|------|------|--------|---------|
| [Name 1] | Project Lead / ML Engineer | @username1 | email1 |
| [Name 2] | Data Engineer | @username2 | email2 |
| [Name 3] | Backend Developer | @username3 | email3 |
| [Name 4] | Frontend Developer | @username4 | email4 |

## ��� Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Git
- Docker (optional)

### Setup

```bash
# Clone repository
git clone https://github.com/your-org/fake-news-detection.git
cd fake-news-detection

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup pre-commit hooks
pre-commit install
```

### Running the Application

```bash
# Start backend
cd src/api
uvicorn main:app --reload

# Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

## ��� Project Structure

```
fake-news-detection/
├── data/                   # Datasets (not tracked in git)
│   ├── raw/               # Original datasets
│   ├── processed/         # Cleaned and tokenized data
│   └── feedback/          # User feedback for active learning
├── models/                # Trained models (use DVC or external storage)
│   ├── distilbert/
│   ├── roberta/
│   └── checkpoints/
├── notebooks/             # Jupyter notebooks for exploration
│   ├── 01_data_exploration.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_model_training.ipynb
│   └── 04_evaluation.ipynb
├── src/                   # Source code
│   ├── data/             # Data processing scripts
│   ├── models/           # Model training and evaluation
│   ├── api/              # FastAPI backend
│   ├── explainability/   # SHAP/LIME integration
│   └── utils/            # Helper functions
├── frontend/              # React application
│   ├── src/
│   └── public/
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation
├── configs/               # Configuration files
├── scripts/               # Utility scripts
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## ��� Development Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Critical production fixes

### Commit Convention
Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

Example: `feat: add SHAP explainability module`

## ��� Datasets Used

1. **ISOT Fake News Dataset** (~44k articles)
2. **LIAR Dataset** (~12.8k statements)
3. **FakeNewsNet** (multimodal data)
4. **Satire Datasets** (The Onion, Babylon Bee)

## ��� Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_preprocessing.py
```

## ��� Model Performance

| Model | Accuracy | F1-Score | Latency |
|-------|----------|----------|---------|
| DistilBERT | TBD | TBD | ~50ms |
| RoBERTa | TBD | TBD | ~100ms |
| XLNet | TBD | TBD | ~150ms |

## ��� Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Update documentation
5. Submit pull request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.

## ��� License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## ��� Resources

- [Project Documentation](docs/)
- [API Documentation](docs/api/)
- [Weights & Biases Dashboard](https://wandb.ai/your-team/fake-news-detection)
- [Hugging Face Models](https://huggingface.co/your-org)

## ��� Contact

For questions or issues, please contact [project lead email] or open an issue on GitHub.
