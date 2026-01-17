# Fake News Detection System

Multi-class fake news detection using deep learning, explainable AI (XAI), and a real-time news API.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Team Members](#team-members)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
  - [Branch Strategy](#branch-strategy)
  - [Commit Convention](#commit-convention)
- [Datasets Used](#datasets-used)
- [Testing](#testing)
- [Model Performance](#model-performance)
- [Contributing](#contributing)
- [License](#license)
- [Resources](#resources)
- [Contact](#contact)

---

## Project Overview

This repository implements a multi-class fake-news detection system that classifies news articles into four categories:

- **True**: Verified factual news
- **Fake**: Fabricated or misleading content
- **Satire**: Humorous or satirical content
- **Bias**: Politically or ideologically biased reporting

The system uses transformer-based models for classification, integrates explainability tools for model interpretation, and supports real-time ingestion via a news API.

## Architecture

- **Models**: DistilBERT, RoBERTa, XLNet
- **Backend**: FastAPI + PostgreSQL
- **Frontend**: React + Tailwind CSS
- **Explainability (XAI)**: SHAP, LIME
- **MLOps / Experiment Tracking**: Weights & Biases (W&B)

## Team Members

| Name         | Role                         | GitHub       | Contact  |
|--------------|------------------------------|--------------|----------|
| Avi Seth     | Project Lead / ML Engineer   | `@username1` | email1   |
| Aliza khan   | Data / Integration Engineer  | `@username2` | email2   |
| Shweta Bisht | Frontend / Backend Developer | `@username3` | email3   |


## Quick Start

### Prerequisites

- Python 3.9 or newer
- Node.js 16 or newer
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

# Install Python dependencies
pip install -r requirements.txt

# Install pre-commit hooks (optional)
pre-commit install
```

### Running the Application

```bash
# Start backend (from project root)
cd src/api
uvicorn main:app --reload

# Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Project Structure

```
fake-news-detection/
├── data/                   # Datasets (not tracked in git)
│   ├── raw/                # Original datasets
│   ├── processed/          # Cleaned and tokenized data
│   └── feedback/           # User feedback for active learning
├── models/                 # Trained models (use DVC or external storage)
│   ├── distilbert/
│   ├── roberta/
│   └── checkpoints/
├── notebooks/              # Jupyter notebooks for exploration
│   ├── 01_data_exploration.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_model_training.ipynb
│   └── 04_evaluation.ipynb
├── src/                    # Source code
│   ├── data/               # Data processing scripts
│   ├── models/             # Model training and evaluation
│   ├── api/                # FastAPI backend
│   ├── explainability/     # SHAP/LIME integration
│   └── utils/              # Helper functions
├── frontend/               # React application
│   ├── src/
│   └── public/
├── tests/                  # Unit and integration tests
├── docs/                   # Documentation
├── configs/                # Configuration files
├── scripts/                # Utility scripts
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Development Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Critical production fixes

### Commit Convention

Follow Conventional Commits. Examples:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

Example: `feat: add SHAP explainability module`

## Datasets Used

1. ISOT Fake News Dataset (~44k articles)
2. LIAR Dataset (~12.8k statements)
3. FakeNewsNet (multimodal data)
4. Satire datasets (e.g., The Onion, Babylon Bee)

Store large datasets outside of Git (use DVC, cloud storage, or private buckets).

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run a specific test file
pytest tests/test_preprocessing.py
```

## Model Performance

| Model     | Accuracy | F1-Score | Latency |
|-----------|----------|----------|---------|
| DistilBERT| TBD      | TBD      | ~50 ms  |
| RoBERTa   | TBD      | TBD      | ~100 ms |
| XLNet     | TBD      | TBD      | ~150 ms |

## Contributing

1. Create a feature branch from `develop` or `main` depending on the workflow
2. Implement your changes
3. Add or update tests
4. Update documentation
5. Submit a pull request

See `docs/CONTRIBUTING.md` for detailed contribution guidelines.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Resources

- Project documentation: `docs/`
- API documentation: `docs/api/`
- Weights & Biases dashboard: `https://wandb.ai/your-team/fake-news-detection`
- Hugging Face models: `https://huggingface.co/your-org`

## Contact

For questions or issues, contact the project lead or open an issue on GitHub.
