# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development Setup
```bash
# Install in development mode with all dev dependencies
pip install -e ".[dev]"

# Or install dev dependencies separately
pip install -r requirements-dev.txt
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_wkrq_basic.py

# Run single test
pytest tests/test_wkrq_basic.py::test_propositional_satisfiability

# Run with coverage
pytest --cov=wkrq

# Run tests excluding slow tests
pytest -m "not slow"

# Run tests in parallel
pytest -n auto
```

### Code Quality
```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src

# All quality checks
black src tests && ruff check src tests && mypy src
```

### Build and Distribution
```bash
# Build package
python -m build

# Upload to PyPI (requires credentials)
twine upload dist/*
```

## Architecture Overview

wKrQ implements three-valued weak Kleene logic with restricted quantification. The system is organized into these core components:

### Core Logic Engine (src/wkrq/)
- **formula.py**: Formula representation hierarchy (PropositionalAtom, CompoundFormula, PredicateFormula, Restricted quantifiers)
- **semantics.py**: Three-valued weak Kleene semantic system where any operation with undefined produces undefined
- **signs.py**: Four-sign tableau system (T, F, M, N) for proof construction
- **tableau.py**: Industrial-grade optimized tableau engine with O(1) contradiction detection
- **parser.py**: String-to-formula parsing with support for Unicode operators

### Key Design Patterns
1. **Weak Kleene Semantics**: Unlike strong Kleene, `t ∨ e = e` (not `t`)
2. **Four-Sign System**: 
   - T: Must be true
   - F: Must be false  
   - M: Can be true or false
   - N: Must be undefined
3. **Restricted Quantification**: `[∃X P(X)]Q(X)` and `[∀X P(X)]Q(X)` for domain-bounded reasoning
4. **Performance Optimizations**:
   - Hash-based formula indexing for O(1) contradiction detection
   - Alpha (non-branching) rules prioritized over beta (branching) rules
   - "Least complex first" branch selection strategy
   - Early termination for satisfiability testing

### Testing Strategy
The test suite (79 tests) validates:
- Semantic correctness against weak Kleene truth tables
- Tableau soundness and completeness
- Performance benchmarks (sub-millisecond response times)
- Literature validation against published examples