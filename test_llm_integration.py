#!/usr/bin/env python3
"""Test LLM integration is working correctly."""

from wkrq import (
    ACrQTableau,
    BilateralTruthValue,
    TRUE, FALSE,
    PredicateFormula,
    Constant,
    SignedFormula,
    t, f
)

def mock_llm_evaluator(formula):
    """Mock LLM that knows Socrates is human."""
    formula_str = str(formula)
    
    if formula_str == "Human(socrates)":
        # Socrates is definitely human
        return BilateralTruthValue(positive=TRUE, negative=FALSE)
    elif formula_str == "Robot(socrates)":
        # Socrates is definitely not a robot
        return BilateralTruthValue(positive=FALSE, negative=TRUE)
    else:
        # Unknown - knowledge gap
        return BilateralTruthValue(positive=FALSE, negative=FALSE)

def test_llm_integration():
    """Test that LLM evaluator works correctly."""
    socrates = Constant("socrates")
    human = PredicateFormula("Human", [socrates])
    robot = PredicateFormula("Robot", [socrates])
    
    print("Test 1: t:Human(socrates) with LLM knowing it's true")
    tableau1 = ACrQTableau(
        [SignedFormula(t, human)],
        llm_evaluator=mock_llm_evaluator
    )
    result1 = tableau1.construct()
    print(f"  Satisfiable: {result1.satisfiable} (expected: True)")
    print(f"  Models: {len(result1.models)}")
    if result1.models:
        print(f"  Model: {result1.models[0]}")
    print()
    
    print("Test 2: f:Human(socrates) with LLM knowing it's true")
    tableau2 = ACrQTableau(
        [SignedFormula(f, human)],
        llm_evaluator=mock_llm_evaluator
    )
    result2 = tableau2.construct()
    print(f"  Satisfiable: {result2.satisfiable} (expected: False)")
    print(f"  Closed branches: {result2.closed_branches}")
    print()
    
    print("Test 3: t:Robot(socrates) with LLM knowing it's false")
    tableau3 = ACrQTableau(
        [SignedFormula(t, robot)],
        llm_evaluator=mock_llm_evaluator
    )
    result3 = tableau3.construct()
    print(f"  Satisfiable: {result3.satisfiable} (expected: False)")
    print(f"  Closed branches: {result3.closed_branches}")
    print()

if __name__ == "__main__":
    test_llm_integration()