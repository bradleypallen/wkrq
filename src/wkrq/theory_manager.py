#!/usr/bin/env python3
"""
Theory Manager for ACrQ - Natural Language Knowledge Base with Reasoning.

This module provides a complete system for:
1. Asserting natural language statements to a persistent theory
2. Translating NL to ACrQ formulas
3. Testing satisfiability and inferring new knowledge
4. Detecting and reporting gaps/gluts
5. Managing theory updates interactively
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from .acrq_parser import parse_acrq_formula
from .formula import BilateralPredicateFormula, PredicateFormula
from .signs import SignedFormula, e, f, t
from .tableau import ACrQTableau


@dataclass
class Statement:
    """A statement in the theory with an explicit sign."""

    id: str
    natural_language: str
    formula: Optional[str] = None
    sign: str = "t"  # Default to true; can be t, f, e, m, n, v
    is_inferred: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)


@dataclass
class InformationState:
    """Information state analysis result."""

    predicate: str
    state: str  # 'true', 'false', 'glut', 'gap'
    evidence: list[str]
    branch_id: Optional[int] = None


class NaturalLanguageTranslator:
    """Translate natural language to ACrQ formulas."""

    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
        self.patterns = self._build_patterns()

    def _build_patterns(self) -> list[tuple[re.Pattern, str]]:
        """Build regex patterns for common NL constructs."""
        return [
            # Negations (check before simple predicates)
            (re.compile(r"(\w+) is not a (\w+)"), r"~\2(\1)"),
            (re.compile(r"(\w+) is not (\w+)"), r"~\2(\1)"),
            # Simple predicates
            (re.compile(r"(\w+) is a (\w+)"), r"\2(\1)"),
            (re.compile(r"(\w+) is (\w+)"), r"\2(\1)"),
            # Conditionals
            (
                re.compile(r"if (\w+) is a (\w+) then (\w+) is a (\w+)"),
                r"\2(\1) -> \4(\3)",
            ),
            # Universals
            (re.compile(r"all (\w+)s are (\w+)"), r"[forall X \1(X)]\2(X)"),
            (re.compile(r"every (\w+) can (\w+)"), r"[forall X \1(X)]\2(X)"),
            (re.compile(r"every (\w+) is a (\w+)"), r"[forall X \1(X)]\2(X)"),
            # Existentials
            (re.compile(r"some (\w+)s are (\w+)"), r"[exists X \1(X)]\2(X)"),
            (re.compile(r"some (\w+) is a (\w+)"), r"[exists X \1(X)]\2(X)"),
            (
                re.compile(r"there exists a (\w+) that is a (\w+)"),
                r"[exists X \1(X)]\2(X)",
            ),
            # Conjunctions
            (re.compile(r"(\w+) is a (\w+) and a (\w+)"), r"\2(\1) & \3(\1)"),
            # Disjunctions
            (re.compile(r"(\w+) is a (\w+) or a (\w+)"), r"\2(\1) | \3(\1)"),
            # Relations (most general, check last)
            (re.compile(r"(\w+) (\w+) (\w+)"), r"\2(\1, \3)"),
        ]

    def translate(self, text: str) -> Optional[str]:
        """Translate natural language to ACrQ formula."""
        text = text.lower().strip()

        # Try pattern matching first
        for pattern, replacement in self.patterns:
            match = pattern.match(text)
            if match:
                formula = pattern.sub(replacement, text)
                # Capitalize predicates and constants appropriately
                formula = self._capitalize_formula(formula)
                return formula

        # If using LLM, try that
        if self.use_llm:
            return self._translate_with_llm(text)

        return None

    def _capitalize_formula(self, formula: str) -> str:
        """Capitalize predicates and constants appropriately."""
        import re

        # Fix predicates to have capital first letter
        # Pattern: word(args) where word starts with lowercase
        formula = re.sub(
            r"\b([a-z])(\w*)\(",
            lambda m: m.group(1).upper() + m.group(2) + "(",
            formula,
        )

        # Ensure ALL X variables are uppercase (comprehensive replacement)
        # Replace any lowercase x that appears to be a variable
        formula = re.sub(r"\bx\b", "X", formula)  # Any standalone x
        formula = formula.replace("(x)", "(X)")
        formula = formula.replace("(x,", "(X,")
        formula = formula.replace(", x)", ", X)")
        formula = formula.replace(", x,", ", X,")
        formula = formula.replace("]x(", "]X(")
        formula = formula.replace(" x ", " X ")
        formula = formula.replace("[forall x", "[forall X")
        formula = formula.replace("[exists x", "[exists X")
        formula = formula.replace("X(x)", "X(X)")  # Fix pattern like Cat(x)

        return formula

    def _translate_with_llm(self, text: str) -> Optional[str]:
        """Use LLM to translate (requires llm_integration)."""
        # This would use an LLM to translate complex NL to ACrQ
        # For now, return None
        return None


class TheoryManager:
    """Manage a theory of statements with persistence and reasoning."""

    def __init__(
        self,
        theory_file: Path = Path("theory.json"),
        llm_evaluator: Optional[Callable] = None,
    ):
        self.theory_file = theory_file
        self.llm_evaluator = llm_evaluator
        self.translator = NaturalLanguageTranslator()

        # Theory state
        self.statements: dict[str, Statement] = {}
        self.next_id = 1

        # Don't auto-load - let user explicitly load if desired

    def assert_statement(
        self,
        natural_language: str,
        formula: Optional[str] = None,
        sign: str = "t",
        verify_facts: bool = False,
    ) -> Statement:
        """Assert a new statement to the theory with a specific sign.

        Args:
            natural_language: The natural language statement
            formula: Optional ACrQ formula (will be translated if not provided)
            sign: The sign for the statement (t=true, f=false, e=error, m=meaningful, n=nontrue, v=variable)
            verify_facts: If True and formula is atomic with LLM available, use sign 'v' for verification
        """
        # Validate sign
        valid_signs = ["t", "f", "e", "m", "n", "v"]
        if sign not in valid_signs:
            raise ValueError(
                f"Invalid sign '{sign}'. Must be one of: {', '.join(valid_signs)}"
            )

        # Generate ID
        stmt_id = f"S{self.next_id:04d}"
        self.next_id += 1

        # Translate if no formula provided
        if formula is None:
            # First, try to parse the natural language as a formula directly
            try:
                from .acrq_parser import SyntaxMode

                parse_acrq_formula(natural_language, SyntaxMode.MIXED)
                # It's a valid formula, use it directly
                formula = natural_language
            except Exception:
                # Not a valid formula, try to translate
                formula = self.translator.translate(natural_language)
                if formula is None:
                    # Couldn't translate - store as comment
                    formula = f"// {natural_language}"

        # Validate formula syntax
        try:
            if not formula.startswith("//"):
                from .acrq_parser import SyntaxMode

                parse_acrq_formula(formula, SyntaxMode.MIXED)
        except Exception as e:
            formula = f"// PARSE ERROR: {formula} - {e}"

        # Create statement with source metadata
        stmt = Statement(
            id=stmt_id,
            natural_language=natural_language,
            formula=formula,
            sign=sign,
            is_inferred=False,
            metadata={"source": "user_assertion"},
        )

        self.statements[stmt_id] = stmt
        return stmt

    def retract_statement(self, stmt_id: str) -> bool:
        """Retract a statement from the theory."""
        if stmt_id in self.statements:
            del self.statements[stmt_id]
            return True
        return False

    def check_satisfiability(self) -> tuple[bool, list[InformationState]]:
        """Check if the current theory is satisfiable."""
        # Collect valid formulas with their signs
        formulas = []
        for stmt in self.statements.values():
            if stmt.formula and not stmt.formula.startswith("//"):
                try:
                    # Use MIXED mode to handle both syntaxes correctly
                    from .acrq_parser import SyntaxMode

                    formula = parse_acrq_formula(stmt.formula, SyntaxMode.MIXED)
                    # Convert string sign to sign object
                    sign_map = {"t": t, "f": f, "e": e}
                    sign_obj = sign_map.get(stmt.sign, t)  # Default to t if m, n, or v
                    formulas.append(SignedFormula(sign_obj, formula))
                except Exception:
                    continue

        if not formulas:
            return True, []  # Empty theory is satisfiable

        # Create tableau
        tableau = ACrQTableau(formulas, llm_evaluator=self.llm_evaluator)
        result = tableau.construct()

        # Analyze information states
        info_states = self._analyze_information_states(result.tableau)

        # Store LLM-generated formulas as inferred statements
        if self.llm_evaluator:
            self._store_llm_evidence_from_tableau(result.tableau)

        return result.satisfiable, info_states

    def _analyze_information_states(self, tableau: Any) -> list[InformationState]:
        """Analyze tableau for gaps and gluts."""
        states = []
        seen_states = set()  # Track (predicate, state) pairs to avoid duplicates

        for branch in tableau.branches:
            if branch.is_closed:
                continue

            # Track evidence for each predicate
            predicates: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}

            for node_id in branch.node_ids:
                node = tableau.nodes[node_id]
                sf = node.formula

                if isinstance(
                    sf.formula, (PredicateFormula, BilateralPredicateFormula)
                ):
                    # Get base predicate info
                    if isinstance(sf.formula, BilateralPredicateFormula):
                        base_name = sf.formula.get_base_name()
                        is_negative = sf.formula.is_negative
                    else:
                        base_name = sf.formula.predicate_name.rstrip("*")
                        is_negative = sf.formula.predicate_name.endswith("*")

                    terms = tuple(str(t) for t in sf.formula.terms)
                    key = (base_name, terms)

                    if key not in predicates:
                        predicates[key] = {
                            "t_positive": False,
                            "t_negative": False,
                            "f_positive": False,
                            "f_negative": False,
                            "error": False,
                            "evidence": [],
                        }

                    # Record evidence
                    evidence_str = f"{sf.sign}:{sf.formula}"
                    predicates[key]["evidence"].append(evidence_str)

                    if sf.sign == t:
                        if is_negative:
                            predicates[key]["t_negative"] = True
                        else:
                            predicates[key]["t_positive"] = True
                    elif sf.sign == f:
                        if is_negative:
                            predicates[key]["f_negative"] = True
                        else:
                            predicates[key]["f_positive"] = True
                    elif sf.sign == e:
                        predicates[key]["error"] = True

            # Classify each predicate's state
            for (base_name, terms), evidence in predicates.items():
                pred_str = f"{base_name}({','.join(terms)})"

                if evidence["t_positive"] and evidence["t_negative"]:
                    # Glut
                    state_key = (pred_str, "glut")
                    if state_key not in seen_states:
                        seen_states.add(state_key)
                        states.append(
                            InformationState(
                                predicate=pred_str,
                                state="glut",
                                evidence=evidence["evidence"],
                                branch_id=branch.id,
                            )
                        )
                elif evidence["t_positive"] and not evidence["t_negative"]:
                    # True
                    state_key = (pred_str, "true")
                    if state_key not in seen_states:
                        seen_states.add(state_key)
                        states.append(
                            InformationState(
                                predicate=pred_str,
                                state="true",
                                evidence=evidence["evidence"],
                                branch_id=branch.id,
                            )
                        )
                elif evidence["t_negative"] and not evidence["t_positive"]:
                    # False
                    state_key = (pred_str, "false")
                    if state_key not in seen_states:
                        seen_states.add(state_key)
                        states.append(
                            InformationState(
                                predicate=pred_str,
                                state="false",
                                evidence=evidence["evidence"],
                                branch_id=branch.id,
                            )
                        )
                elif evidence["f_positive"] and evidence["f_negative"]:
                    # Gap
                    state_key = (pred_str, "gap")
                    if state_key not in seen_states:
                        seen_states.add(state_key)
                        states.append(
                            InformationState(
                                predicate=pred_str,
                                state="gap",
                                evidence=evidence["evidence"],
                                branch_id=branch.id,
                            )
                        )
                elif evidence["error"]:
                    # Gap (undefined)
                    state_key = (pred_str, "gap")
                    if state_key not in seen_states:
                        seen_states.add(state_key)
                        states.append(
                            InformationState(
                                predicate=pred_str,
                                state="gap",
                                evidence=evidence["evidence"],
                                branch_id=branch.id,
                            )
                        )

        return states

    def _store_llm_evidence_from_tableau(self, tableau: Any) -> None:
        """Store LLM-generated evidence from tableau nodes as inferred statements."""
        # Track which formulas came from LLM evaluations
        llm_formulas = {}

        # Check all nodes in the tableau
        for node in tableau.nodes.values():
            sf = node.formula
            formula = sf.formula

            # Look for bilateral predicates (these are created by LLM evaluations)
            if isinstance(formula, BilateralPredicateFormula):
                # Only store negative predicates (P*) as these represent LLM negative evidence
                if formula.is_negative:
                    formula_str = str(formula)

                    # Check if this is from an LLM evaluation (not from user input)
                    # We can tell because user input formulas are already in our statements
                    is_user_input = False
                    for stmt in self.statements.values():
                        if stmt.formula == formula_str:
                            is_user_input = True
                            break

                    if not is_user_input and formula_str not in llm_formulas:
                        # This is LLM-generated evidence
                        base_name = formula.get_base_name()
                        terms_str = ", ".join(str(t) for t in formula.terms)

                        # Create natural language description
                        natural_desc = (
                            f"LLM evidence: {terms_str} is not {base_name.lower()}"
                        )

                        llm_formulas[formula_str] = natural_desc

        # Store each LLM formula as a statement
        for formula_str, natural_desc in llm_formulas.items():
            # Create new statement for LLM evidence
            stmt_id = f"E{self.next_id:04d}"  # E for Evidence from LLM
            self.next_id += 1

            # Get model info from the evaluator if available
            metadata = {"source": "llm_evaluation"}
            if self.llm_evaluator and hasattr(self.llm_evaluator, "model_info"):
                metadata.update(self.llm_evaluator.model_info)

            stmt = Statement(
                id=stmt_id,
                natural_language=natural_desc,
                formula=formula_str,
                sign="t",  # LLM evidence is asserted as true
                is_inferred=True,
                timestamp=datetime.now().isoformat(),
                metadata=metadata,
            )

            self.statements[stmt_id] = stmt

    def infer_consequences(self) -> list[Statement]:
        """Infer logical consequences from the current theory."""
        inferred: list[Statement] = []

        # Get current formulas
        formulas = []
        for stmt in self.statements.values():
            if stmt.formula and not stmt.formula.startswith("//"):
                try:
                    # Use MIXED mode to handle both syntaxes correctly
                    from .acrq_parser import SyntaxMode

                    formula = parse_acrq_formula(stmt.formula, SyntaxMode.MIXED)
                    formulas.append(SignedFormula(t, formula))
                except Exception:
                    continue

        if not formulas:
            return inferred

        # Create tableau and analyze
        tableau = ACrQTableau(formulas, llm_evaluator=self.llm_evaluator)
        result = tableau.construct()

        if result.satisfiable and result.models:
            # Extract new facts from models
            model = result.models[0]

            # Also check tableau nodes to identify LLM-generated formulas
            llm_generated = set()
            for node in tableau.nodes.values():
                if node.rule_applied and "llm-eval" in node.rule_applied:
                    # This node was created by LLM evaluation
                    formula_str = str(node.formula.formula)
                    llm_generated.add(formula_str)

            for pred_str, truth_value in model.valuations.items():
                # Check if this is a new fact not already in theory
                if self._is_new_fact(pred_str, truth_value):
                    # Determine if this came from LLM or inference
                    is_llm = pred_str in llm_generated

                    if is_llm:
                        # LLM-generated evidence
                        nl = f"LLM evidence: {pred_str} is {truth_value}"
                        stmt_id = f"E{self.next_id:04d}"  # E for Evidence

                        # Get model info from the evaluator if available
                        metadata = {"source": "llm_evaluation"}
                        if self.llm_evaluator and hasattr(
                            self.llm_evaluator, "model_info"
                        ):
                            metadata.update(self.llm_evaluator.model_info)
                    else:
                        # Regular inference
                        nl = f"Inferred: {pred_str} is {truth_value}"
                        stmt_id = f"I{self.next_id:04d}"  # I for Inferred
                        metadata = {"source": "tableau_inference"}

                    formula_str = (
                        pred_str if str(truth_value) == "t" else f"~{pred_str}"
                    )

                    stmt = Statement(
                        id=stmt_id,
                        natural_language=nl,
                        formula=formula_str,
                        sign="t",
                        is_inferred=True,
                        metadata=metadata,
                    )
                    self.next_id += 1

                    inferred.append(stmt)
                    self.statements[stmt.id] = stmt

        return inferred

    def _is_new_fact(self, predicate: str, truth_value: Any) -> bool:
        """Check if a fact is new to the theory."""
        # Check if this exact predicate with this truth value already exists
        formula_to_check = predicate if str(truth_value) == "t" else f"~{predicate}"

        for stmt in self.statements.values():
            if stmt.formula == formula_to_check:
                return False
            # Also check if the predicate itself is the formula (without sign prefix)
            if stmt.formula == predicate:
                return False
        return True

    def save(self) -> None:
        """Save theory to file."""
        data = {
            "metadata": {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "next_id": self.next_id,
            },
            "statements": [
                {
                    "id": s.id,
                    "natural_language": s.natural_language,
                    "formula": s.formula,
                    "sign": s.sign,
                    "is_inferred": s.is_inferred,
                    "timestamp": s.timestamp,
                    "metadata": s.metadata,
                }
                for s in self.statements.values()
            ],
        }

        with open(self.theory_file, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        """Load theory from file."""
        with open(self.theory_file) as f:
            data = json.load(f)

        self.next_id = data["metadata"].get("next_id", 1)
        self.statements = {}

        for stmt_data in data["statements"]:
            stmt = Statement(
                id=stmt_data["id"],
                natural_language=stmt_data["natural_language"],
                formula=stmt_data.get("formula"),
                sign=stmt_data.get(
                    "sign", "t"
                ),  # Default to 't' for backward compatibility
                is_inferred=stmt_data.get("is_inferred", False),
                timestamp=stmt_data.get("timestamp", ""),
                metadata=stmt_data.get("metadata", {}),
            )
            self.statements[stmt.id] = stmt

    def clear(self) -> None:
        """Clear all statements."""
        self.statements = {}
        self.next_id = 1

    def list_statements(self, only_asserted: bool = False) -> list[Statement]:
        """List all statements."""
        statements = list(self.statements.values())
        if only_asserted:
            statements = [s for s in statements if not s.is_inferred]
        return sorted(statements, key=lambda s: s.id)

    def get_report(self) -> str:
        """Generate a comprehensive report on the theory."""
        satisfiable, info_states = self.check_satisfiability()

        report = []
        report.append("=" * 70)
        report.append("THEORY ANALYSIS REPORT")
        report.append("=" * 70)
        report.append("")

        # Basic stats
        total = len(self.statements)
        asserted = sum(1 for s in self.statements.values() if not s.is_inferred)
        inferred = total - asserted

        report.append(f"Total statements: {total}")
        report.append(f"  - Asserted: {asserted}")
        report.append(f"  - Inferred: {inferred}")
        report.append("")

        # Satisfiability
        report.append(
            f"Satisfiability: {'✓ SATISFIABLE' if satisfiable else '✗ UNSATISFIABLE'}"
        )
        report.append("")

        # Information states
        if info_states:
            gluts = [s for s in info_states if s.state == "glut"]
            gaps = [s for s in info_states if s.state == "gap"]

            if gluts:
                report.append(f"GLUTS (Conflicting Evidence): {len(gluts)}")
                for glut in gluts:
                    report.append(f"  - {glut.predicate}")
                    for ev in glut.evidence[:2]:  # Show first 2 pieces of evidence
                        # Try to find statement ID for this evidence
                        stmt_id = None
                        if ":" in ev:
                            sign, formula = ev.split(":", 1)
                            for stmt in self.statements.values():
                                if stmt.formula == formula:
                                    stmt_id = stmt.id
                                    break
                        if stmt_id:
                            report.append(f"    • {ev} [{stmt_id}]")
                        else:
                            report.append(f"    • {ev}")
                report.append("")

            if gaps:
                report.append(f"GAPS (Lack of Knowledge): {len(gaps)}")
                for gap in gaps:
                    report.append(f"  - {gap.predicate}")
                    if gap.evidence:
                        report.append(f"    • {gap.evidence[0]}")
                report.append("")

        # Current statements
        report.append("CURRENT THEORY:")
        for stmt in sorted(self.statements.values(), key=lambda s: s.id):
            # Determine marker based on ID prefix
            if stmt.id.startswith("S"):
                marker = "[A]"  # Asserted
            elif stmt.id.startswith("I"):
                marker = "[I]"  # Inferred
            elif stmt.id.startswith("E"):
                marker = "[E]"  # LLM Evidence
            else:
                marker = "[?]"
            report.append(f"  {stmt.id} {marker}: {stmt.natural_language}")
            if stmt.formula and not stmt.formula.startswith("//"):
                # Show the actual sign from the statement
                report.append(f"        → {stmt.sign}:{stmt.formula}")

        return "\n".join(report)
