# Key Implementation Design Decisions

## Overview

This document captures the critical implementation decisions made in the wKrQ/ACrQ tableau system and their theoretical justifications for discussion with Thomas Ferguson.

## Major Design Decisions

### 1. Tree Connectivity Architecture (Version 3.2.0 Fix)

**Decision**: Chain-connect all initial formulas as siblings in tableau tree
**Theoretical Justification**: Ferguson's Definition 9 doesn't specify initial formula arrangement, but observability requires connected tree structure

**Code Location**: `WKrQTableau.__init__()` lines ~150-180
```python
# Connect initial formulas in sequence
for i, signed_formula in enumerate(initial_formulas):
    node = self._create_node(signed_formula) 
    if i == 0:
        self.root = node
    else:
        prev_node.add_child(node)  # Critical: connect to previous
    prev_node = node
```

**Alternative Considered**: All initial formulas as children of dummy root
**Why Current Approach**: Simpler structure, matches Ferguson's implicit tree model

### 2. Meta-sign Expansion Strategy

**Decision**: Explicit expansion of m/n signs for atomic formulas only
**Theoretical Justification**: Required for completeness (modus ponens fails without it)

**Code Location**: Rule application in `wkrq_rules.py`
```python
# m:p → (t:p) | (f:p) for atomic p
# n:p → (f:p) | (e:p) for atomic p  
```

**Ferguson Reference**: Not explicit in paper, but necessary for Definition 9 completeness
**Alternative Considered**: Expand m/n for all formulas (causes infinite loops)
**Why Atomic Only**: Compound formulas have explicit branching rules

### 3. Quantifier Instantiation Strategy

**Decision**: Generate both existing constants AND one fresh constant for n-universal
**Theoretical Justification**: Ensures counterexample finding for invalid inferences

**Code Location**: `n-restricted-forall` rule in `wkrq_rules.py`
```python
# For [∀X P(X)]Q(X) with n sign:
# Branch 1: Try existing constants c₁, c₂, ... 
# Branch 2: Generate fresh constant d
```

**Ferguson Reference**: Implicit in quantifier semantics (Definition 3)
**Alternative Considered**: Only existing constants (misses counterexamples)
**Why Fresh Constants**: Critical for completeness, but limited to one to prevent infinite loops

### 4. Branch Closure Logic

**Decision**: Syntactic contradiction checking only (same formula, different truth-value signs)
**Theoretical Justification**: Matches Ferguson Definition 10 exactly

**Code Location**: `check_closure()` method
```python
# Close on: t:φ and f:φ (or t:φ and e:φ, or f:φ and e:φ)
# Don't close on semantic contradictions like t:(p∨q) with e:p, e:q
```

**Ferguson Reference**: Definition 10 specifies syntactic closure
**Alternative Considered**: Semantic contradiction checking
**Why Syntactic**: Faithful to Ferguson; semantic checking is computationally expensive

### 5. Rule Priority System  

**Decision**: Priority-based deterministic rule application order
**Theoretical Justification**: Ensures reproducible tableau construction

**Code Location**: `RuleInfo` class priority field
```python
# Higher priority = applied first
# Alpha rules before beta rules 
# Negation before complex connectives
```

**Ferguson Reference**: Not specified in paper
**Alternative Considered**: Random rule application order
**Why Deterministic**: Reproducible results, easier debugging/verification

### 6. LLM Integration Architecture

**Decision**: LLM evaluators treated as standard tableau rules with caching
**Theoretical Justification**: Maintains soundness through bilateral-truth package integration

**Code Location**: LLM rule application in tableau construction
**Ferguson Reference**: Extension beyond paper scope
**Key Design**: Use wkrq.llm_integration wrapper to ensure proper bilateral semantics

### 7. Mixed Propositional and First-Order Formulas

**Decision**: Allow mixing propositional atoms and first-order predicates in same tableau
**Theoretical Justification**: Unified tableau engine can process both via Ferguson's sign system

**Code Location**: Formula hierarchy in `formula.py`, tableau initialization
```python
# Currently allowed:
p = Formula.atom("p")  # propositional
human_X = Formula.predicate("Human", [Formula.variable("X")])  # first-order
mixed = p & human_X  # p & Human(X) - mixed formula
```

**Ferguson Reference**: Not explicitly addressed in paper (focuses on pure cases)
**Alternative Considered**: Separate propositional and first-order tableau modes
**Why Current Approach**: Simpler unified architecture, users can combine formula types naturally

**Semantic Concerns**:
- **Domain ambiguity**: What domain are we quantifying over when propositional atoms present?
- **Model extraction complexity**: Mixed domains require careful handling
- **Quantifier scope**: Free variables in mixed formulas can be semantically unclear
- **Variable/constant distinction**: Variables uppercase (X), constants lowercase (socrates)

## Theoretical Tradeoffs

### Completeness vs Termination

**Tradeoff**: Fresh constant generation limited to prevent infinite loops
**Impact**: May miss some validities requiring multiple fresh constants
**Justification**: Practical completeness preferred over theoretical perfection

### Performance vs Semantic Accuracy

**Tradeoff**: Syntactic closure creates spurious models but is fast
**Impact**: Some open branches represent semantically impossible situations  
**Justification**: Maintains soundness (crucial) while improving performance

### Observability vs Simplicity

**Tradeoff**: Tree connectivity adds complexity but enables verification
**Impact**: More complex initialization logic
**Justification**: Observable properties essential for validation and debugging

## Questions for Thomas Ferguson Discussion

### 1. Meta-sign Expansion
- Is atomic-only expansion the intended interpretation?
- Should compound formulas with m/n also expand?
- Performance vs completeness tradeoffs?

### 2. Fresh Constant Strategy
- Is one fresh constant per n-universal sufficient for most cases?
- Should we generate more fresh constants in specific scenarios?
- How to balance completeness with termination?

### 3. Semantic Closure
- Should the system check semantic contradictions beyond syntactic ones?
- Would this violate Ferguson's Definition 10 specification?
- Performance impact acceptable?

### 4. Rule Application Order
- Any preferred deterministic ordering of rules?
- Should certain rules have priority over others?
- Impact on tableau structure and verification?

### 5. Mixed Propositional and First-Order Formulas
- Should the system allow mixing propositional atoms and first-order predicates?
- What are the semantic implications for domain construction and model extraction?
- Should users be warned about potential semantic ambiguities?
- How should quantifier scope be handled with free variables in mixed contexts?

### 6. Branch Closure Edge Cases
- Any ambiguous cases in Definition 10?
- How should meta-signs interact with closure conditions?
- ACrQ glut handling vs wKrQ standard closure?

## Implementation Quality Assessment

### Strengths
- **Ferguson Compliance**: Direct implementation of Definitions 9, 10, 18
- **Soundness**: All rules preserve semantic validity
- **Observability**: Tree structure enables complete verification
- **Extensibility**: Clean architecture supports ACrQ and LLM extensions

### Areas for Improvement  
- **Semantic Completeness**: Could add semantic contradiction checking
- **Fresh Constant Strategy**: Could be more sophisticated
- **Performance**: Some optimizations possible for large domains
- **Documentation**: More explicit mapping to Ferguson definitions

### Critical Success Factors
1. **Rule Correctness**: Each rule must preserve validity
2. **Closure Soundness**: Only close on genuine contradictions  
3. **Model Extraction**: Open branches must yield valid models
4. **Observable Verification**: All properties must be user-verifiable

This analysis should help guide the code walkthrough discussion with Thomas Ferguson.