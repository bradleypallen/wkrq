# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2025-08-01

### Fixed

- **Documentation Organization** - Moved ACrQ documentation files to proper docs directory
  - Relocated `ACRQ_DEVELOPMENT_STATE.md` and `ACRQ_QUICK_START.md` from root to `docs/` directory
  - Maintains consistent documentation structure with all documentation files in `docs/` except `README.md` and `CONTRIBUTING.md`

## [1.1.0] - 2025-08-01

### Added

- **ACrQ Core Implementation** - First phase of Analytic Containment with restricted Quantification support
  - `BilateralPredicateFormula` class for R/R* bilateral predicate pairs
  - `BilateralTruthValue` class supporting four information states (true, false, gap, glut)
  - Basic ACrQ parser with transparent mode supporting Ferguson's ¬P(x) → P*(x) translation
  - Comprehensive bilateral predicate test suite (16 tests)
  - Foundation for paraconsistent and paracomplete reasoning
- **ACrQ Parser Infrastructure**
  - `parse_acrq_formula()` function with syntax mode support
  - `SyntaxMode` enum with TRANSPARENT, BILATERAL, and MIXED modes (transparent mode implemented)
  - Automatic translation of negated predicates to bilateral form in transparent mode
- **Development State Documentation**
  - `ACRQ_DEVELOPMENT_STATE.md` for tracking implementation progress
  - `ACRQ_QUICK_START.md` for easy development resumption

### Changed

- Updated package version to 1.1.0 to reflect significant new functionality
- Enhanced package structure to support ACrQ development alongside existing wKrQ

### Fixed

- **Documentation URLs** - Fixed relative URLs in documentation to work correctly on PyPI
  - Converted all docs/*.md links to absolute GitHub URLs
  - Updated LICENSE link to absolute GitHub URL
- **Documentation Structure** - Fixed table of contents in wKrQ_ARCHITECTURE.md to match actual sections
- **Code Quality** - Resolved ruff C901 complexity warnings through method refactoring
  - Refactored `_eval_compound` method in ACrQ semantics into separate logical operator methods
  - Refactored `_get_acrq_rule` method in ACrQ tableau into specialized bilateral predicate handling methods
  - Refactored main CLI function into separate argument parsing and mode handling functions
- **Type Annotations** - Resolved all mypy type annotation issues in ACrQ implementation

## [1.0.9] - 2025-01-30

### Added

- **ACrQ Implementation Guide** - Comprehensive implementation plan for extending wKrQ with Analytic Containment
  - Added `docs/ACrQ_IMPLEMENTATION_GUIDE.md` with complete architectural design for bilateral predicates
  - 5-phase implementation strategy for paraconsistent and paracomplete reasoning
  - External system integration framework for pluggable bilateral valuation providers
  - Detailed tableau rules for ACrQ with bilateral predicate support
  - Testing strategy and migration path preserving backward compatibility
- **Enhanced CLAUDE.md** with ACrQ architecture overview and development workflow guidance

### Documentation

- **Future Extension Planning** - Detailed roadmap for ACrQ (Analytic Containment with restricted Quantification)
  - Bilateral predicates (R/R*) for independent positive/negative evidence tracking
  - Knowledge glut and knowledge gap handling for robust real-world reasoning
  - Ferguson's translation framework from wKrQ to ACrQ systems
  - Model extraction supporting bilateral valuations and consistency checking

## [1.0.6] - 2025-01-29

### Added

- **Comprehensive Ferguson (2021) validation** with complete theoretical
  analysis
  - Created `FERGUSON_2021_ANALYSIS.md` documenting implementation
    correctness against academic literature
  - 17 Ferguson compliance tests validating truth tables, validity
    definitions, and sign systems
  - 37 semantic validation tests covering weak Kleene truth tables and
    epistemic reasoning
- **Corrected semantic understanding** based on Ferguson's hybrid system
  - Ferguson uses classical validity (truth preservation) with weak Kleene semantics
  - Classical tautologies ARE valid in Ferguson's system (corrected
    documentation)
  - Four-sign system (T, F, M, N) properly validated against Ferguson's Definition 9

### Fixed

- **Corrected failing semantic validation tests** that were based on
  incorrect assumptions
  - Fixed `test_law_of_excluded_middle_ferguson_behavior` to expect
    F:(p ∨ ¬p) unsatisfiable
  - Fixed `test_material_conditional_properties_ferguson_behavior` for
    classical tautology behavior
  - Fixed `test_epistemic_vs_truth_functional_distinction` for contradiction handling
- **Code quality improvements**
  - Fixed all ruff linting issues (trailing whitespace, formatting)
  - All 193 tests now pass with comprehensive coverage

### Changed

- **Updated documentation** to reflect Ferguson's actual specifications
  - Corrected README.md Python API example explaining tautology validity
  - Added reference to Ferguson analysis documentation
  - Updated performance claims to remove inappropriate subsumption references

### Validated

- **Complete theoretical correctness** confirmed against Ferguson (2021)
  - ✅ Weak Kleene truth tables with contagious undefined values
  - ✅ Classical validity through truth preservation
  - ✅ Four-sign tableau system with epistemic uncertainty support
  - ✅ Restricted quantification for practical knowledge representation
  - ✅ Sound and complete tableau calculus (Ferguson's Theorems 1-2)

## [1.0.5] - 2025-01-29

### Removed

- **Complete subsumption system removal** after discovering it was
  inappropriate for tableau calculus
  - Removed all subsumption-related methods and data structures
  - Created `TABLEAU_OPTIMIZATIONS.md` to preserve knowledge of legitimate optimizations
  - Fixed universal quantifier inference that was broken by subsumption interference

### Bug Fixes

- **Quantifier reasoning restoration** with proper universal instantiation
  - Basic universal quantifier inference now works correctly
  - Fixed modus ponens with universal quantifiers:
    `[∀X Human(X)]Mortal(X), Human(socrates) |- Mortal(socrates)`
  - Restored unification-based witness selection for existential quantifiers

## [1.0.4] - 2025-01-29

### Performance Fixes

- **Performance regression correction** from GitHub Actions test failures
- **Black code formatting** issues resolved
- **Quantifier test cascade failure** addressed

## [1.0.3] - 2025-01-29

### Performance Features  

- **Performance optimization attempts** (later determined to be inappropriate)
- **Fast-path logic** for common cases
- **Complexity thresholds** for optimization triggers

## [1.0.2] - 2025-01-29

### Optimizations

- **Complete subsumption optimization system** for tableau theorem
  proving
  - Propositional subsumption: stronger formulas subsume weaker ones
    (e.g., `p` subsumes `p ∨ q`)
  - First-order subsumption: universals subsume instances with
    consistency checking (e.g., `P(X)` subsumes `P(a)`)
  - Three-valued logic subsumption: sign relationships based on truth
    value sets (e.g., `T:p` subsumes `M:p`)
- **Industrial-grade tableau optimizations**
  - Forward subsumption filtering: incoming subsumed formulas are rejected
  - Backward subsumption marking: existing formulas marked as subsumed
    when stronger ones are added
  - Rule application optimization: subsumed formulas skipped during expansion
- **Comprehensive test coverage** with 27 new subsumption tests
- **Performance benchmarking** showing significant optimization benefits
- **Soundness preservation** ensuring tableau correctness while optimizing performance

### Performance

- Sub-millisecond subsumption detection (~0.015ms propositional,
  ~0.003ms first-order)
- Optimized tableau construction with redundancy elimination
- Reduced memory usage through intelligent formula filtering

## [1.0.1] - 2025-01-28

### Improvements

- Added proper academic citation to Thomas Ferguson's TABLEAUX 2021 paper
- Added research software disclaimer
- Clarified documentation to indicate this is an implementation of a
  semantic tableau calculus
- Fixed version numbers from 2.0 to 1.0.0 throughout codebase
- Updated Python requirement from 3.8+ to 3.9+
- Fixed all code quality issues (mypy, ruff, black)
- Adjusted performance test timing thresholds for CI environments

### Additional Fixes

- Fixed deprecated license format in pyproject.toml
- Fixed deprecated typing imports (List → list, etc.)
- Fixed mypy type checking errors across all modules
- Fixed CLI to use version from **init**.py

## [1.0.0] - 2025-01-28

### Initial Features

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
