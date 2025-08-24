# Theory Management System

## Overview

The Theory Management System provides a complete framework for building and reasoning with knowledge bases using natural language input and ACrQ's paraconsistent logic. It bridges the gap between human-readable statements and formal logical reasoning.

## Key Features

### 1. Natural Language Input
Express knowledge in plain English:
```python
manager.assert_statement("Socrates is a human")
manager.assert_statement("All humans are mortal")
```

### 2. Automatic Translation to ACrQ
Natural language is automatically translated to logical formulas:
- "Socrates is a human" → `Human(socrates)`
- "All humans are mortal" → `[forall X Human(X)]Mortal(X)`
- "Pluto is not a planet" → `~Planet(pluto)`

### 3. Persistent Storage
Theories are saved as JSON files for easy sharing and versioning:
```json
{
  "metadata": {
    "version": "1.0",
    "created": "2025-08-24T...",
    "next_id": 5
  },
  "statements": [
    {
      "id": "S0001",
      "natural_language": "Socrates is a human",
      "formula": "Human(socrates)",
      "is_inferred": false,
      "timestamp": "2025-08-24T..."
    }
  ]
}
```

### 4. Gap and Glut Detection

The system automatically detects:
- **Gaps**: Missing knowledge (neither positive nor negative evidence)
- **Gluts**: Conflicting evidence (both positive and negative evidence)

```python
satisfiable, info_states = manager.check_satisfiability()

gluts = [s for s in info_states if s.state == 'glut']
gaps = [s for s in info_states if s.state == 'gap']
```

### 5. Inference Engine
Derive new facts from existing knowledge:
```python
inferred = manager.infer_consequences()
# Automatically adds inferred statements to the theory
```

### 6. LLM Integration
Enhance reasoning with real-world knowledge:
```python
from wkrq.llm_integration import create_llm_tableau_evaluator

llm_evaluator = create_llm_tableau_evaluator('openai')
manager = TheoryManager(llm_evaluator=llm_evaluator)
```

## Interactive CLI

The system includes a full-featured command-line interface with slash commands:

```bash
python -m wkrq.theory_cli
```

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/assert <statement>` | Add a natural language statement | `/assert Socrates is mortal` |
| `/retract <id>` | Remove a statement | `/retract S0001` |
| `/list [asserted]` | Show all or only asserted statements | `/list` |
| `/check` | Check satisfiability and find gluts/gaps | `/check` |
| `/infer` | Derive new statements | `/infer` |
| `/report` | Generate comprehensive analysis | `/report` |
| `/clear` | Clear all statements | `/clear` |
| `/save [file]` | Save theory to file | `/save my_theory.json` |
| `/load [file]` | Load theory from file | `/load my_theory.json` |
| `/llm <provider>` | Enable LLM evaluator | `/llm openai` |
| `/help` | Show help | `/help` |
| `/quit` | Exit | `/quit` |

## Usage Examples

### Basic Theory Building

```python
from wkrq import TheoryManager

# Create a theory manager
manager = TheoryManager()

# Assert some facts
manager.assert_statement("Tweety is a bird")
manager.assert_statement("Tweety is a penguin")
manager.assert_statement("All birds can fly")
manager.assert_statement("Penguins cannot fly")  # Conflict!

# Check satisfiability
satisfiable, info_states = manager.check_satisfiability()

# Find gluts (conflicting evidence)
gluts = [s for s in info_states if s.state == 'glut']
if gluts:
    print(f"Found {len(gluts)} conflicts")
```

### Advanced Reasoning with Quantifiers

```python
# Universal rules
manager.assert_statement("All humans are mortal")
manager.assert_statement("Socrates is a human")

# Infer consequences
inferred = manager.infer_consequences()
# Automatically infers: Mortal(socrates)
```

### Detecting Information States

```python
def analyze_theory(manager):
    """Analyze a theory for information states."""
    satisfiable, info_states = manager.check_satisfiability()
    
    # Categorize by state
    states_by_type = {
        'true': [],
        'false': [],
        'glut': [],
        'gap': []
    }
    
    for state in info_states:
        states_by_type[state.state].append(state)
    
    # Report
    print(f"Theory is {'satisfiable' if satisfiable else 'unsatisfiable'}")
    print(f"True facts: {len(states_by_type['true'])}")
    print(f"False facts: {len(states_by_type['false'])}")
    print(f"Gluts (conflicts): {len(states_by_type['glut'])}")
    print(f"Gaps (unknown): {len(states_by_type['gap'])}")
    
    return states_by_type
```

## Natural Language Patterns

The translator supports these patterns:

### Simple Predicates
- "X is a Y" → `Y(x)`
- "X is Y" → `Y(x)`

### Negations
- "X is not a Y" → `~Y(x)`
- "X is not Y" → `~Y(x)`

### Relations
- "X loves Y" → `Loves(x, y)`
- "X orbits Y" → `Orbits(x, y)`

### Conditionals
- "if X is a Y then X is a Z" → `Y(x) -> Z(x)`

### Universal Quantification
- "all Xs are Ys" → `[forall X X(X)]Y(X)`
- "every X is a Y" → `[forall X X(X)]Y(X)`

### Existential Quantification
- "some X is a Y" → `[exists X X(X)]Y(X)`
- "there exists an X that is a Y" → `[exists X X(X)]Y(X)`

### Conjunctions
- "X is a Y and a Z" → `Y(x) & Z(x)`

### Disjunctions
- "X is a Y or a Z" → `Y(x) | Z(x)`

## Architecture

### Core Components

1. **TheoryManager**: Main class for managing statements and reasoning
2. **NaturalLanguageTranslator**: Converts NL to ACrQ formulas
3. **Statement**: Data class for theory statements
4. **InformationState**: Represents gaps, gluts, and truth values
5. **TheoryCLI**: Interactive command-line interface

### Workflow

```
Natural Language Input
        ↓
   Translation
        ↓
  ACrQ Formula
        ↓
  Theory Storage
        ↓
  Tableau Reasoning
        ↓
Gap/Glut Detection
        ↓
    Inference
        ↓
  Update Theory
```

## Benefits

1. **Human-Friendly**: Work with natural language, not complex formulas
2. **Paraconsistent**: Handle conflicting information without explosion
3. **Persistent**: Save and share knowledge bases
4. **Extensible**: Integrate with LLMs for real-world knowledge
5. **Interactive**: Manage theories through intuitive commands
6. **Analytical**: Automatically detect gaps and conflicts in knowledge

## Future Enhancements

- [ ] Advanced NL translation using LLMs
- [ ] Web interface for theory management
- [ ] Collaborative theory editing
- [ ] Theory merging and conflict resolution
- [ ] Explanation generation for inferences
- [ ] Theory visualization graphs
- [ ] Export to other logical formats