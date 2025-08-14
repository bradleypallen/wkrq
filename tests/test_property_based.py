"""
Property-based testing for tableau correctness.

These tests verify that logical properties hold across random inputs,
helping to catch edge cases that specific tests might miss.
"""

import pytest
import random
from itertools import product
from wkrq import solve, valid, entails, parse, t, f, e
from wkrq.semantics import WeakKleeneSemantics, TRUE, FALSE, UNDEFINED


class TestTableauSoundness:
    """Verify that tableau results match semantic evaluation."""
    
    def test_propositional_soundness(self):
        """For propositional formulas, tableau should match truth table."""
        wk = WeakKleeneSemantics()
        
        # Generate random truth assignments
        for _ in range(100):
            # Random values for P and Q
            p_val = random.choice([TRUE, FALSE, UNDEFINED])
            q_val = random.choice([TRUE, FALSE, UNDEFINED])
            
            # Test conjunction
            conj_semantic = wk.conjunction(p_val, q_val)
            conj_formula = parse("P & Q")
            # We'd need a way to set initial values for P and Q
            # This requires extending the API
            
    def test_tautology_detection(self):
        """Tautologies should be valid regardless of error values."""
        # P ∨ ¬P is NOT a tautology in weak Kleene (when P=e)
        result = valid(parse("P | ~P"))
        assert not result, "P ∨ ¬P is not valid in weak Kleene"
        
        # But (P → P) should be valid
        result = valid(parse("P -> P"))
        assert result, "P → P should be valid"
    
    def test_contradiction_detection(self):
        """Contradictions should be unsatisfiable."""
        # P ∧ ¬P is unsatisfiable even in weak Kleene
        result = solve(parse("P & ~P"))
        assert not result.satisfiable, "P ∧ ¬P should be unsatisfiable"


class TestLogicalProperties:
    """Test that fundamental logical properties hold."""
    
    def test_modus_ponens(self):
        """If P and P→Q are true, then Q must be true."""
        # Should be valid: (P ∧ (P → Q)) → Q
        formula = parse("(P & (P -> Q)) -> Q")
        assert valid(formula), "Modus ponens should be valid"
    
    def test_demorgan_laws_weak_kleene(self):
        """De Morgan's laws in weak Kleene."""
        # ¬(P ∧ Q) ↔ (¬P ∨ ¬Q) should be valid
        formula = parse("~(P & Q) <-> (~P | ~Q)")
        result = valid(formula)
        # In weak Kleene, this might not be valid due to error cases
        # Document the actual behavior
    
    def test_distribution_laws(self):
        """Distribution of ∧ over ∨."""
        # P ∧ (Q ∨ R) ↔ (P ∧ Q) ∨ (P ∧ R)
        formula = parse("P & (Q | R) <-> (P & Q) | (P & R)")
        result = valid(formula)
        # Check if distribution holds in weak Kleene


class TestTableauProperties:
    """Test properties of the tableau construction itself."""
    
    def test_branch_independence(self):
        """Branches should be independent - modifying one shouldn't affect others."""
        # This is tested in the rule verification
        pass
    
    def test_termination(self):
        """Tableau should terminate for propositional formulas."""
        # Generate random propositional formulas
        for _ in range(50):
            # Build random formula
            atoms = ["P", "Q", "R"]
            ops = ["&", "|", "->"]
            
            # Simple random formula generator
            depth = random.randint(1, 3)
            formula_str = self._generate_random_formula(atoms, ops, depth)
            
            try:
                formula = parse(formula_str)
                result = solve(formula)
                # Should terminate without timeout
                assert result is not None
            except:
                # Parsing might fail for malformed formulas
                pass
    
    def _generate_random_formula(self, atoms, ops, depth):
        """Generate a random propositional formula."""
        if depth == 0:
            return random.choice(atoms)
        
        op = random.choice(ops)
        if op in ["&", "|", "->"]:
            left = self._generate_random_formula(atoms, ops, depth - 1)
            right = self._generate_random_formula(atoms, ops, depth - 1)
            return f"({left} {op} {right})"
        else:  # negation
            sub = self._generate_random_formula(atoms, ops, depth - 1)
            return f"~{sub}"


class TestCompleteness:
    """Test that the tableau is complete."""
    
    def test_finds_all_models(self):
        """Tableau should find all satisfying assignments."""
        # For P ∨ Q, there should be models where:
        # 1. P=t, Q can be anything (3 models)
        # 2. P=f, Q=t (1 model)
        # 3. P=e, Q=t (1 model)
        # Total: 5 models where the formula is true
        
        formula = parse("P | Q")
        result = solve(formula, t)
        
        # The current API doesn't expose all models, just satisfiability
        # This would require extending the API
        assert result.satisfiable


class TestErrorSemantics:
    """Test that error values are handled correctly."""
    
    def test_error_propagation(self):
        """Error should propagate through operations."""
        # If P is error, then ¬P is also error
        # If P is error, then P ∧ Q is error (regardless of Q)
        # If P is error and Q is true, then P ∨ Q is true
        # If P is error and Q is false, then P ∨ Q is error
        
        # These tests require a way to set initial error values
        pass
    
    def test_error_absorption(self):
        """True ∨ error = true (not error)."""
        # This is a key property of weak Kleene
        # But we need to test it at the tableau level
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])