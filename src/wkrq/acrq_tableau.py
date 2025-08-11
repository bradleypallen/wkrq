"""
ACrQ-specific tableau implementation with bilateral predicate support.

This module extends the standard wKrQ tableau to handle bilateral predicates
according to Ferguson's ACrQ system.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional

from .acrq_ferguson_rules import get_acrq_rule
from .formula import (
    BilateralPredicateFormula,
    CompoundFormula,
    Formula,
    PredicateFormula,
    RestrictedUniversalFormula,
)
from .semantics import FALSE, TRUE, UNDEFINED, BilateralTruthValue, TruthValue
from .signs import Sign, SignedFormula, e, f, t
from .tableau import Branch, Model, RuleInfo, RuleType, Tableau, TableauResult


class ACrQBranch(Branch):
    """Branch for ACrQ tableau with paraconsistent contradiction detection."""

    def __init__(self, branch_id: int):
        """Initialize ACrQ branch."""
        super().__init__(branch_id)
        self.bilateral_pairs: dict[str, str] = {}  # Maps R to R*

    def _check_contradiction(self, new_formula: SignedFormula) -> bool:
        """Check for contradictions per Ferguson's Lemma 5.

        A branch closes in ACrQ when:
        1. Standard contradiction: u:φ and v:φ appear for distinct u,v ∈ {t,f,e}
        2. But NOT when t:R(a) and t:R*(a) appear (this is a glut, allowed)

        The key insight from Lemma 5 is that φ* = ψ* ensures they share a
        common primary logical operator, preventing closure in glut cases.
        """
        formula = new_formula.formula
        sign = new_formula.sign

        # Check standard contradictions (distinct signs from {t,f,e})
        for other_sign in [t, f, e]:
            if other_sign != sign and len(self.formula_index[other_sign][formula]) > 0:
                # Check if this is a bilateral predicate glut case
                if sign == t and other_sign == t:
                    # Both are t - check if they form a glut (R and R*)
                    if self._is_bilateral_glut(formula, sign):
                        # This is allowed in ACrQ - don't close
                        return False
                # Standard contradiction - close branch
                return True

        return False

    def _is_bilateral_glut(self, formula: Formula, sign: Sign) -> bool:
        """Check if this formula forms a bilateral glut with existing formulas.

        Returns True if we have both t:R(a) and t:R*(a) which is allowed.
        """
        if not isinstance(formula, PredicateFormula) and not isinstance(
            formula, BilateralPredicateFormula
        ):
            return False

        # Get the base name and check for its dual
        if isinstance(formula, BilateralPredicateFormula):
            base_name = formula.get_base_name()
            is_negative = formula.is_negative
        else:
            # Regular predicate
            if formula.predicate_name.endswith("*"):
                base_name = formula.predicate_name[:-1]
                is_negative = True
            else:
                base_name = formula.predicate_name
                is_negative = False

        # Look for the dual predicate with same sign
        for node_id in self.formula_index[sign][formula]:
            # Get the actual signed formula from the node
            node = self.nodes[node_id]
            other = node.formula.formula
            if isinstance(other, PredicateFormula) or isinstance(
                other, BilateralPredicateFormula
            ):
                # Check if it's the dual
                if isinstance(other, BilateralPredicateFormula):
                    other_base = other.get_base_name()
                    other_negative = other.is_negative
                else:
                    if other.predicate_name.endswith("*"):
                        other_base = other.predicate_name[:-1]
                        other_negative = True
                    else:
                        other_base = other.predicate_name
                        other_negative = False

                # If same base name but different polarity, it's a glut
                if base_name == other_base and is_negative != other_negative:
                    # Check that arguments match
                    if str(formula.terms) == str(other.terms):
                        return True

        return False


@dataclass
class ACrQModel(Model):
    """Model for ACrQ with bilateral predicate support."""

    bilateral_valuations: dict[str, BilateralTruthValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize bilateral valuations from standard valuations."""
        super().__init__(self.valuations, self.constants)
        self.bilateral_valuations = {}

        # Group predicates by base name
        bilateral_predicates: dict[str, dict[str, dict[str, TruthValue]]] = {}

        for atom_str, value in self.valuations.items():
            # Skip propositional atoms
            if "(" not in atom_str:
                continue

            # Extract predicate name and arguments
            pred_name = atom_str.split("(")[0]
            args = "(" + atom_str.split("(", 1)[1]

            # Determine base name
            if pred_name.endswith("*"):
                base_name = pred_name[:-1]
                is_negative = True
            else:
                base_name = pred_name
                is_negative = False

            # Initialize structure if needed
            if base_name not in bilateral_predicates:
                bilateral_predicates[base_name] = {}

            key = f"{base_name}{args}"
            if key not in bilateral_predicates[base_name]:
                bilateral_predicates[base_name][key] = {
                    "positive": FALSE,
                    "negative": FALSE,
                }

            # Set the appropriate value
            if is_negative:
                bilateral_predicates[base_name][key]["negative"] = value
            else:
                bilateral_predicates[base_name][key]["positive"] = value

        # Create bilateral truth values
        for _base_name, pred_instances in bilateral_predicates.items():
            for key, values in pred_instances.items():
                btv = BilateralTruthValue(
                    positive=values["positive"], negative=values["negative"]
                )
                self.bilateral_valuations[key] = btv

    def __eq__(self, other: object) -> bool:
        """Check equality for ACrQ models."""
        if not isinstance(other, ACrQModel):
            return False
        # First check parent equality
        if not super().__eq__(other):
            return False
        # Then check bilateral valuations
        return self.bilateral_valuations == other.bilateral_valuations

    def __hash__(self) -> int:
        """Hash for ACrQ model deduplication."""
        # Combine parent hash with bilateral valuations
        parent_hash = super().__hash__()
        bilateral_items = tuple(
            (k, (v.positive, v.negative))
            for k, v in sorted(self.bilateral_valuations.items())
        )
        return hash((parent_hash, bilateral_items))


class ACrQTableau(Tableau):
    """Extended tableau for ACrQ with bilateral predicate support."""

    def __init__(
        self,
        initial_formulas: list[SignedFormula],
        llm_evaluator: Optional[Callable[[Formula], BilateralTruthValue]] = None,
    ) -> None:
        """Initialize ACrQ tableau with bilateral predicate tracking.

        Args:
            initial_formulas: Initial signed formulas for the tableau
            llm_evaluator: Optional function that takes an atomic formula and returns
                          a BilateralTruthValue representing the LLM's assessment
        """
        self.bilateral_pairs: dict[str, str] = (
            {}
        )  # Maps R to R* - Initialize before super()
        self.llm_evaluator = llm_evaluator
        super().__init__(initial_formulas)
        self.logic_system = "ACrQ"
        self._constant_counter = 0  # Initialize counter for fresh constants

        # Disable early termination if LLM evaluator is present
        # This ensures that atomic formulas are processed for LLM evaluation
        if self.llm_evaluator:
            self.early_termination = False

        # Identify bilateral predicates in initial formulas
        self._identify_bilateral_predicates(initial_formulas)

    def _identify_bilateral_predicates(self, formulas: list[SignedFormula]) -> None:
        """Identify and register bilateral predicate pairs."""
        for sf in formulas:
            self._extract_bilateral_pairs(sf.formula)

    def _extract_bilateral_pairs(self, formula: Formula) -> None:
        """Extract bilateral predicate pairs from a formula."""
        if isinstance(formula, BilateralPredicateFormula):
            # Register both R -> R* and R* -> R mappings
            pos_name = formula.positive_name
            neg_name = f"{formula.positive_name}*"
            self.bilateral_pairs[pos_name] = neg_name
            self.bilateral_pairs[neg_name] = pos_name

        elif isinstance(formula, CompoundFormula):
            for sub in formula.subformulas:
                self._extract_bilateral_pairs(sub)

        elif hasattr(formula, "restriction") and hasattr(formula, "matrix"):
            # Handle quantified formulas
            self._extract_bilateral_pairs(formula.restriction)
            self._extract_bilateral_pairs(formula.matrix)

    def _create_branch(self, branch_id: int) -> ACrQBranch:
        """Create an ACrQ branch with paraconsistent contradiction detection."""
        branch = ACrQBranch(branch_id)
        branch.bilateral_pairs = self.bilateral_pairs.copy()
        return branch

    def _get_applicable_rule(
        self, signed_formula: SignedFormula, branch: Branch
    ) -> Optional[RuleInfo]:
        """Get applicable rule using ACrQ Ferguson rules from Definition 18."""
        # Use ACrQ-specific Ferguson rules which:
        # 1. Drop the general negation elimination rule
        # 2. Handle bilateral predicates specially
        # 3. Keep all other wKrQ rules

        # Get the ACrQ rule from our Ferguson rules module
        from .formula import Constant

        def fresh_constant_generator() -> Constant:
            """Generate fresh constants for quantifier instantiation."""
            self._constant_counter += 1
            return Constant(f"c_{self._constant_counter}")

        # Get existing constants from branch
        existing_constants = list(branch.ground_terms) if branch.ground_terms else []

        # Get used constants for this formula if it's a universal quantifier
        used_constants = None
        if isinstance(signed_formula.formula, RestrictedUniversalFormula):
            if hasattr(branch, "_universal_instantiations"):
                used_constants = branch._universal_instantiations.get(
                    signed_formula, set()
                )
            else:
                branch._universal_instantiations = {}
                used_constants = set()

        ferguson_rule = get_acrq_rule(
            signed_formula, fresh_constant_generator, existing_constants, used_constants
        )

        if ferguson_rule:
            # Convert FergusonRule to RuleInfo
            rule_type = (
                RuleType.BETA if ferguson_rule.is_branching() else RuleType.ALPHA
            )
            priority = 10 if rule_type == RuleType.ALPHA else 20

            return RuleInfo(
                name=ferguson_rule.name,
                rule_type=rule_type,
                priority=priority,
                complexity_cost=len(ferguson_rule.conclusions),
                conclusions=ferguson_rule.conclusions,
                instantiation_constant=ferguson_rule.instantiation_constant,
            )

        # If no ACrQ rule applies, check if it's an atomic formula that can be LLM-evaluated
        if self.llm_evaluator and signed_formula.formula.is_atomic():
            return self._create_llm_evaluation_rule(signed_formula, branch)

        return None

    def _extract_model(self, branch: Branch) -> Optional[ACrQModel]:
        """Extract an ACrQ model from an open branch."""
        # Use base class to get standard model
        base_model = super()._extract_model(branch)

        if base_model is None:
            return None

        # Create ACrQ model with bilateral valuations
        acrq_model = ACrQModel(
            valuations=base_model.valuations, constants=base_model.constants
        )

        return acrq_model

    def _create_llm_evaluation_rule(
        self, signed_formula: SignedFormula, branch: Branch
    ) -> Optional[RuleInfo]:
        """Create a rule that evaluates an atomic formula using the LLM.

        This method creates a tableau rule that:
        1. Calls the LLM evaluator on the atomic formula
        2. Gets a BilateralTruthValue back
        3. Adds the appropriately signed formula(s) as conclusions

        The key insight is that BilateralTruthValue has both positive and negative
        components, which in ACrQ correspond to R and R* respectively.
        """
        if not self.llm_evaluator or not signed_formula.formula.is_atomic():
            return None

        # Prevent multiple evaluations of the same atomic formula
        evaluation_key = f"llm_evaluated_{signed_formula.formula}"
        if not hasattr(branch, "_llm_evaluated"):
            branch._llm_evaluated = set()

        if evaluation_key in branch._llm_evaluated:
            return None  # Already evaluated this formula

        # Call the LLM evaluator
        try:
            bilateral_value = self.llm_evaluator(signed_formula.formula)
        except Exception:
            # If LLM evaluation fails, don't add any information
            return None

        # Convert BilateralTruthValue to signed formulas
        conclusions = []
        conclusion_set = []

        # For positive evidence (R is true)
        if bilateral_value.positive == TRUE:
            conclusion_set.append(SignedFormula(t, signed_formula.formula))
        elif bilateral_value.positive == FALSE:
            conclusion_set.append(SignedFormula(f, signed_formula.formula))
        elif bilateral_value.positive == UNDEFINED:
            from .signs import e as e_sign
            conclusion_set.append(SignedFormula(e_sign, signed_formula.formula))

        # For bilateral predicates, also handle the negative component (R*)
        if isinstance(
            signed_formula.formula, (PredicateFormula, BilateralPredicateFormula)
        ):
            # Create the dual predicate R*
            if isinstance(signed_formula.formula, BilateralPredicateFormula):
                dual_formula = signed_formula.formula.get_dual()
            else:
                # Convert regular predicate to bilateral
                dual_formula = BilateralPredicateFormula(
                    positive_name=signed_formula.formula.predicate_name,
                    terms=signed_formula.formula.terms,
                    is_negative=True,
                )

            # Add signed formula for R* based on negative component
            if bilateral_value.negative == TRUE:
                conclusion_set.append(SignedFormula(t, dual_formula))
            elif bilateral_value.negative == FALSE:
                conclusion_set.append(SignedFormula(f, dual_formula))
            elif bilateral_value.negative == UNDEFINED:
                from .signs import e as e_sign
                conclusion_set.append(SignedFormula(e_sign, dual_formula))

        if conclusion_set:
            conclusions.append(conclusion_set)

        if not conclusions:
            return None

        # Don't mark as evaluated here - mark it when the rule is actually applied

        return RuleInfo(
            name=f"LLM-Eval({signed_formula.formula})",
            rule_type=RuleType.ALPHA,  # Non-branching rule
            priority=5,  # Medium priority - after basic rules but before complex ones
            complexity_cost=len(conclusion_set),
            conclusions=conclusions,
        )

    def construct(self) -> TableauResult:
        """Construct tableau with LLM evaluation support."""
        max_iterations = 1000
        iteration = 0

        while (
            self.open_branches
            and not self.is_complete()
            and iteration < max_iterations
            and len(self.branches) < self.max_branching_factor
        ):

            iteration += 1

            # Advanced branch selection strategy
            selected_branch = self._select_optimal_branch()
            if not selected_branch:
                break

            # Get all applicable rules for this branch and prioritize them
            applicable_rules = self._get_prioritized_rules(selected_branch)
            if not applicable_rules:
                # No more rules can be applied to any branch
                break

            # Apply the highest priority rule
            best_rule = applicable_rules[0]  # Already sorted by priority
            node, rule_info = best_rule

            self.apply_rule(node, selected_branch, rule_info)

            # Modified early termination logic for LLM evaluation
            if self.early_termination and len(self.open_branches) > 0:
                # Don't terminate early if LLM evaluator is present and there are unevaluated atomic formulas
                if not self.llm_evaluator:
                    # Original logic: check if any branch is ready for model extraction
                    for branch in self.open_branches:
                        if all(
                            node.formula.formula.is_atomic() for node in branch.nodes
                        ):
                            break
                else:
                    # With LLM evaluator: continue until all atomic formulas are evaluated
                    all_evaluated = True
                    for branch in self.open_branches:
                        if not hasattr(branch, "_llm_evaluated"):
                            branch._llm_evaluated = set()
                        for node in branch.nodes:
                            if (
                                node.formula.formula.is_atomic()
                                and f"llm_evaluated_{node.formula.formula}"
                                not in branch._llm_evaluated
                            ):
                                all_evaluated = False
                                break
                        if not all_evaluated:
                            break
                    if all_evaluated:
                        break

        # Extract models from open branches
        models = []
        seen_models = set()
        for branch in self.open_branches:
            if not branch.is_closed:
                model = self._extract_model(branch)
                if model and model not in seen_models:
                    models.append(model)
                    seen_models.add(model)

        # Convert ACrQModel to base Model for type compatibility
        base_models = [model for model in models]  # ACrQModel inherits from Model

        return TableauResult(
            satisfiable=len(models) > 0,
            models=base_models,
            closed_branches=len(self.closed_branches),
            open_branches=len(self.open_branches),
            total_nodes=len(self.nodes),
            tableau=self,
        )

    def apply_rule(
        self, node, branch: Branch, rule_info: RuleInfo
    ) -> None:
        """Apply rule with special handling for LLM-Eval rules to ensure visibility."""
        from .tableau import TableauNode

        # For LLM-Eval rules, always show the conclusion nodes even if formulas already exist
        if rule_info.name.startswith("LLM-Eval"):
            conclusions = rule_info.conclusions

            if len(conclusions) == 1:
                # Non-branching LLM-Eval rule - always create visible nodes
                for signed_formula in conclusions[0]:
                    # Always create new node for LLM evaluation results
                    new_node = TableauNode(self.node_counter, signed_formula)
                    self.node_counter += 1
                    self.nodes.append(new_node)
                    node.add_child(new_node, rule_info.name)

                    # Check if this creates a contradiction and closes the branch
                    if branch.add_formula(signed_formula, new_node):
                        # Branch closed due to contradiction
                        if branch in self.open_branches:
                            self.open_branches.remove(branch)
                            self.closed_branches.append(branch)
                        return

                # Mark the formula as evaluated after successful rule application
                evaluation_key = f"llm_evaluated_{node.formula.formula}"
                if not hasattr(branch, "_llm_evaluated"):
                    branch._llm_evaluated = set()
                branch._llm_evaluated.add(evaluation_key)
            return

        # For non-LLM rules, use the standard logic
        super().apply_rule(node, branch, rule_info)
