# wKrQ: Three-Valued Weak Kleene Logic with Restricted Quantification

[![PyPI version](https://badge.fury.io/py/wkrq.svg)](https://badge.fury.io/py/wkrq)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/bradleypallen/wkrq/actions/workflows/tests.yml/badge.svg)](https://github.com/bradleypallen/wkrq/actions/workflows/tests.yml)

A Python implementation of three-valued weak Kleene logic with restricted quantification, featuring a complete tableau-based theorem prover with industrial-grade performance optimizations.

## Features

- 🎯 **Three-valued semantics**: true (t), false (f), undefined (e)
- 🔤 **Weak Kleene logic**: Operations with undefined propagate undefinedness
- 🔢 **Restricted quantification**: Domain-bounded first-order reasoning
- ⚡ **Industrial performance**: Optimized tableau with sub-millisecond response
- 🖥️ **CLI and API**: Both command-line and programmatic interfaces
- 📚 **Comprehensive docs**: Full documentation with examples

## Quick Start

### Installation

```bash
pip install wkrq
```

### Command Line Usage

```bash
# Test a simple formula
wkrq "p & q"

# Test with specific sign (T, F, M, N)
wkrq --sign=N "p | ~p"

# Show all models
wkrq --models "p | q"

# Display tableau tree
wkrq --tree "p -> q"

# First-order logic with restricted quantifiers
wkrq "[∃X Student(X)]Human(X)"
wkrq "[∀X Human(X)]Mortal(X)"
```

### Python API

```python
from wkrq import Formula, solve, valid, T, F, M, N

# Create formulas
p, q = Formula.atoms('p', 'q')
formula = p & (q | ~p)

# Test satisfiability
result = solve(formula, T)
print(f"Satisfiable: {result.satisfiable}")
print(f"Models: {result.models}")

# Test validity
tautology = p | ~p
print(f"Valid in weak Kleene: {valid(tautology)}")  # True (surprisingly!)

# Three-valued reasoning
result = solve(p | ~p, N)  # Can it be undefined?
print(f"Can be undefined: {result.satisfiable}")  # True
```

## Three-Valued Logic Semantics

wKrQ implements **weak Kleene** logic where undefined values propagate:

| Operation | Result |
|-----------|--------|
| t ∧ e | e |
| t ∨ e | e |
| ¬e | e |
| e → t | e |

This differs from strong Kleene logic where `t ∨ e = t`.

## Documentation

- 📖 [CLI Guide](docs/wKrQ_CLI_GUIDE.md) - Complete command-line reference
- 🔧 [API Reference](docs/wKrQ_API_REFERENCE.md) - Full Python API documentation
- 🏗️ [Architecture](docs/wKrQ_ARCHITECTURE.md) - System design and theory

## Examples

### Philosophical Logic: Sorites Paradox

```python
from wkrq import Formula, solve, T, N

# Model vague predicates with three-valued logic
heap_1000 = Formula.atom("Heap1000")  # Clearly a heap
heap_999 = Formula.atom("Heap999")    # Borderline case
heap_1 = Formula.atom("Heap1")        # Clearly not a heap

# Sorites principle
sorites = heap_1000.implies(heap_999)

# The paradox dissolves with undefined values
result = solve(heap_999, N)  # Can be undefined
print(f"Borderline case can be undefined: {result.satisfiable}")
```

### First-Order Reasoning

```python
from wkrq import Formula

# Variables and predicates
x = Formula.variable("X")
human = Formula.predicate("Human", [x])
mortal = Formula.predicate("Mortal", [x])

# Restricted quantification
all_humans_mortal = Formula.restricted_forall(x, human, mortal)
print(f"∀-formula: {all_humans_mortal}")  # [∀X Human(X)]Mortal(X)
```

## Development

```bash
# Clone repository
git clone https://github.com/bradleypallen/wkrq.git
cd wkrq

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
ruff check src tests

# Type checking
mypy src
```

## Theory

wKrQ uses a tableau proof system with four signs:

- **T**: Must be true (t)
- **F**: Must be false (f)
- **M**: Can be true or false (t or f)
- **N**: Must be undefined (e)

This enables systematic proof search in three-valued logic while maintaining classical reasoning as a special case.

## Performance

Industrial-grade optimizations include:

- O(1) contradiction detection via hash indexing
- Alpha/beta rule prioritization
- Intelligent branch selection
- Early termination strategies
- Subsumption elimination

## Citation

If you use wKrQ in academic work, please cite:

```bibtex
@software{wkrq2025,
  title={wKrQ: Three-Valued Weak Kleene Logic with Restricted Quantification},
  author={Allen, Bradley P.},
  year={2025},
  url={https://github.com/bradleypallen/wkrq}
}
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- [PyPI Package](https://pypi.org/project/wkrq/)
- [GitHub Repository](https://github.com/bradleypallen/wkrq)
- [Issue Tracker](https://github.com/bradleypallen/wkrq/issues)
- [Documentation](https://github.com/bradleypallen/wkrq/tree/main/docs)