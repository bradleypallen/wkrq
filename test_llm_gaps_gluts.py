#!/usr/bin/env python3
"""Test LLM integration with gaps and gluts."""

from wkrq import (
    ACrQTableau,
    BilateralTruthValue,
    TRUE, FALSE,
    PredicateFormula,
    Constant,
    SignedFormula,
    t, f
)

def glut_llm_evaluator(formula):
    """Mock LLM with gluts and gaps."""
    formula_str = str(formula)
    
    if formula_str == "Flying(tweety)":
        # Conflicting evidence - glut
        print(f"    LLM: {formula_str} -> GLUT (both true)")
        return BilateralTruthValue(positive=TRUE, negative=TRUE)
    elif formula_str == "Unknown(tweety)":
        # No evidence - gap
        print(f"    LLM: {formula_str} -> GAP (both false)")
        return BilateralTruthValue(positive=FALSE, negative=FALSE)
    else:
        # Default gap
        print(f"    LLM: {formula_str} -> GAP (unknown)")
        return BilateralTruthValue(positive=FALSE, negative=FALSE)

def test_gaps_and_gluts():
    """Test that LLM evaluator handles gaps and gluts correctly."""
    tweety = Constant("tweety")
    flying = PredicateFormula("Flying", [tweety])
    unknown = PredicateFormula("Unknown", [tweety])
    
    print("Test 1: t:Flying(tweety) with LLM returning GLUT")
    print("  Expected: Satisfiable (ACrQ allows gluts)")
    tableau1 = ACrQTableau(
        [SignedFormula(t, flying)],
        llm_evaluator=glut_llm_evaluator
    )
    result1 = tableau1.construct()
    print(f"  Result: Satisfiable={result1.satisfiable}")
    print(f"  Open branches: {result1.open_branches}")
    print(f"  Closed branches: {result1.closed_branches}")
    if result1.models:
        print(f"  Model: {result1.models[0]}")
    print()
    
    print("Test 2: t:Unknown(tweety) with LLM returning GAP")
    print("  Expected: Should close (gap means cannot verify)")
    tableau2 = ACrQTableau(
        [SignedFormula(t, unknown)],
        llm_evaluator=glut_llm_evaluator
    )
    result2 = tableau2.construct()
    print(f"  Result: Satisfiable={result2.satisfiable}")
    print(f"  Open branches: {result2.open_branches}")
    print(f"  Closed branches: {result2.closed_branches}")
    print()
    
    print("Test 3: f:Unknown(tweety) with LLM returning GAP")
    print("  Expected: Should be satisfiable (gap is consistent with f)")
    tableau3 = ACrQTableau(
        [SignedFormula(f, unknown)],
        llm_evaluator=glut_llm_evaluator
    )
    result3 = tableau3.construct()
    print(f"  Result: Satisfiable={result3.satisfiable}")
    print(f"  Open branches: {result3.open_branches}")
    print(f"  Closed branches: {result3.closed_branches}")
    if result3.models:
        print(f"  Model: {result3.models[0]}")

if __name__ == "__main__":
    test_gaps_and_gluts()
