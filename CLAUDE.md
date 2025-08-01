# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

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

# Run tests excluding slow tests (for performance regression tests)
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

## Development Workflow

- Before committing and pushing to GitHub, make sure the repo passes
  pytest, ruff, black, and mypy tests, update the CHANGELOG.md file, and
  uprev the release number in the pyproject.toml file, the PyPI badge in
  the README.md file, and all of the documentation headers.
- Before deploying a release to PyPI once a commit has been pushed to
  GitHub, monitor the GitHub Actions to make the repo was pushed
  successfully.

## Architecture Overview

wKrQ is a Python implementation of a semantic tableau calculus for
three-valued weak Kleene logic with restricted quantification. The system
is organized into these core components:

### Core Logic Engine (src/wkrq/)

- **formula.py**: Formula representation hierarchy (PropositionalAtom,
  CompoundFormula, PredicateFormula, Restricted quantifiers)
- **semantics.py**: Three-valued weak Kleene semantic system where any
  operation with undefined produces undefined
- **signs.py**: Four-sign tableau system (T, F, M, N) for proof construction
- **tableau.py**: Industrial-grade optimized tableau engine with O(1)
  contradiction detection
- **parser.py**: String-to-formula parsing with support for Unicode operators
- **api.py**: High-level API functions (solve, valid, entails, check_inference)
- **cli.py**: Command-line interface implementation

### Key Design Patterns

1. **Weak Kleene Semantics**: Unlike strong Kleene, `t ∨ e = e` (not `t`)
2. **Four-Sign System**:
   - T: Must be true
   - F: Must be false  
   - M: Can be true or false
   - N: Must be undefined
3. **Restricted Quantification**: `[∃X P(X)]Q(X)` and `[∀X P(X)]Q(X)`
   for domain-bounded reasoning
4. **Unification-Based Quantifier Instantiation**:
   - Ground terms (constants) are tracked in each tableau branch
     (`branch.ground_terms`)
   - Universal quantifiers are instantiated with existing constants
     before generating fresh ones
   - Universal instantiation tracking
     (`branch._universal_instantiations`) prevents redundant applications
   - Existential quantifiers use unification for witness selection
   - Proper inference: `[∀X Human(X)]Mortal(X), Human(socrates) |-
     Mortal(socrates)` now works correctly
5. **Performance Optimizations**:
   - Hash-based formula indexing for O(1) contradiction detection
   - Alpha (non-branching) rules prioritized over beta (branching) rules
   - "Least complex first" branch selection strategy
   - Early termination for satisfiability testing

   **Future optimizations** (see `docs/TABLEAU_OPTIMIZATIONS.md`):
   - Branch pruning: Eliminate contradictory/irrelevant branches
   - Simplification rules: Replace subformulas with true/false in context
   - Connectedness restrictions: Limit expansion based on literal
     connections
   - Formula elimination via splitting (for clause-based tableaux)

### Ferguson (2021) Compliance

The implementation follows Ferguson's hybrid approach that combines:

- **Weak Kleene truth tables** for semantic operations (any operation with undefined produces undefined)
- **Classical validity** for practical reasoning (classical tautologies
  remain valid)
- **Truth preservation** as the validity criterion: Γ ⊨wK φ if for all
  interpretations where premises are true, conclusion is true

This means:

- `p ∨ ¬p` is unsatisfiable under F sign (classical tautologies cannot
  be false)
- `p ∧ ¬p` is unsatisfiable under T sign (contradictions cannot be true)
- M and N signs allow epistemic uncertainty about logical truths

### Testing Strategy

The test suite validates:

- Semantic correctness against weak Kleene truth tables
- Tableau soundness and completeness
- Performance benchmarks (sub-millisecond response times)
- Literature validation against published examples (Ferguson 2021)
- Quantifier unification and inference patterns
- CLI functionality and quantifier parsing
- Ferguson compliance tests (17 tests validating against the paper's
  definitions)

### Future Extension: ACrQ

The codebase is designed to support ACrQ (Analytic Containment with
restricted Quantification) as documented in
`docs/ACrQ_IMPLEMENTATION_GUIDE.md`. ACrQ extends wKrQ with:

- **Bilateral predicates**: Each predicate R has a dual R* for
  independent tracking of positive and negative conditions
- **Paraconsistent reasoning**: Handle knowledge gluts (conflicting
  information) without explosion
- **Paracomplete reasoning**: Handle knowledge gaps (missing
  information) without assuming classical completeness

The architecture is prepared for this extension through:

- Modular formula hierarchy that can accommodate
  BilateralPredicateFormula
- Extensible tableau engine with pluggable rule systems
- System selection layer for choosing between wKrQ and ACrQ

## Documentation Guidelines

- All documentation save the README.md and CONTRIBUTING.md files need to go in the docs directory.