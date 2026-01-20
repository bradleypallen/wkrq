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
import time
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
            # Universals - capture plural consequent for singularization
            (re.compile(r"all (\w+)s are (\w+)s"), r"[forall X \1(X)]\2(X)"),
            (re.compile(r"all (\w+)s are (\w+)"), r"[forall X \1(X)]\2(X)"),
            (re.compile(r"every (\w+) can (\w+)"), r"[forall X \1(X)]\2(X)"),
            (re.compile(r"every (\w+) is a (\w+)"), r"[forall X \1(X)]\2(X)"),
            # Existentials
            (re.compile(r"some (\w+)s are (\w+)s"), r"[exists X \1(X)]\2(X)"),
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

    def _singularize(self, word: str) -> str:
        """Convert a plural word to singular form (simple heuristic)."""
        # Handle common irregular plurals
        irregulars = {
            "analyses": "analysis",
            "indices": "index",
            "vertices": "vertex",
        }
        if word.lower() in irregulars:
            return irregulars[word.lower()]

        # Handle words ending in 'ies' -> 'y' (e.g., 'properties' -> 'property')
        if word.endswith("ies") and len(word) > 3:
            return word[:-3] + "y"

        # Handle words ending in 'es' after s, x, z, ch, sh
        if word.endswith("es") and len(word) > 2:
            if word[-3] in "sxz" or word[-4:-2] in ["ch", "sh"]:
                return word[:-2]

        # Handle regular plurals ending in 's'
        if word.endswith("s") and not word.endswith("ss") and len(word) > 1:
            return word[:-1]

        return word

    def translate(self, text: str) -> Optional[str]:
        """Translate natural language to ACrQ formula."""
        text = text.lower().strip()

        # Try pattern matching first
        # Use fullmatch to ensure the entire string is matched
        for pattern, replacement in self.patterns:
            match = pattern.fullmatch(text)
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

        # Fix predicates: capitalize first letter AND singularize
        # Pattern: word(args) where word starts with lowercase
        def capitalize_and_singularize(m: re.Match) -> str:
            pred = m.group(1) + m.group(2)
            # Singularize the predicate name
            singular = self._singularize(pred)
            # Capitalize first letter
            return singular[0].upper() + singular[1:] + "("

        formula = re.sub(r"\b([a-z])(\w*)\(", capitalize_and_singularize, formula)

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

        # Timing data
        self.last_infer_time: Optional[float] = None
        self.last_check_time: Optional[float] = None
        self.last_llm_time: Optional[float] = None  # LLM verification time within infer

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
        start_time = time.perf_counter()

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

        self.last_check_time = time.perf_counter() - start_time
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
        """Infer logical consequences from the current theory using forward chaining.

        This method uses proper forward-chaining inference for restricted universal
        quantifiers: [∀X P(X)]Q(X) only derives Q(c) when P(c) is already true.
        """
        import logging

        start_time = time.perf_counter()
        llm_start_time: Optional[float] = None

        logger = logging.getLogger(__name__)
        inferred: list[Statement] = []

        from .acrq_parser import SyntaxMode
        from .formula import (
            RestrictedUniversalFormula,
        )

        # Step 1: Parse all formulas and collect ground facts and universals
        ground_facts: dict[str, set[str]] = {}  # predicate_name -> set of constants
        universal_rules: list[tuple[str, RestrictedUniversalFormula]] = []
        all_constants: set[str] = set()

        for stmt in self.statements.values():
            if stmt.formula and not stmt.formula.startswith("//"):
                try:
                    formula = parse_acrq_formula(stmt.formula, SyntaxMode.MIXED)
                    # Collect constants from all formulas
                    all_constants.update(self._extract_constants(formula))

                    # Only consider formulas with sign 't' for forward chaining
                    if stmt.sign == "t":
                        if isinstance(formula, RestrictedUniversalFormula):
                            universal_rules.append((stmt.id, formula))
                            logger.debug(
                                f"Found universal rule {stmt.id}: {stmt.formula}"
                            )
                        elif self._is_ground_atomic(formula):
                            # Ground atomic fact
                            pred_name, const_name = self._extract_predicate_constant(
                                formula
                            )
                            if pred_name and const_name:
                                if pred_name not in ground_facts:
                                    ground_facts[pred_name] = set()
                                ground_facts[pred_name].add(const_name)
                                logger.debug(
                                    f"Found ground fact: {pred_name}({const_name})"
                                )
                except Exception as e:
                    logger.debug(f"Failed to parse formula '{stmt.formula}': {e}")
                    continue

        logger.debug(f"All constants: {all_constants}")
        logger.debug(f"Ground facts: {ground_facts}")
        logger.debug(f"Universal rules: {len(universal_rules)}")

        # Step 2: Forward chaining - apply universal rules until fixed point
        new_inferences: list[tuple[str, str, str]] = (
            []
        )  # (predicate, constant, from_rule)
        changed = True
        iteration = 0
        max_iterations = 100  # Safety limit

        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            logger.debug(f"Forward chaining iteration {iteration}")

            for rule_id, universal in universal_rules:
                # universal is [∀X P(X)]Q(X)
                # restriction is P(X), matrix is Q(X)
                restriction = universal.restriction
                matrix = universal.matrix

                # Get the predicate name from the restriction
                restrictor_pred = self._get_predicate_name(restriction)
                if not restrictor_pred:
                    logger.debug(
                        f"Could not extract predicate from restriction: {restriction}"
                    )
                    continue

                # Get the predicate name from the matrix
                matrix_pred = self._get_predicate_name(matrix)
                if not matrix_pred:
                    logger.debug(f"Could not extract predicate from matrix: {matrix}")
                    continue

                logger.debug(
                    f"Rule {rule_id}: {restrictor_pred}(X) -> {matrix_pred}(X)"
                )

                # Check which constants satisfy the restriction
                satisfying_constants = ground_facts.get(restrictor_pred, set())
                logger.debug(
                    f"Constants satisfying {restrictor_pred}: {satisfying_constants}"
                )

                for const in satisfying_constants:
                    # Check if we already have matrix_pred(const)
                    existing_matrix_facts = ground_facts.get(matrix_pred, set())
                    if const not in existing_matrix_facts:
                        # New inference!
                        logger.debug(
                            f"New inference: {matrix_pred}({const}) from rule {rule_id}"
                        )
                        if matrix_pred not in ground_facts:
                            ground_facts[matrix_pred] = set()
                        ground_facts[matrix_pred].add(const)
                        new_inferences.append((matrix_pred, const, rule_id))
                        changed = True

        logger.debug(f"Forward chaining completed after {iteration} iterations")
        logger.debug(f"New inferences: {new_inferences}")

        # Step 3: Create Statement objects for new inferences
        for pred_name, const_name, from_rule in new_inferences:
            formula_str = f"{pred_name}({const_name})"

            # Check if this exact formula already exists as a statement
            if self._formula_exists(formula_str):
                continue

            stmt_id = f"I{self.next_id:04d}"
            self.next_id += 1

            nl = f"Inferred: {pred_name}({const_name}) is t"
            metadata = {"source": "forward_chaining", "from_rule": from_rule}

            stmt = Statement(
                id=stmt_id,
                natural_language=nl,
                formula=formula_str,
                sign="t",
                is_inferred=True,
                metadata=metadata,
            )

            inferred.append(stmt)
            self.statements[stmt.id] = stmt
            logger.info(f"Added inference: {stmt_id} t:{formula_str}")

        # Step 4: Run LLM verification on newly inferred atoms (if LLM evaluator available)
        # This verifies deductive inferences against LLM knowledge
        if self.llm_evaluator:
            llm_start_time = time.perf_counter()
            llm_verifications = self._verify_inferences_with_llm(new_inferences)
            inferred.extend(llm_verifications)
            self.last_llm_time = time.perf_counter() - llm_start_time
        else:
            self.last_llm_time = None

        self.last_infer_time = time.perf_counter() - start_time
        return inferred

    def _verify_inferences_with_llm(
        self, inferences: list[tuple[str, str, str]]
    ) -> list[Statement]:
        """Verify inferred atoms with LLM and add evidence statements.

        Args:
            inferences: List of (predicate_name, constant_name, from_rule) tuples

        Returns:
            List of LLM evidence statements
        """
        import logging

        from .acrq_parser import SyntaxMode
        from .semantics import FALSE, TRUE

        logger = logging.getLogger(__name__)
        llm_statements: list[Statement] = []

        if not self.llm_evaluator:
            return llm_statements

        for pred_name, const_name, from_rule in inferences:
            formula_str = f"{pred_name}({const_name})"

            try:
                # Parse the formula
                formula = parse_acrq_formula(formula_str, SyntaxMode.MIXED)

                # Only evaluate atomic formulas
                if not formula.is_atomic():
                    continue

                # Call LLM evaluator
                result = self.llm_evaluator(formula)

                if result is None:
                    logger.debug(f"LLM returned None for {formula_str}")
                    continue

                # Interpret the bilateral truth value and create appropriate statements
                # In ACrQ bilateral logic:
                # - Verified <t,f>: assert t:P(c) - confirms inference
                # - Refuted <f,t>: assert t:P*(c) - creates glut with inference (paraconsistent)
                # - Glut <t,t>: assert both t:P(c) and t:P*(c)
                # - Gap <f,f>: don't assert (no evidence) - just report

                metadata: dict[str, Any] = {
                    "source": "llm_verification",
                    "verified_inference": from_rule,
                    "bilateral": {
                        "positive": str(result.positive),
                        "negative": str(result.negative),
                    },
                }
                if hasattr(self.llm_evaluator, "model_info"):
                    metadata.update(self.llm_evaluator.model_info)

                if result.positive == TRUE and result.negative == FALSE:
                    # LLM confirms: <t,f> → assert t:P(c)
                    verdict = "verified"
                    logger.info(f"LLM verified inference {formula_str}")

                    stmt_id = f"E{self.next_id:04d}"
                    self.next_id += 1
                    stmt = Statement(
                        id=stmt_id,
                        natural_language=f"LLM: {formula_str} confirmed <t,f>",
                        formula=formula_str,
                        sign="t",
                        is_inferred=True,
                        metadata={**metadata, "verdict": verdict},
                    )
                    llm_statements.append(stmt)
                    self.statements[stmt.id] = stmt

                elif result.positive == FALSE and result.negative == TRUE:
                    # LLM refutes: <f,t> → assert t:P*(c) (bilateral negative evidence)
                    # This creates a GLUT with the inference t:P(c), which ACrQ tolerates
                    verdict = "refuted"
                    star_formula = f"{pred_name}*({const_name})"
                    logger.info(
                        f"LLM refuted inference {formula_str} → asserting {star_formula}"
                    )

                    stmt_id = f"E{self.next_id:04d}"
                    self.next_id += 1
                    stmt = Statement(
                        id=stmt_id,
                        natural_language=f"LLM: {star_formula} (refutes {pred_name}) <f,t>",
                        formula=star_formula,
                        sign="t",
                        is_inferred=True,
                        metadata={
                            **metadata,
                            "verdict": verdict,
                            "refutes": formula_str,
                        },
                    )
                    llm_statements.append(stmt)
                    self.statements[stmt.id] = stmt

                elif result.positive == TRUE and result.negative == TRUE:
                    # LLM has conflicting evidence: <t,t> → assert both t:P(c) and t:P*(c)
                    verdict = "glut"
                    star_formula = f"{pred_name}*({const_name})"
                    logger.info(f"LLM glut for {formula_str}")

                    # Positive evidence
                    stmt_id = f"E{self.next_id:04d}"
                    self.next_id += 1
                    stmt = Statement(
                        id=stmt_id,
                        natural_language=f"LLM: {formula_str} (glut positive) <t,t>",
                        formula=formula_str,
                        sign="t",
                        is_inferred=True,
                        metadata={**metadata, "verdict": verdict},
                    )
                    llm_statements.append(stmt)
                    self.statements[stmt.id] = stmt

                    # Negative evidence
                    stmt_id2 = f"E{self.next_id:04d}"
                    self.next_id += 1
                    stmt2 = Statement(
                        id=stmt_id2,
                        natural_language=f"LLM: {star_formula} (glut negative) <t,t>",
                        formula=star_formula,
                        sign="t",
                        is_inferred=True,
                        metadata={**metadata, "verdict": verdict, "glut_pair": stmt.id},
                    )
                    llm_statements.append(stmt2)
                    self.statements[stmt2.id] = stmt2

                elif result.positive == FALSE and result.negative == FALSE:
                    # LLM has no evidence: <f,f> → GAP, don't assert anything
                    # Just record the gap for reporting purposes
                    verdict = "gap"
                    logger.info(f"LLM gap for {formula_str} (no evidence)")

                    # Create a gap record but with a special marker
                    # We use sign "v" (variable) to indicate unknown/gap without conflict
                    stmt_id = f"E{self.next_id:04d}"
                    self.next_id += 1
                    stmt = Statement(
                        id=stmt_id,
                        natural_language=f"LLM: {formula_str} has no evidence <f,f>",
                        formula=formula_str,
                        sign="v",  # Variable sign = unknown, doesn't conflict
                        is_inferred=True,
                        metadata={**metadata, "verdict": verdict},
                    )
                    llm_statements.append(stmt)
                    self.statements[stmt.id] = stmt

                else:
                    # UNDEFINED or complex state
                    verdict = "undefined"
                    logger.info(f"LLM undefined for {formula_str}")
                    # Don't assert anything for undefined states

            except Exception as e:
                logger.warning(f"Error verifying {formula_str} with LLM: {e}")
                continue

        return llm_statements

    def _extract_constants(self, formula: Any) -> set[str]:
        """Extract all constant names from a formula."""
        from .formula import (
            BilateralPredicateFormula,
            CompoundFormula,
            Constant,
            PredicateFormula,
            RestrictedQuantifierFormula,
        )

        constants: set[str] = set()

        if isinstance(formula, (PredicateFormula, BilateralPredicateFormula)):
            for term in formula.terms:
                if isinstance(term, Constant):
                    constants.add(term.name)
        elif isinstance(formula, CompoundFormula):
            for subformula in formula.subformulas:
                constants.update(self._extract_constants(subformula))
        elif isinstance(formula, RestrictedQuantifierFormula):
            constants.update(self._extract_constants(formula.restriction))
            constants.update(self._extract_constants(formula.matrix))

        return constants

    def _is_ground_atomic(self, formula: Any) -> bool:
        """Check if formula is a ground atomic predicate (no variables)."""
        from .formula import (
            BilateralPredicateFormula,
            PredicateFormula,
            Variable,
        )

        if isinstance(formula, (PredicateFormula, BilateralPredicateFormula)):
            # Check all terms are constants (not variables)
            for term in formula.terms:
                if isinstance(term, Variable):
                    return False
            return True
        return False

    def _extract_predicate_constant(
        self, formula: Any
    ) -> tuple[Optional[str], Optional[str]]:
        """Extract predicate name and constant from a ground atomic formula."""
        from .formula import BilateralPredicateFormula, Constant, PredicateFormula

        if isinstance(formula, BilateralPredicateFormula):
            if len(formula.terms) == 1 and isinstance(formula.terms[0], Constant):
                return formula.predicate_name, formula.terms[0].name
        elif isinstance(formula, PredicateFormula):
            if len(formula.terms) == 1 and isinstance(formula.terms[0], Constant):
                return formula.predicate_name, formula.terms[0].name

        return None, None

    def _get_predicate_name(self, formula: Any) -> Optional[str]:
        """Get predicate name from an atomic formula or formula with single predicate."""
        from .formula import BilateralPredicateFormula, PredicateFormula

        if isinstance(formula, (PredicateFormula, BilateralPredicateFormula)):
            return formula.predicate_name
        return None

    def _formula_exists(self, formula_str: str) -> bool:
        """Check if a formula string already exists in statements."""
        for stmt in self.statements.values():
            if stmt.formula == formula_str:
                return True
        return False

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

        # Timing information
        if self.last_infer_time is not None or self.last_check_time is not None:
            report.append("Execution Time:")
            if self.last_infer_time is not None:
                report.append(f"  - Inference: {self.last_infer_time:.3f}s")
                if self.last_llm_time is not None:
                    report.append(f"    (LLM verification: {self.last_llm_time:.3f}s)")
            if self.last_check_time is not None:
                report.append(f"  - Satisfiability check: {self.last_check_time:.3f}s")
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

            # Show bilateral truth values for LLM evidence
            if stmt.id.startswith("E") and stmt.metadata.get("bilateral"):
                bilateral = stmt.metadata["bilateral"]
                pos = bilateral.get("positive", "?")
                neg = bilateral.get("negative", "?")
                report.append(f"        <{pos},{neg}>")

        return "\n".join(report)
