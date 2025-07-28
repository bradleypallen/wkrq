# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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