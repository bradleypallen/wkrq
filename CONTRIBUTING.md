# Contributing to wKrQ

Thank you for your interest in contributing to wKrQ! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/yourusername/wkrq.git
cd wkrq
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

## Development Workflow

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and ensure tests pass:
```bash
pytest
```

3. Format your code:
```bash
black src tests
ruff check src tests --fix
```

4. Type check your code:
```bash
mypy src
```

5. Commit your changes:
```bash
git add .
git commit -m "Add your descriptive commit message"
```

6. Push and create a pull request:
```bash
git push origin feature/your-feature-name
```

## Code Style

- We use [Black](https://black.readthedocs.io/) for code formatting
- We use [Ruff](https://docs.astral.sh/ruff/) for linting
- All code should have type hints
- Write docstrings for all public functions and classes

## Testing

- Write tests for all new functionality
- Ensure all tests pass before submitting PR
- Aim for high test coverage
- Test files should be in the `tests/` directory

## Documentation

- Update documentation for any API changes
- Include docstrings for new functions/classes
- Update README if adding new features
- Add examples for new functionality

## Pull Request Process

1. Ensure all tests pass
2. Update documentation as needed
3. Add your changes to CHANGELOG.md
4. Request review from maintainers
5. Address any feedback

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include minimal reproducible examples
- Specify your Python version and OS
- Check existing issues before creating new ones

## Questions?

Feel free to open an issue for any questions about contributing!