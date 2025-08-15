# wKrQ Examples

This directory contains essential examples demonstrating the wKrQ and ACrQ tableau systems.

## Core Examples

### 1. Basic wKrQ Operations (`01_basic_wkrq.py`)
- Three-valued logic fundamentals
- Weak Kleene undefined contagion
- Valid and invalid inferences
- Classical principles that fail in weak Kleene
- Model finding and counterexamples

### 2. Restricted Quantifier Reasoning (`02_quantifier_reasoning.py`)
- Ferguson's restricted quantification syntax
- Valid quantifier inferences (universal instantiation, existential generalization)
- Invalid inferences critical for soundness
- Domain-specific reasoning examples
- Tests Ferguson Definition 11 implementation

### 3. ACrQ Bilateral Predicates (`03_acrq_bilateral.py`)
- Three parsing modes (Transparent, Bilateral, Mixed)
- Four information states (true, false, gap, glut)
- Paraconsistent reasoning (gluts don't explode)
- DeMorgan transformations in ACrQ
- Practical belief revision examples

### 4. LLM Integration (`04_llm_integration.py`)
- Integration with bilateral-truth package
- Real-world knowledge evaluation
- Bilateral truth values from LLMs
- Knowledge base validation
- Requires: `pip install bilateral-truth`

### 5. Ferguson Compliance Validation (`wkrq_validation_demo.py`)
- Comprehensive demonstration of Ferguson (2021) compliance
- Six-sign system explanation
- All tableau rules with examples
- Classical syllogisms testing
- Interactive walkthrough of formal specifications

## Running the Examples

Basic usage:
```bash
python 01_basic_wkrq.py
python 02_quantifier_reasoning.py
python 03_acrq_bilateral.py
python 04_llm_integration.py
```

For the validation demo:
```bash
# Interactive mode (with pauses between sections)
python wkrq_validation_demo.py

# Non-interactive mode
python wkrq_validation_demo.py --no-pause
```

## Requirements

All examples work with the base wKrQ installation except:
- `04_llm_integration.py` requires `bilateral-truth` package
- For real LLM evaluation, set one of:
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `GOOGLE_API_KEY`

## Archive

The `archive/` directory contains additional examples, debug traces, and test files that may be useful for development but are not essential for understanding the system.