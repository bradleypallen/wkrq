# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

## CRITICAL: bilateral-truth Package Usage

**NEVER create mock LLM evaluators. ONLY use the bilateral-truth package via wkrq.llm_integration.**

### Correct Usage:
```python
from wkrq.llm_integration import create_llm_tableau_evaluator

# Create evaluator using wkrq's integration (handles all complexity)
llm_evaluator = create_llm_tableau_evaluator('openai')  # or 'anthropic', 'google', 'mock'

# Use directly in tableau - no wrapper needed!
tableau = ACrQTableau(formulas, llm_evaluator=llm_evaluator)
```

### Under the Hood:
- wkrq.llm_integration properly wraps bilateral-truth's create_llm_evaluator
- Converts between GeneralizedTruthValue (u,v) and BilateralTruthValue (positive,negative)
- Handles caching and bilateral predicate relationships
- Mock evaluator returns <e,e> (undefined) for testing

### Common Mistakes to AVOID:
1. DO NOT create functions that return BilateralTruthValue objects directly
2. DO NOT implement mock evaluators with if/else logic
3. DO NOT use bilateral-truth's create_llm_evaluator directly - use wkrq.llm_integration
4. DO NOT try to call evaluator.evaluate_bilateral manually - wkrq handles this

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
# Run all tests (311 tests for both wKrQ and ACrQ)
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

# Run Ferguson compliance tests
pytest tests/test_ferguson_compliance.py -v

# Run ACrQ-specific tests
pytest tests/test_acrq_tableau.py -v
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
- **IMPORTANT**: Version consistency is critical for releases. Before any push to GitHub and subsequent release to PyPI, verify that ALL version references are updated consistently:
  - `pyproject.toml` (version field)
  - `src/wkrq/__init__.py` (__version__ variable)
  - Documentation headers in `docs/*.md` files
  - `README.md` PyPI badge (if applicable)
  - `CHANGELOG.md` release entry
- Before deploying a release to PyPI once a commit has been pushed to
  GitHub, monitor the GitHub Actions to make sure the repo was pushed
  successfully.

## Release Checklist

When creating a new release, follow this checklist to ensure consistency:

1. **Version Updates**:
   - [ ] Update version in `pyproject.toml`
   - [ ] Update version in `src/wkrq/__init__.py`
   - [ ] Update `CHANGELOG.md` with release notes
   - [ ] Update documentation headers in `docs/*.md` files with new version
   - [ ] Update PyPI badge version parameter in `README.md`

2. **Code Quality**:
   - [ ] Run `black src tests` (formatting)
   - [ ] Run `ruff check src tests` (linting)
   - [ ] Run `mypy src` (type checking)
   - [ ] Run full test suite `pytest`

3. **Commit and Push**:
   - [ ] Commit all version updates with descriptive message
   - [ ] Push to GitHub main branch

4. **GitHub Actions Verification**:
   - [ ] Monitor GitHub Actions tests with `gh run list`
   - [ ] Verify all tests pass before proceeding
   - [ ] Wait for successful completion (green checkmark)

5. **Release Creation**:
   - [ ] Create GitHub release with `gh release create v{VERSION}`
   - [ ] Include comprehensive release notes
   - [ ] Monitor PyPI publication workflow
   - [ ] Verify package appears on PyPI

6. **Post-Release Verification**:
   - [ ] Confirm PyPI package is installable: `pip install wkrq=={VERSION}`
   - [ ] Check that PyPI badge updates automatically

**CRITICAL**: Never tag and release while GitHub Actions tests are failing. Always wait for test success confirmation before creating releases.

## Architecture Overview

wKrQ implements Ferguson's (2021) tableau calculus for three-valued weak
Kleene logic with restricted quantification. The codebase now includes both
wKrQ (Definition 9) and ACrQ (Definition 18) implementations.

### Core Systems

#### wKrQ System (Ferguson Definition 9)
- **wkrq_rules.py**: Exact tableau rules from Ferguson's Definition 9
- **tableau.py**: Tableau engine with Ferguson's 6-sign system (t,f,e,m,n,v)
- **signs.py**: Ferguson's signs: t (true), f (false), e (error/undefined), 
  m (meaningful/branching), n (nontrue/branching), v (variable/meta-sign)

#### ACrQ System (Ferguson Definition 18)
- **acrq_rules.py**: Modified rules without general negation elimination
- **acrq_tableau.py**: Extended tableau with bilateral predicate support
- **acrq_parser.py**: Three parsing modes (Transparent, Bilateral, Mixed)
- **BilateralPredicateFormula**: R/R* duality for paraconsistent reasoning

### Core Components (src/wkrq/)

- **formula.py**: Formula hierarchy including BilateralPredicateFormula
- **semantics.py**: Weak Kleene semantics with BilateralTruthValue
- **parser.py**: Base parser for standard syntax
- **api.py**: High-level API functions (solve, valid, entails, check_inference)
- **cli.py**: Command-line interface with --mode flag for wKrQ/ACrQ selection

### Key Design Patterns

1. **Ferguson's Sign System**:
   - t: True (definite truth value)
   - f: False (definite truth value)
   - e: Error/undefined (definite truth value)
   - m: Meaningful (branches to t or f)
   - n: Nontrue (branches to f or e)
   - v: Variable (meta-sign for any of t, f, e)

2. **Weak Kleene Semantics**: 
   - Any operation with undefined produces undefined
   - `t ∨ e = e` (not `t` as in strong Kleene)
   - `t ∧ e = e`, `f → e = e`, etc.

3. **Restricted Quantification**: 
   - `[∃X P(X)]Q(X)`: "There exists an X such that P(X) and Q(X)"
   - `[∀X P(X)]Q(X)`: "For all X, if P(X) then Q(X)"

4. **Branch Closure (Ferguson Definition 10)**:
   - wKrQ: Branch closes when distinct v, u ∈ {t,f,e} appear for same formula
   - ACrQ: Modified per Lemma 5 - gluts allowed (t:R(a) and t:R*(a) can coexist)

5. **Quantifier Instantiation**:
   - Universal quantifiers reuse existing constants before generating fresh ones
   - Tracking prevents redundant instantiations
   - Proper unification enables valid inferences

6. **ACrQ Bilateral Predicates**:
   - Each predicate R has dual R* for negative evidence
   - Four information states: true, false, gap, glut
   - Transparent mode: `¬P(x)` automatically becomes `P*(x)`
   - Paraconsistent: handles contradictions without explosion

### Ferguson (2021) Compliance

The implementation exactly follows Ferguson's specifications:

- **Definition 9**: wKrQ tableau rules with 6-sign system
- **Definition 10**: Branch closure conditions
- **Definition 17**: Translation from standard syntax to bilateral
- **Definition 18**: ACrQ as wKrQ minus negation elimination plus bilateral rules
- **Lemma 5**: Glut-tolerant branch closure for ACrQ

Key compliance points:
- Signs are lowercase (t,f,e,m,n,v) as in the paper
- m and n are branching instructions, not truth values
- Negation elimination dropped in ACrQ for compound formulas
- Bilateral predicates enable paraconsistent reasoning

### Testing Strategy

The test suite (311 tests) validates:

- Ferguson compliance tests against Definition 9 and 18
- Semantic correctness for weak Kleene operations
- Tableau soundness and completeness
- ACrQ glut handling and bilateral predicates
- Quantifier unification patterns
- Parser modes (Transparent, Bilateral, Mixed)
- Literature examples from Ferguson's paper
- Performance benchmarks

### Key Differences: wKrQ vs ACrQ

See `docs/wKrQ_vs_ACrQ_COMPARISON.md` for detailed comparison.

**wKrQ**:
- General negation elimination: `v : ~φ → ~v : φ`
- Standard predicates only
- Contradictions close branches
- Three-valued logic

**ACrQ**:
- No general negation elimination (only for predicates)
- Bilateral predicates R/R*
- Gluts allowed: t:R(a) and t:R*(a) can coexist
- Four information states per predicate

### Usage Examples

```python
# wKrQ: Standard three-valued logic
from wkrq import solve, valid, entails

# ACrQ: Paraconsistent reasoning
from wkrq import parse_acrq_formula, SyntaxMode, ACrQTableau

# Transparent mode (default): ¬P(x) becomes P*(x)
formula = parse_acrq_formula("Human(x) & ~Human(x)")  # Handles glut

# Bilateral mode: Explicit R/R* syntax
formula = parse_acrq_formula("Human(x) & Human*(x)", SyntaxMode.BILATERAL)
```

### File Organization

```
src/wkrq/
├── formula.py              # Formula types including BilateralPredicateFormula
├── semantics.py            # Weak Kleene semantics, BilateralTruthValue
├── signs.py                # Ferguson's 6-sign system
├── wkrq_rules.py           # wKrQ rules (Definition 9)
├── tableau.py              # wKrQ tableau engine
├── acrq_rules.py           # ACrQ rules (Definition 18)
├── acrq_tableau.py         # ACrQ tableau with glut handling
├── acrq_parser.py          # Mode-aware parser for ACrQ
├── parser.py               # Base parser
├── api.py                  # High-level API
└── cli.py                  # CLI with --mode flag

tests/
├── test_ferguson_compliance.py  # Ferguson Definition 9/10 tests
├── test_acrq_tableau.py        # ACrQ-specific tests
├── test_acrq_ferguson.py       # ACrQ rule tests
└── ...                         # 311 total tests
```

## Documentation Guidelines

- All documentation except README.md and CONTRIBUTING.md goes in the docs directory
- Use version numbers in documentation headers
- Update all version references consistently before releases
- Key documents:
  - `docs/wKrQ_vs_ACrQ_COMPARISON.md`: Detailed system comparison
  - `docs/FERGUSON_2021_ANALYSIS.md`: Paper analysis
  - `docs/TABLEAU_OPTIMIZATIONS.md`: Performance notes
- IMPORTANT: DO NOT UNDER ANY CIRCUMSTANCES USE AN LLM EVALUATOR OTHER THAN ONE FROM THE bilateral-truth PACKAGE!