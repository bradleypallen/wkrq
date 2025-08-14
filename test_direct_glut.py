#!/usr/bin/env python3
"""Test gluts directly without LLM."""

from wkrq import (
    ACrQTableau,
    PredicateFormula,
    BilateralPredicateFormula,
    Constant,
    SignedFormula,
    t
)

def test_direct_glut():
    """Test that ACrQ allows gluts."""
    tweety = Constant("tweety")
    
    # Create bilateral predicates
    flying_pos = BilateralPredicateFormula(
        positive_name="Flying",
        terms=[tweety],
        is_negative=False
    )
    flying_neg = BilateralPredicateFormula(
        positive_name="Flying",
        terms=[tweety],
        is_negative=True
    )
    
    print("Test: t:Flying(tweety) AND t:Flying*(tweety) (direct glut)")
    print("  Expected: Satisfiable in ACrQ")
    
    tableau = ACrQTableau(
        [SignedFormula(t, flying_pos), SignedFormula(t, flying_neg)],
    )
    result = tableau.construct()
    
    print(f"  Result: Satisfiable={result.satisfiable}")
    print(f"  Open branches: {result.open_branches}")
    print(f"  Closed branches: {result.closed_branches}")
    if result.models:
        print(f"  Model: {result.models[0]}")

if __name__ == "__main__":
    test_direct_glut()
