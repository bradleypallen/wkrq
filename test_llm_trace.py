#!/usr/bin/env python3
"""Trace LLM evaluation to see what's happening."""

from wkrq import (
    ACrQTableau,
    BilateralTruthValue,
    TRUE, FALSE,
    PredicateFormula,
    Constant,
    SignedFormula,
    t
)

def glut_llm_evaluator(formula):
    """Mock LLM that returns a glut for Flying."""
    formula_str = str(formula)
    print(f"      LLM called for: {formula_str}")
    
    if formula_str == "Flying(tweety)":
        # Conflicting evidence - glut
        result = BilateralTruthValue(positive=TRUE, negative=TRUE)
        print(f"      LLM returns: GLUT (pos=TRUE, neg=TRUE)")
        return result
    else:
        result = BilateralTruthValue(positive=FALSE, negative=FALSE)
        print(f"      LLM returns: GAP (pos=FALSE, neg=FALSE)")
        return result

def test_with_trace():
    """Test with trace to see what's happening."""
    tweety = Constant("tweety")
    flying = PredicateFormula("Flying", [tweety])
    
    print("Test: t:Flying(tweety) with LLM returning GLUT")
    print("  Starting with: t:Flying(tweety)")
    print("  LLM should add: t:Flying*(tweety) for the glut")
    print()
    
    tableau = ACrQTableau(
        [SignedFormula(t, flying)],
        llm_evaluator=glut_llm_evaluator,
        trace=True
    )
    result = tableau.construct()
    
    print(f"\n  Result: Satisfiable={result.satisfiable}")
    print(f"  Open branches: {result.open_branches}")
    print(f"  Closed branches: {result.closed_branches}")
    
    # Show trace
    if result.trace:
        print("\n  Trace of rule applications:")
        for step in result.trace.steps[:10]:  # First 10 steps
            print(f"    Step {step.step_number}: {step.rule_name}")
            if step.conclusions:
                for c in step.conclusions[:3]:  # First 3 conclusions
                    print(f"      -> {c}")

if __name__ == "__main__":
    test_with_trace()
