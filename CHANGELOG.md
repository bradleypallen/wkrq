# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2025-01-29

### Added
- **Complete subsumption optimization system** for tableau theorem proving
  - Propositional subsumption: stronger formulas subsume weaker ones (e.g., `p` subsumes `p ∨ q`)
  - First-order subsumption: universals subsume instances with consistency checking (e.g., `P(X)` subsumes `P(a)`)
  - Three-valued logic subsumption: sign relationships based on truth value sets (e.g., `T:p` subsumes `M:p`)
- **Industrial-grade tableau optimizations**
  - Forward subsumption filtering: incoming subsumed formulas are rejected
  - Backward subsumption marking: existing formulas marked as subsumed when stronger ones are added
  - Rule application optimization: subsumed formulas skipped during expansion
- **Comprehensive test coverage** with 27 new subsumption tests
- **Performance benchmarking** showing significant optimization benefits
- **Soundness preservation** ensuring tableau correctness while optimizing performance

### Performance
- Sub-millisecond subsumption detection (~0.015ms propositional, ~0.003ms first-order)
- Optimized tableau construction with redundancy elimination
- Reduced memory usage through intelligent formula filtering

## [1.0.1] - 2025-01-28

### Changed
- Added proper academic citation to Thomas Ferguson's TABLEAUX 2021 paper
- Added research software disclaimer
- Clarified documentation to indicate this is an implementation of a semantic tableau calculus
- Fixed version numbers from 2.0 to 1.0.0 throughout codebase
- Updated Python requirement from 3.8+ to 3.9+
- Fixed all code quality issues (mypy, ruff, black)
- Adjusted performance test timing thresholds for CI environments

### Fixed
- Fixed deprecated license format in pyproject.toml
- Fixed deprecated typing imports (List → list, etc.)
- Fixed mypy type checking errors across all modules
- Fixed CLI to use version from __init__.py

## [1.0.0] - 2025-01-28

### Added
- Initial release of wKrQ as a standalone package
- Three-valued weak Kleene logic implementation
- Restricted quantification for first-order logic
- Complete tableau-based theorem prover
- Command-line interface with `wkrq` command
- Python API for programmatic use
- Four tableau signs (T, F, M, N) for three-valued reasoning
- Industrial-grade performance optimizations
- Comprehensive test suite (79 tests)
- Full documentation (CLI guide, API reference, architecture)
- Examples for philosophical logic applications

### Features
- O(1) contradiction detection
- Alpha/beta rule prioritization
- Intelligent branch selection
- Early termination strategies
- Subsumption elimination
- Support for Python 3.8+

[1.0.1]: https://github.com/bradleypallen/wkrq/releases/tag/v1.0.1
[1.0.0]: https://github.com/bradleypallen/wkrq/releases/tag/v1.0.0