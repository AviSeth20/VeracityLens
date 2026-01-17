# Contributing Guidelines

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/fake-news-detection.git`
3. Add upstream remote: `git remote add upstream https://github.com/ORIGINAL-OWNER/fake-news-detection.git`
4. Create a branch: `git checkout -b feature/your-feature-name`

## Before Committing

1. Run tests: `pytest`
2. Format code: `black src/`
3. Check linting: `flake8 src/`
4. Update documentation if needed

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the requirements.txt if you add dependencies
3. Follow the commit message convention
4. Request review from at least one team member
5. Squash commits before merging

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for functions
- Maximum line length: 100 characters

## Testing

- Write tests for new features
- Maintain test coverage above 80%
- Use descriptive test names
