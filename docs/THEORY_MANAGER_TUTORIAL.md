# ACrQ-LLM Theory Manager Tutorial - wKrQ v3.3.2

A comprehensive guide to using the ACrQ Theory Manager with LLM integration for paraconsistent reasoning.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation & Setup](#installation--setup)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Basic Commands](#basic-commands)
6. [Working with Formulas](#working-with-formulas)
7. [Inference and Reasoning](#inference-and-reasoning)
8. [Managing Theory Files](#managing-theory-files)
9. [LLM Integration](#llm-integration)
10. [Advanced Workflows](#advanced-workflows)
11. [Examples](#examples)
12. [Troubleshooting](#troubleshooting)
13. [Reference](#reference)

## Introduction

The Theory Manager is an interactive command-line interface for building, testing, and reasoning with logical theories using ACrQ (AC with Restricted Quantification) - a paraconsistent logic that can handle contradictory information without explosion.

### Key Features

- **Natural language assertions** - State facts in plain English
- **Automatic formula translation** - Converts natural language to logical formulas
- **Paraconsistent reasoning** - Handles contradictions gracefully
- **Gap and glut detection** - Identifies missing and conflicting information
- **Persistent storage** - Save and load theories as JSON files
- **LLM integration** - Query language models for factual evidence
- **Inference engine** - Derives new facts from existing knowledge

## Installation & Setup

### Prerequisites

```bash
# Requires Python 3.8+
python --version

# Install wKrQ package
pip install wkrq
```

### Starting the Theory Manager

```bash
# Start interactive ACrQ theory manager with LLM support
acrq-llm

# Start with a specific theory file
acrq-llm --file my_theory.json

# Start with LLM provider configured
acrq-llm --llm openai
```

## Quick Start

Here's a simple example to get you started:

```
ACrQ Theory Manager - wkrq version 3.3.2
Type 'help' for available commands.

theory> assert Socrates is human
Added: S0001 t:Human(socrates)

theory> assert All humans are mortal
Added: S0002 t:[forall X Human(X)](Mortal(X))

theory> infer
Running inference...
New facts inferred:
  I0003 t:Mortal(socrates)

theory> check
Satisfiable

theory> save philosophy.json
Theory saved to philosophy.json
```

## Core Concepts

### Statements

Each statement in a theory has:
- **ID**: Unique identifier (S#### for assertions, I#### for inferences, E#### for LLM evidence)
- **Natural language**: Human-readable description
- **Formula**: Logical representation
- **Sign**: Truth value (t=true, f=false, e=undefined)
- **Metadata**: Source, timestamp, and other information

### Signs in ACrQ

- `t` - True (definitely true)
- `f` - False (definitely false)
- `e` - Error/undefined (no truth value)
- `m` - Meaningful (true or false, not undefined)
- `n` - Non-true (false or undefined)
- `v` - Variable (any value possible)

### Bilateral Predicates

ACrQ uses bilateral predicates to handle negative evidence:
- `P(x)` - Positive evidence for P
- `P*(x)` - Negative evidence for P (star syntax)

This allows four information states:
- **True**: `t:P(x)` and `f:P*(x)`
- **False**: `f:P(x)` and `t:P*(x)`
- **Gap**: Neither P(x) nor P*(x) has evidence
- **Glut**: Both `t:P(x)` and `t:P*(x)` (contradiction)

## Basic Commands

### Assertions

```
# Assert a fact in natural language
theory> assert Birds can fly
Added: S0001 t:CanFly(birds)

# Assert with explicit formula
theory> assert formula Human(socrates)
Added: S0002 t:Human(socrates)

# Assert negative evidence (bilateral predicate)
theory> assert formula Human*(alien)
Added: S0003 t:Human*(alien)

# Assert with specific sign
theory> assert f:IsEven(3)
Added: S0004 f:IsEven(3)
```

### Claims (LLM-Verified Assertions)

The `claim` command is like `assert` but verifies atomic facts with an LLM first:

```
# Claim a fact - LLM verifies before asserting
theory> claim firstManOnTheMoon(armstrong)
Verifying claim with LLM: firstManOnTheMoon(armstrong)
Using: openai / gpt-4
✓ Claimed: S0005
  Sign: t
  Formula: firstManOnTheMoon(armstrong)
  LLM verdict: TRUE (verified by LLM)

# False claims get refuted
theory> claim firstManOnTheMoon(scott)
Verifying claim with LLM: firstManOnTheMoon(scott)
Using: openai / gpt-4
✓ Claimed: S0006
  Sign: f
  Formula: firstManOnTheMoon(scott)
  LLM verdict: FALSE (refuted by LLM)

# Compound formulas can't be verified
theory> claim P(x) & Q(y)
Note: Compound formula cannot be verified with LLM, asserting as true
Added: S0007 t:P(x) & Q(y)

# Without LLM, behaves like assert
theory> claim Human(socrates)  # (if no LLM configured)
Note: No LLM evaluator available, treating as regular assertion
Added: S0008 t:Human(socrates)
```

### Listing Statements

```
# List all statements
theory> list
Current statements:
  S0001 t:CanFly(birds) - "Birds can fly"
  S0002 t:Human(socrates) - "Human(socrates)"
  S0003 t:Human*(alien) - "Human*(alien)"
  S0004 f:IsEven(3) - "f:IsEven(3)"

# List only inferred statements
theory> list --inferred
Inferred statements:
  (none)
```

### Retracting Statements

```
# Retract single statement
theory> retract S0003
Retracted: S0003

# Retract multiple statements
theory> retract S0001 S0004
Retracted: S0001
Retracted: S0004

# Retract all inferred statements
theory> retract --inferred
Retracted all inferred statements (0 removed)
```

## Working with Formulas

### Assert vs Claim

The theory manager provides two ways to add statements:

- **`assert`** - Traditional logical assertion, taken as given truth
  - Used for axioms, rules, and logical facts
  - Example: `assert All humans are mortal`
  
- **`claim`** - Factual claim verified by LLM before assertion  
  - Used for real-world facts that can be checked
  - Only works for atomic formulas (predicates and propositions)
  - Requires LLM provider to be configured
  - Example: `claim firstManOnTheMoon(armstrong)` → verified as TRUE
  - Example: `claim firstManOnTheMoon(scott)` → refuted as FALSE

### Natural Language Translation

The system attempts to translate natural language to logical formulas:

```
theory> assert The sky is blue
Added: S0001 t:Blue(sky)

theory> assert All cats are animals
Added: S0002 t:[forall X Cat(X)](Animal(X))

theory> assert Some dogs bark
Added: S0003 t:[exists X Dog(X)](Bark(X))
```

### Direct Formula Input

For precise control, use explicit formulas:

```
# Propositional logic
theory> assert formula P & Q
Added: S0001 t:P & Q

# Predicate logic
theory> assert formula Human(x) | Robot(x)
Added: S0002 t:Human(x) | Robot(x)

# Quantified formulas
theory> assert formula [forall X P(X)](Q(X))
Added: S0003 t:[forall X P(X)](Q(X))

# Bilateral predicates (negative evidence)
theory> assert formula Human*(x)
Added: S0004 t:Human*(x)
```

### Complex Formulas

```
# Nested quantifiers
theory> assert formula [forall X Person(X)]([exists Y Parent(Y,X)](Loves(Y,X)))
Added: S0001 t:[forall X Person(X)]([exists Y Parent(Y,X)](Loves(Y,X)))

# Mixed connectives
theory> assert formula (P(a) & Q(b)) -> (R(c) | S(d))
Added: S0002 t:(P(a) & Q(b)) -> (R(c) | S(d))

# Negation
theory> assert formula ~Happy(monday)
Added: S0003 t:Happy*(monday)  # Automatically converted to bilateral
```

## Inference and Reasoning

### Running Inference

```
theory> assert Human(socrates)
Added: S0001 t:Human(socrates)

theory> assert [forall X Human(X)](Mortal(X))
Added: S0002 t:[forall X Human(X)](Mortal(X))

theory> infer
Running inference...
New facts inferred:
  I0003 t:Mortal(socrates)
```

### Checking Satisfiability

```
theory> check
Satisfiable

# After adding contradiction
theory> assert formula Van(c435)
Added: S0004 t:Van(c435)

theory> assert formula Van*(c435)
Added: S0005 t:Van*(c435)

theory> check
Satisfiable with 1 glut:
  Van(c435) and Van*(c435)
```

### Understanding Gaps and Gluts

**Gaps** - Missing information:
```
theory> assert formula [forall X Bird(X)](CanFly(X))
theory> assert formula Bird(penguin)
theory> infer
# CanFly(penguin) is inferred even though penguins can't fly
# This is a gap in our knowledge about penguin flight
```

**Gluts** - Conflicting information:
```
theory> assert formula Tall(john)
Added: S0001 t:Tall(john)

theory> assert formula Tall*(john)
Added: S0002 t:Tall*(john)

theory> check
Satisfiable with 1 glut:
  Tall(john) and Tall*(john)
```

## Managing Theory Files

### Saving Theories

```
# Save current theory
theory> save my_theory.json
Theory saved to my_theory.json
```

### Loading Theories

```
# Load a theory file
theory> load my_theory.json
Loaded 5 statements from my_theory.json

# Loading protects the file from accidental overwrite
theory> clear
Theory cleared
```

### Theory File Format

```json
{
  "metadata": {
    "version": "1.0",
    "created": "2025-08-24T10:30:00.000000",
    "next_id": 6
  },
  "statements": [
    {
      "id": "S0001",
      "natural_language": "Socrates is human",
      "formula": "Human(socrates)",
      "sign": "t",
      "is_inferred": false,
      "timestamp": "2025-08-24T10:30:00.000000",
      "metadata": {
        "source": "user_assertion"
      }
    }
  ]
}
```

## LLM Integration

### Setting up LLM Provider

```bash
# Set API key for your provider
export OPENAI_API_KEY=your-key-here
# or
export ANTHROPIC_API_KEY=your-key-here
```

### Querying LLM for Evidence

```
theory> llm Paris is the capital of France
Querying LLM...
Added: E0001 t:Capital(paris, france) (Source: gpt-4)

theory> llm The moon is made of cheese
Querying LLM...
Added: E0002 t:MadeOf*(moon, cheese) (Source: gpt-4)
```

### Available LLM Providers

- OpenAI (gpt-4, gpt-3.5-turbo)
- Anthropic (claude-3-opus, claude-3-sonnet)
- OpenRouter (various models)
- Mock (for testing)

## Advanced Workflows

### Contradiction Analysis

```
# Load a theory with potential contradictions
theory> load vehicle_types.json

theory> assert c435 is a Sedan
theory> assert c435 is a Van
theory> assert Sedans are not Vans

theory> check
Satisfiable with 1 glut:
  Van(c435) and Van*(c435)

theory> report
Theory Report
=============
Total statements: 3
- User assertions: 3
- Inferred facts: 0

Gluts detected: 1
- Van(c435) and Van*(c435)
```

### Incremental Theory Building

```
# Start with basic facts
theory> assert All humans are mortal
theory> assert Socrates is human
theory> infer

# Add exceptions
theory> assert formula Vampire(dracula)
theory> assert formula Human(dracula) & ~Mortal(dracula)
theory> check
# System handles the exception without explosion

# Save checkpoint
theory> save checkpoint1.json
```

### Hypothetical Reasoning

```
# Test a hypothesis
theory> assert formula Hypothesis(rain_tomorrow)
theory> assert formula [forall X Hypothesis(X)](Umbrella(needed))
theory> infer
# See consequences

# Retract hypothesis
theory> retract S0001 S0002
theory> list
# Back to original state
```

## Examples

### Example 1: Animal Taxonomy

```
theory> assert All dogs are animals
theory> assert All cats are animals  
theory> assert Fido is a dog
theory> assert Whiskers is a cat
theory> assert Dogs bark
theory> assert Cats meow

theory> infer
New facts inferred:
  I0007 t:Animal(fido)
  I0008 t:Animal(whiskers)

theory> check
Satisfiable
```

### Example 2: Traffic Incident (Paraconsistent)

```
theory> load example13_accident.json
theory> list

Current statements:
  S0001 t:Sedan(c435) - "c435 is a Sedan"
  S0002 t:Van(c435) - "c435 is a Van"
  S0003 t:[forall X Sedan(X)](Van*(X)) - "Sedan is equivalent to not Van"
  
theory> infer
New facts inferred:
  I0004 t:Van*(c435)

theory> check
Satisfiable with 1 glut:
  Van(c435) and Van*(c435)
```

### Example 3: Knowledge Base with LLM

```
theory> assert Paris is a city
theory> assert London is a city
theory> llm Paris is the capital of France
Added: E0003 t:Capital(paris, france)

theory> llm London is the capital of England  
Added: E0004 t:Capital(london, england)

theory> assert formula [forall X,Y Capital(X,Y)](Important(X))
theory> infer
New facts inferred:
  I0005 t:Important(paris)
  I0006 t:Important(london)
```

## Troubleshooting

### Common Issues

#### Parse Errors

**Problem**: "PARSE ERROR: unexpected character"
```
theory> assert The temperature is 75°F
Parse error: unexpected character '°'
```

**Solution**: Use simpler language or explicit formulas
```
theory> assert The temperature is 75 degrees
# or
theory> assert formula Temperature(75, fahrenheit)
```

#### Formula Translation Failures

**Problem**: Natural language doesn't translate correctly
```
theory> assert It will rain tomorrow
Added: S0001 t:// PARSE ERROR: It will rain tomorrow
```

**Solution**: Use explicit formulas for complex statements
```
theory> assert formula WillRain(tomorrow)
```

#### Star Syntax Issues

**Problem**: "Star syntax (P*) is not allowed"

**Solution**: The system now uses Mixed mode by default, but if you encounter issues:
```
# Negative evidence should work automatically
theory> assert formula ~Human(robot)
Added: S0001 t:Human*(robot)

# Or use explicit bilateral predicate
theory> assert formula Human*(robot)
Added: S0001 t:Human*(robot)
```

#### Unexpected Inferences

**Problem**: System infers facts that seem wrong

**Solution**: Check your axioms for overgeneralization
```
theory> list
# Look for universal statements that might be too broad
# Add exceptions or more specific conditions
```

### Getting Help

```
# Show all commands
theory> help

# Show specific command help  
theory> help assert
assert <statement> - Add a natural language or formula statement

# Exit theory manager
theory> exit
```

## Reference

### Command Summary

| Command | Description | Example |
|---------|-------------|---------|
| `assert` | Add a statement | `assert Birds fly` |
| `claim` | Assert with LLM verification | `claim firstManOnTheMoon(armstrong)` |
| `retract` | Remove statement(s) | `retract S0001 S0002` |
| `list` | Show all statements | `list --inferred` |
| `check` | Check satisfiability | `check` |
| `infer` | Run inference engine | `infer` |
| `report` | Show theory summary | `report` |
| `save` | Save theory to file | `save theory.json` |
| `load` | Load theory from file | `load theory.json` |
| `clear` | Clear all statements | `clear` |
| `llm` | Set up LLM provider | `llm openai` |
| `evaluate` | Test LLM evaluation | `evaluate Planet(pluto)` |
| `help` | Show help | `help assert` |
| `exit` | Exit theory manager | `exit` |

### Statement ID Prefixes

- `S####` - User assertions (source: user_assertion)
- `I####` - Inferred facts (source: tableau_inference)  
- `E####` - LLM evidence (source: llm_evidence)

### File Locations

Default save location: Current working directory
Theory files: Saved in JSON format with .json extension

### Best Practices

1. **Start simple** - Build theories incrementally
2. **Test frequently** - Run `check` and `infer` often
3. **Save checkpoints** - Save working theories before major changes
4. **Use explicit formulas** - When natural language translation fails
5. **Document assertions** - Natural language helps readability
6. **Handle contradictions** - ACrQ is paraconsistent, contradictions are OK
7. **Verify inferences** - Check that inferred facts make sense

## Conclusion

The Theory Manager provides a powerful environment for exploring logical theories with paraconsistent reasoning. Its ability to handle contradictions without explosion makes it ideal for real-world knowledge representation where conflicting information is common.

For more information:
- [wKrQ Documentation](https://github.com/bradleyallen/wkrq)
- [ACrQ Paper (Ferguson 2021)](https://link.to.paper)
- [API Reference](./API.md)