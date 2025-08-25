#!/usr/bin/env python3
"""
Interactive CLI for Theory Management.

Provides an interactive environment for managing logical theories
with natural language input and ACrQ reasoning.
"""

import cmd
import os
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .llm_integration import create_llm_tableau_evaluator
from .theory_manager import TheoryManager

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv

    # Look for .env file in current directory or parent directories
    current_path = Path.cwd()
    for _ in range(3):  # Check up to 3 levels up
        env_file = current_path / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            break
        current_path = current_path.parent
except ImportError:
    pass  # dotenv not installed


class TheoryCLI(cmd.Cmd):
    """Interactive theory management CLI."""

    intro = ""  # Will be set in __init__ after checking LLM status

    prompt = "theory> "

    def __init__(self, theory_file: Path = Path("theory.json")):
        super().__init__()
        self.manager = TheoryManager(theory_file=theory_file)
        self.llm_provider: Optional[str] = None
        self.loaded_from: Optional[Path] = None  # Track what file we loaded from

        # Enable tab completion (if readline is available)
        try:
            import readline

            readline.set_completer_delims(" \t\n;")  # Customize word delimiters
        except ImportError:
            pass  # readline not available (e.g., on Windows)

        # Build intro message with LLM status
        self._build_intro_message()

    def _build_intro_message(self) -> None:
        """Build intro message with version and LLM status."""
        intro_lines = [f"ACrQ Theory Manager - wkrq version {__version__}"]

        # Check for available LLM providers
        available = []
        if os.getenv("OPENAI_API_KEY"):
            available.append("openai")
        if os.getenv("ANTHROPIC_API_KEY"):
            available.append("anthropic")
        if os.getenv("OPENROUTER_API_KEY"):
            available.append("openrouter")

        if available:
            intro_lines.append(f"LLM providers available: {', '.join(available)}")
        else:
            intro_lines.append("No LLM API keys found in environment")

        intro_lines.append("Type 'help' for available commands.")

        # Set the intro message
        self.intro = "\n".join(intro_lines) + "\n"

    def do_assert(self, arg: str) -> None:
        """assert [sign:] <statement> - Add a statement with optional sign.

        Signs: t (true), f (false), e (error/undefined), m (meaningful), n (nontrue), v (variable)
        Default sign is 't' if not specified.

        Examples:
            assert Socrates is a human              # Defaults to t:
            assert t: All humans are mortal         # Explicitly true
            assert f: Pluto is a planet            # Assert as false
            assert e: Undefined predicate          # Assert as undefined
        """
        if not arg:
            print("Error: Please provide a statement to assert")
            return

        # Check for sign prefix
        sign = "t"  # Default
        statement = arg

        # Parse sign if provided
        if ":" in arg[:3]:  # Check first 3 chars for sign
            parts = arg.split(":", 1)
            potential_sign = parts[0].strip()
            if potential_sign in ["t", "f", "e", "m", "n", "v"]:
                sign = potential_sign
                statement = parts[1].strip()

        try:
            stmt = self.manager.assert_statement(statement, sign=sign)
            print(f"✓ Asserted: {stmt.id}")
            print(f"  NL: {stmt.natural_language}")
            print(f"  Sign: {sign}")
            if stmt.formula and not stmt.formula.startswith("//"):
                print(f"  Formula: {sign}:{stmt.formula}")
            else:
                print("  Formula: [Could not translate]")
        except ValueError as e:
            print(f"Error: {e}")

    def do_retract(self, arg: str) -> None:
        """retract <id> [id2 id3...] | --inferred - Remove statement(s) by ID or all inferred.

        Examples:
            retract S0001              # Retract single statement
            retract S0001 S0002 I0003  # Retract multiple statements
            retract --inferred         # Retract all inferred statements
        """
        if not arg:
            print("Error: Please provide statement ID(s) or --inferred")
            return

        # Check for --inferred flag
        if arg.strip() == "--inferred":
            # Find and retract all inferred statements
            inferred_ids = []
            for stmt_id, stmt in self.manager.statements.items():
                if (
                    stmt.is_inferred
                    or stmt_id.startswith("I")
                    or stmt_id.startswith("E")
                ):
                    inferred_ids.append(stmt_id)

            if not inferred_ids:
                print("No inferred statements to retract")
                return

            # Retract all inferred statements
            retracted_count = 0
            for stmt_id in inferred_ids:
                if self.manager.retract_statement(stmt_id):
                    retracted_count += 1

            print(
                f"✓ Retracted {retracted_count} inferred statement(s): {', '.join(inferred_ids)}"
            )
        else:
            # Parse multiple IDs
            stmt_ids = arg.split()
            retracted = []
            not_found = []

            for stmt_id in stmt_ids:
                if self.manager.retract_statement(stmt_id):
                    retracted.append(stmt_id)
                else:
                    not_found.append(stmt_id)

            if retracted:
                print(f"✓ Retracted: {', '.join(retracted)}")
            if not_found:
                print(f"Error: Not found: {', '.join(not_found)}")

    def do_list(self, arg: str) -> None:
        """list [asserted] - List all statements or only asserted ones."""
        only_asserted = arg.lower() == "asserted"
        statements = self.manager.list_statements(only_asserted)

        if not statements:
            print("No statements in theory")
            return

        print("\nCurrent Theory:")
        print("-" * 70)
        for stmt in statements:
            # Determine marker based on statement ID prefix
            if stmt.id.startswith("S"):
                marker = "[A]"  # Asserted by user
            elif stmt.id.startswith("I"):
                marker = "[I]"  # Inferred by tableau
            elif stmt.id.startswith("E"):
                marker = "[E]"  # Evidence from LLM
            else:
                marker = "[?]"  # Unknown type

            print(f"{stmt.id} {marker}: {stmt.natural_language}")
            if stmt.formula and not stmt.formula.startswith("//"):
                # Show the actual sign from the statement
                print(f"       → {stmt.sign}:{stmt.formula}")
        print("-" * 70)
        print(f"Total: {len(statements)} statements")

        # Show legend if there are different types
        types_present = set()
        for stmt in statements:
            if stmt.id.startswith("S"):
                types_present.add("A")
            elif stmt.id.startswith("I"):
                types_present.add("I")
            elif stmt.id.startswith("E"):
                types_present.add("E")

        if len(types_present) > 1:
            print("Legend: [A]=Asserted, [I]=Inferred, [E]=LLM Evidence")

    def do_check(self, arg: str) -> None:
        """check - Check if the current theory is satisfiable."""
        print("Checking satisfiability...")
        satisfiable, info_states = self.manager.check_satisfiability()

        print(f"{'✓ Satisfiable' if satisfiable else '✗ Unsatisfiable'}")

        # Report gluts and gaps
        gluts = [s for s in info_states if s.state == "glut"]
        gaps = [s for s in info_states if s.state == "gap"]

        if gluts:
            glut_word = "glut" if len(gluts) == 1 else "gluts"
            print(f"⚠ Found {len(gluts)} {glut_word} (conflicting evidence):")
            for glut in gluts:
                # Get the evidence statements
                evidence_lines = []
                for ev in glut.evidence:
                    # Extract formula from evidence (format is "sign:formula")
                    if ":" in ev:
                        sign, formula = ev.split(":", 1)
                        # Find matching statement
                        stmt_id = None
                        marker = None
                        for stmt in self.manager.statements.values():
                            if stmt.formula == formula:
                                stmt_id = stmt.id
                                # Determine marker based on ID
                                if stmt.id.startswith("S"):
                                    marker = "[A]"
                                elif stmt.id.startswith("I"):
                                    marker = "[I]"
                                elif stmt.id.startswith("E"):
                                    marker = "[E]"
                                break
                        if stmt_id and marker:
                            evidence_lines.append(f"  {stmt_id} {marker}: {ev}")

                # Only show unique evidence (avoid duplicates)
                seen = set()
                for line in evidence_lines:
                    if line not in seen:
                        print(line)
                        seen.add(line)

        if gaps:
            gap_word = "gap" if len(gaps) == 1 else "gaps"
            print(f"⚠ Found {len(gaps)} {gap_word} (lack of knowledge):")
            for gap in gaps:
                # Display gap evidence in same format
                for ev in gap.evidence:
                    if ":" in ev:
                        sign, formula = ev.split(":", 1)
                        # Find matching statement
                        stmt_id = None
                        marker = None
                        for stmt in self.manager.statements.values():
                            if stmt.formula == formula:
                                stmt_id = stmt.id
                                if stmt.id.startswith("S"):
                                    marker = "[A]"
                                elif stmt.id.startswith("I"):
                                    marker = "[I]"
                                elif stmt.id.startswith("E"):
                                    marker = "[E]"
                                break
                        if stmt_id and marker:
                            print(f"  {stmt_id} {marker}: {ev}")

        if not gluts and not gaps and satisfiable:
            print("✓ No gluts or gaps detected")

    def do_infer(self, arg: str) -> None:
        """infer - Infer logical consequences from the current theory."""
        print("Inferring consequences...")
        inferred = self.manager.infer_consequences()

        if inferred:
            print(f"✓ Inferred {len(inferred)} new statement(s):")
            for stmt in inferred:
                # Determine the marker based on ID prefix
                if stmt.id.startswith("E"):
                    marker = "[E]"  # LLM Evidence
                else:
                    marker = "[I]"  # Regular inference

                # Show in format: <id> [I/E]: <sign>:<formula>
                if stmt.formula:
                    print(f"  {stmt.id} {marker}: {stmt.sign}:{stmt.formula}")
                else:
                    print(f"  {stmt.id} {marker}: [no formula]")
        else:
            print("No new consequences could be inferred")

    def do_report(self, arg: str) -> None:
        """report - Generate a comprehensive analysis report."""
        report = self.manager.get_report()
        print("\n" + report)

    def do_clear(self, arg: str) -> None:
        """clear - Clear all statements from the theory."""
        confirm = input("Are you sure you want to clear all statements? (y/n): ")
        if confirm.lower() == "y":
            self.manager.clear()
            print("✓ Theory cleared")
        else:
            print("Cancelled")

    def complete_save(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        """Provide filename completion for save command."""
        import glob
        import os

        # Get the directory and partial filename
        if "/" in text:
            # Has directory component
            dir_path = os.path.dirname(text)
            partial = os.path.basename(text)
            search_pattern = os.path.join(dir_path, partial + "*")
        else:
            # Current directory
            partial = text
            search_pattern = partial + "*"

        # Find matching files and directories
        matches = []
        has_dir = False
        for path in glob.glob(search_pattern):
            if os.path.isdir(path):
                matches.append(path + "/")
                has_dir = True
            else:
                # Prefer .json files but show all
                matches.append(path)

        # Only suggest .json extension if:
        # 1. We have a partial name without extension
        # 2. No directories match (to avoid "examples.json" when typing "examples/")
        # 3. No exact matches already exist
        if partial and "." not in partial and not has_dir and not matches:
            json_suggestion = partial + ".json"
            matches.append(json_suggestion)

        return matches

    def do_save(self, arg: str) -> None:
        """save [filename] - Save the theory to a file.

        Without filename: saves to current working file (theory.json by default)
        With filename: saves to specified file

        Note: After loading a file, auto-save is disabled to prevent overwriting
        the original. Use 'save' explicitly to save changes.
        """
        if arg:
            file_path = Path(arg)
            # Update the working file
            self.manager.theory_file = file_path
            self.loaded_from = None  # No longer working from a loaded file
        else:
            file_path = self.manager.theory_file

            # Warn if saving over a loaded file
            if self.loaded_from and file_path == self.loaded_from:
                confirm = input(
                    f"This will overwrite the loaded file {file_path}. Continue? (y/n): "
                )
                if confirm.lower() != "y":
                    print("Save cancelled")
                    return

        self.manager.save()
        print(f"✓ Theory saved to {file_path}")

        # Save was successful

    def complete_load(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        """Provide filename completion for load command."""
        import glob
        import os

        # Check if we're completing the --merge flag
        if text.startswith("--"):
            return ["--merge"]

        # Check if --merge was already typed
        if "--merge" in line[:begidx]:
            # We're after --merge, complete filenames
            pass
        elif " " in line and not text:
            # Space after filename, suggest --merge
            return ["--merge"]

        # Get the directory and partial filename
        if "/" in text:
            # Has directory component
            dir_path = os.path.dirname(text)
            partial = os.path.basename(text)
            search_pattern = os.path.join(dir_path, partial + "*")
        else:
            # Current directory
            partial = text
            search_pattern = partial + "*"

        # Find matching files and directories
        matches = []
        for path in glob.glob(search_pattern):
            if os.path.isdir(path):
                matches.append(path + "/")
            elif path.endswith(".json"):
                # Prioritize .json files
                matches.insert(0, path)
            else:
                matches.append(path)

        # If no matches and we have a partial name, suggest .json extension
        if partial and "." not in partial and not matches:
            matches.append(partial + ".json")

        return matches

    def do_load(self, arg: str) -> None:
        """load [filename] [--merge] - Load a theory from a file.

        By default, replaces the current theory. Use --merge to combine.

        Examples:
            load                     # Load from default theory.json
            load my_theory.json      # Load from specific file
            load axioms.json --merge # Add to current theory
        """
        # Parse arguments
        merge = False
        filename = None

        if arg:
            parts = arg.split()
            for part in parts:
                if part == "--merge":
                    merge = True
                else:
                    filename = part

        file_path = Path(filename) if filename else self.manager.theory_file

        if not file_path.exists():
            print(f"Error: File {file_path} not found")
            return

        if merge:
            # Store current statements
            current_statements = dict(self.manager.statements)
            current_next_id = self.manager.next_id
            original_file = self.manager.theory_file

            # Load new statements into a temporary manager
            temp_manager = TheoryManager(theory_file=file_path)
            temp_manager.load()
            loaded_statements = dict(temp_manager.statements)

            # Restore original state and merge
            self.manager.statements = current_statements
            self.manager.next_id = current_next_id
            self.manager.theory_file = original_file

            # Add loaded statements with new IDs if needed
            id_mapping = {}  # Track ID changes for reference
            for stmt_id, stmt in loaded_statements.items():
                # Check for ID conflict
                if stmt_id in self.manager.statements:
                    # Generate new ID
                    new_id = f"{stmt_id[0]}{self.manager.next_id:04d}"
                    self.manager.next_id += 1
                    stmt.id = new_id
                    id_mapping[stmt_id] = new_id
                    stmt_id = new_id

                self.manager.statements[stmt_id] = stmt

            print(f"✓ Merged theory from {file_path}")
            print(f"  Added {len(loaded_statements)} statements")
            if id_mapping:
                print(f"  Renamed {len(id_mapping)} statements to avoid conflicts")

            # Don't change loaded_from for merge, but note the merge
            print(f"  Working file remains: {self.manager.theory_file}")
        else:
            # Replace current theory
            if self.manager.statements:
                confirm = input(
                    "This will replace the current theory. Continue? (y/n): "
                )
                if confirm.lower() != "y":
                    print("Load cancelled")
                    return

            self.manager.theory_file = file_path
            self.manager.load()
            print(f"✓ Theory loaded from {file_path}")
            print(f"  Loaded {len(self.manager.statements)} statements")

            # Track that we loaded from this file
            self.loaded_from = file_path

    def do_claim(self, arg: str) -> None:
        """claim <statement> - Assert a factual claim, verifying with LLM if available.

        For atomic formulas with LLM available: queries LLM first, then asserts the result.
        For compound formulas or no LLM: behaves like regular assert.

        Examples:
            claim firstManOnTheMoon(armstrong)  # LLM verifies, then asserts result
            claim Paris is the capital of France  # Translates and verifies if atomic
            claim P(x) & Q(y)  # Compound formula, asserted as true
        """
        if not arg:
            print("Error: Please provide a statement to claim")
            return

        # Check if LLM evaluator is available
        if not self.manager.llm_evaluator:
            # No LLM available, fall back to regular assertion
            print("Note: No LLM evaluator available, treating as regular assertion")
            return self.do_assert(arg)

        # Try to parse as formula or translate from natural language
        formula_str = arg
        original_nl = arg

        # First, try to parse as a formula directly
        try:
            from wkrq.acrq_parser import SyntaxMode, parse_acrq_formula

            formula = parse_acrq_formula(arg, SyntaxMode.MIXED)
            # It's a valid formula
        except Exception:
            # Not a valid formula, try to translate
            translated = self.manager.translator.translate(arg)
            if translated:
                formula_str = translated
                try:
                    formula = parse_acrq_formula(formula_str, SyntaxMode.MIXED)
                except Exception as e:
                    print(f"Error: Could not parse translated formula: {e}")
                    return
            else:
                print(f"Error: Could not translate or parse: {arg}")
                return

        # Check if it's atomic
        if not formula.is_atomic():
            # Compound formula, can't verify with LLM
            print(
                "Note: Compound formula cannot be verified with LLM, asserting as true"
            )
            return self.do_assert(arg)

        # Evaluate using the LLM
        print(f"Verifying claim with LLM: {formula}")
        if self.manager.llm_evaluator is not None and hasattr(
            self.manager.llm_evaluator, "model_info"
        ):
            model_info = self.manager.llm_evaluator.model_info
            print(f"Using: {model_info['provider']} / {model_info['model']}")

        try:
            result = (
                self.manager.llm_evaluator(formula)
                if self.manager.llm_evaluator is not None
                else None
            )

            if result is None:
                print("No LLM evaluation available, asserting as true")
                return self.do_assert(arg)

            # Determine the appropriate sign based on LLM result
            from wkrq.semantics import FALSE, TRUE, UNDEFINED

            if result.positive == TRUE and result.negative == FALSE:
                sign = "t"
                interpretation = "TRUE (verified by LLM)"
            elif result.positive == FALSE and result.negative == TRUE:
                sign = "f"
                interpretation = "FALSE (refuted by LLM)"
            elif result.positive == UNDEFINED and result.negative == UNDEFINED:
                sign = "e"
                interpretation = "UNDEFINED (no evidence from LLM)"
            elif result.positive == TRUE and result.negative == TRUE:
                # Glut - need to add both P and P*
                print(f"LLM reports conflicting evidence (glut) for: {formula}")
                # Add positive assertion
                stmt1 = self.manager.assert_statement(
                    natural_language=original_nl, formula=formula_str, sign="t"
                )
                print(f"✓ Asserted: {stmt1.id}")
                print("  Sign: t")
                print(f"  Formula: {formula_str}")

                # Add negative assertion (bilateral predicate)
                from wkrq.formula import BilateralPredicateFormula, PredicateFormula

                if isinstance(formula, (PredicateFormula, BilateralPredicateFormula)):
                    star_formula = f"{formula.predicate_name}*({','.join(str(t) for t in formula.terms)})"
                    stmt2 = self.manager.assert_statement(
                        natural_language=f"{original_nl} (negative evidence)",
                        formula=star_formula,
                        sign="t",
                    )
                    print(f"✓ Asserted: {stmt2.id}")
                    print("  Sign: t")
                    print(f"  Formula: {star_formula}")
                    print("  Note: LLM reported conflicting evidence (glut)")
                return
            else:
                # Gap - neither true nor false
                sign = "e"
                interpretation = "GAP (neither true nor false per LLM)"

            # Assert the statement with the determined sign
            stmt = self.manager.assert_statement(
                natural_language=original_nl, formula=formula_str, sign=sign
            )

            print(f"✓ Claimed: {stmt.id}")
            print(f"  Sign: {sign}")
            print(f"  Formula: {formula_str}")
            print(f"  LLM verdict: {interpretation}")

            # Store LLM metadata
            stmt.metadata["llm_evaluated"] = True
            if self.manager.llm_evaluator is not None and hasattr(
                self.manager.llm_evaluator, "model_info"
            ):
                stmt.metadata.update(self.manager.llm_evaluator.model_info)

            # Statement added successfully

        except Exception as e:
            print(f"Error evaluating with LLM: {e}")
            print("Falling back to regular assertion")
            return self.do_assert(arg)

    def do_evaluate(self, arg: str) -> None:
        """evaluate <formula> [--assert] - Get LLM evaluation for an atomic formula.

        Examples:
            evaluate Planet(pluto)            # Check if Pluto is a planet
            evaluate Mortal(socrates)          # Check if Socrates is mortal
            evaluate Red(mars) --assert        # Evaluate and add to theory

        Options:
            --assert    Add the evaluation result to the theory

        Returns the LLM's assessment as:
            - TRUE/FALSE for definite knowledge
            - UNDEFINED if the LLM has no knowledge
            - Shows both positive and negative evidence
        """
        if not arg:
            print("Error: Please provide a formula to evaluate")
            return

        # Check for --assert flag
        should_assert = False
        formula_str = arg.strip()
        if "--assert" in formula_str:
            should_assert = True
            formula_str = formula_str.replace("--assert", "").strip()

        if not self.llm_provider:
            print("Error: No LLM provider configured. Use 'llm <provider>' first")
            return

        # Try to parse the formula
        try:
            from wkrq.acrq_parser import parse_acrq_formula

            formula = parse_acrq_formula(formula_str)
        except Exception as e:
            print(f"Error parsing formula: {e}")
            return

        # Check if it's atomic
        if not formula.is_atomic():
            print("Error: Only atomic formulas can be evaluated by LLM")
            print(
                "       Atomic formulas are predicates like P(x) or propositional atoms"
            )
            return

        # Evaluate using the LLM
        print(f"\nEvaluating: {formula}")
        if self.manager.llm_evaluator is not None and hasattr(
            self.manager.llm_evaluator, "model_info"
        ):
            model_info = self.manager.llm_evaluator.model_info
            print(f"Using: {model_info['provider']} / {model_info['model']}")

        try:
            result = (
                self.manager.llm_evaluator(formula)
                if self.manager.llm_evaluator is not None
                else None if self.manager.llm_evaluator else None
            )

            if result is None:
                print("Result: No evaluation available")
                return

            # Display the bilateral truth value
            print("\nLLM Evaluation:")
            print(f"  Positive evidence (P is true): {result.positive}")
            print(f"  Negative evidence (P is false): {result.negative}")

            # Interpret the result
            from wkrq.semantics import FALSE, TRUE, UNDEFINED

            if result.positive == TRUE and result.negative == FALSE:
                print(f"\nInterpretation: {formula} is TRUE")
                print("  The LLM has positive evidence for this statement")
            elif result.positive == FALSE and result.negative == TRUE:
                print(f"\nInterpretation: {formula} is FALSE")
                print("  The LLM has negative evidence for this statement")
            elif result.positive == UNDEFINED and result.negative == UNDEFINED:
                print(f"\nInterpretation: {formula} is UNDEFINED")
                print("  The LLM has no knowledge about this statement")
            elif result.positive == TRUE and result.negative == TRUE:
                print(f"\nInterpretation: {formula} is a GLUT")
                print("  The LLM has conflicting evidence (both true and false)")
            elif result.positive == FALSE and result.negative == FALSE:
                print(f"\nInterpretation: {formula} is a GAP")
                print("  The LLM knows this is neither true nor false")
            else:
                print("\nInterpretation: Complex state")

            # Assert the result if requested
            if should_assert:
                from datetime import datetime

                from wkrq.theory_manager import Statement

                # Determine what to assert based on the evaluation
                if result.positive == TRUE and result.negative == FALSE:
                    # Assert as true
                    stmt_id = f"E{self.manager.next_id:04d}"
                    self.manager.next_id += 1

                    metadata = {
                        "source": "llm_evaluation",
                        "evaluation_type": "direct_query",
                    }
                    if self.manager.llm_evaluator is not None and hasattr(
                        self.manager.llm_evaluator, "model_info"
                    ):
                        metadata.update(self.manager.llm_evaluator.model_info)

                    stmt = Statement(
                        id=stmt_id,
                        natural_language=f"LLM evaluation: {formula} is true",
                        formula=str(formula),
                        sign="t",
                        is_inferred=True,
                        timestamp=datetime.now().isoformat(),
                        metadata=metadata,
                    )
                    self.manager.statements[stmt_id] = stmt
                    print(f"\n✓ Added to theory as {stmt_id}")

                elif result.positive == FALSE and result.negative == TRUE:
                    # Assert as false (using bilateral predicate)
                    stmt_id = f"E{self.manager.next_id:04d}"
                    self.manager.next_id += 1

                    # Create bilateral negative formula
                    from wkrq.formula import BilateralPredicateFormula, PredicateFormula

                    if isinstance(formula, PredicateFormula):
                        bilateral_formula = BilateralPredicateFormula(
                            positive_name=formula.predicate_name,
                            terms=formula.terms,
                            is_negative=True,
                        )
                        formula_str = str(bilateral_formula)
                    else:
                        formula_str = f"~{formula}"

                    metadata = {
                        "source": "llm_evaluation",
                        "evaluation_type": "direct_query",
                    }
                    if self.manager.llm_evaluator is not None and hasattr(
                        self.manager.llm_evaluator, "model_info"
                    ):
                        metadata.update(self.manager.llm_evaluator.model_info)

                    stmt = Statement(
                        id=stmt_id,
                        natural_language=f"LLM evaluation: {formula} is false",
                        formula=formula_str,
                        sign="t",
                        is_inferred=True,
                        timestamp=datetime.now().isoformat(),
                        metadata=metadata,
                    )
                    self.manager.statements[stmt_id] = stmt
                    print(f"\n✓ Added to theory as {stmt_id}")

                elif result.positive == UNDEFINED and result.negative == UNDEFINED:
                    print(
                        "\n⚠ Cannot assert: LLM has no knowledge about this statement"
                    )
                else:
                    print(
                        "\n⚠ Cannot assert: LLM evaluation is not definite (glut or gap)"
                    )

        except Exception as e:
            print(f"Error during evaluation: {e}")

    def do_llm(self, arg: str) -> None:
        """llm <provider> [model] [api_key] - Enable LLM evaluator.

        Providers: openai, anthropic, openrouter, mock

        Examples:
            llm openai                          # Use default model (gpt-4)
            llm openai gpt-4o                   # Use specific model
            llm anthropic claude-3-opus         # Use specific Anthropic model
            llm openrouter meta-llama/llama-3.1 # Use model via OpenRouter
            llm openai gpt-4o sk-abc123...      # Model + API key
            llm status                          # Show current LLM status
            llm list                            # List available providers
        """
        if not arg:
            if self.llm_provider:
                print(f"Current LLM provider: {self.llm_provider}")
                # Check if API key is set
                env_var = {
                    "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                    "openrouter": "OPENROUTER_API_KEY",
                }.get(self.llm_provider)
                if env_var and os.getenv(env_var):
                    print(f"  Using API key from {env_var}")
            else:
                print("No LLM provider set")
                print("Use: llm <provider> [api_key]")
            return

        # Parse arguments (provider, optional model, optional api_key)
        parts = arg.split()
        provider = parts[0].lower()
        model = None
        api_key = None

        # Determine what the additional arguments are
        if len(parts) > 1:
            # Check if second arg looks like an API key
            if parts[1].startswith(("sk-", "claude-", "key-")):
                api_key = parts[1]
            else:
                # Assume it's a model name
                model = parts[1]
                # Check for API key as third argument
                if len(parts) > 2:
                    api_key = parts[2]

        # Handle special commands
        if provider == "status":
            self.do_llm("")  # Call with no args to show status
            return
        elif provider == "list":
            print("Available LLM providers:")
            print("  - openai     : OpenAI GPT models")
            print("  - anthropic  : Anthropic Claude models")
            print("  - openrouter : Access to various models via OpenRouter")
            print("  - mock       : Mock evaluator for testing")

            # Check which have API keys available
            if os.getenv("OPENAI_API_KEY"):
                print("\n✓ OpenAI API key found in environment")
            if os.getenv("ANTHROPIC_API_KEY"):
                print("✓ Anthropic API key found in environment")
            if os.getenv("OPENROUTER_API_KEY"):
                print("✓ OpenRouter API key found in environment")
            return

        # Validate provider
        if provider not in ["openai", "anthropic", "openrouter", "mock"]:
            print(f"Error: Unknown provider '{provider}'")
            print("Available providers: openai, anthropic, openrouter, mock")
            return

        # Set API key in environment if provided
        if api_key:
            env_var = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "openrouter": "OPENROUTER_API_KEY",
            }.get(provider)

            if env_var:
                os.environ[env_var] = api_key
                print(f"✓ Set {env_var}")

        # Try to create evaluator
        try:
            if model:
                evaluator = create_llm_tableau_evaluator(provider, model=model)
            else:
                evaluator = create_llm_tableau_evaluator(provider)
            if evaluator:
                self.manager.llm_evaluator = evaluator
                self.llm_provider = provider

                # Get model info from evaluator
                model_name = "unknown"
                if hasattr(evaluator, "model_info"):
                    model_name = evaluator.model_info.get("model", "unknown")

                print(f"✓ LLM evaluator enabled: {provider}")
                print(f"  Model: {model_name}")

                # Show source of API key
                if provider != "mock":
                    env_var = {
                        "openai": "OPENAI_API_KEY",
                        "anthropic": "ANTHROPIC_API_KEY",
                        "openrouter": "OPENROUTER_API_KEY",
                    }.get(provider)
                    if api_key:
                        print("  Using provided API key")
                    elif env_var and os.getenv(env_var):
                        print("  Using API key from environment")
            else:
                print(f"Error: Could not create LLM evaluator for {provider}")
                if provider != "mock":
                    env_var = {
                        "openai": "OPENAI_API_KEY",
                        "anthropic": "ANTHROPIC_API_KEY",
                        "openrouter": "OPENROUTER_API_KEY",
                    }.get(provider)
                    if env_var and not os.getenv(env_var):
                        print(
                            f"  No {env_var} found. Provide with: llm {provider} <api_key>"
                        )
        except Exception as e:
            print(f"Error: {e}")

    def do_help(self, arg: str) -> None:
        """help [command] - Show available commands or help for a specific command.

        Examples:
            help           - Show all commands
            help assert    - Show help for assert command
            help llm       - Show help for llm command
        """
        if arg:
            # Show help for specific command
            cmd_method = getattr(self, f"do_{arg}", None)
            if cmd_method and cmd_method.__doc__:
                print(cmd_method.__doc__)
            else:
                print(f"No help available for '{arg}'")
        else:
            # Show full command list
            print("\nACrQ Theory Manager Commands")
            print("=" * 40)
            print("\nBasic Commands:")
            print("  assert <statement>  - Add a natural language statement")
            print("  retract <id>        - Remove a statement by ID")
            print("  list                - Show all statements")
            print("  check               - Check satisfiability")
            print("  infer               - Infer new statements")
            print("  evaluate <formula>  - Get LLM evaluation for atomic formula")
            print("  report              - Generate full analysis report")
            print("  clear               - Clear all statements")
            print("  save [file]         - Save theory to file")
            print("  load [file]         - Load theory from file")
            print("\nLLM Integration:")
            print("  llm list            - Show available LLM providers")
            print("  llm status          - Show current LLM configuration")
            print(
                "  llm <provider>      - Enable LLM (openai, anthropic, openrouter, mock)"
            )
            print("  llm <provider> <key> - Enable LLM with API key")
            print("\nOther:")
            print("  help [command]      - Show help for a specific command")
            print("  quit                - Exit")
            print("\nNote: Commands can optionally be prefixed with '/'\n")

    def do_quit(self, arg: str) -> bool:
        """quit - Exit the theory manager."""
        return True

    def do_exit(self, arg: str) -> bool:
        """Alias for quit."""
        return self.do_quit(arg)

    def default(self, line: str) -> None:
        """Handle unrecognized input. Slash prefix is optional for commands."""
        if line.startswith("/"):
            # Extract command and args (slash prefix is optional but supported)
            parts = line[1:].split(None, 1)
            if not parts:
                print("Unknown command. Type 'help' for available commands.")
                return

            cmd = parts[0]
            args = parts[1] if len(parts) > 1 else ""

            # Try to call the appropriate method
            method_name = f"do_{cmd}"
            if hasattr(self, method_name):
                getattr(self, method_name)(args)
            else:
                print(f"Unknown command: /{cmd}")
                print("Type 'help' for available commands.")
        else:
            # Don't automatically treat unknown input as assertions
            if line.strip():
                print(f"Unknown command: {line.split()[0]}")
                print("Type 'help' for available commands.")
                print("To make an assertion, use: assert <statement>")

    def emptyline(self) -> bool:
        """Do nothing on empty line."""
        return False

    def precmd(self, line: str) -> str:
        """Pre-process commands to handle slash syntax."""
        # Strip leading/trailing whitespace
        line = line.strip()

        # Convert slash commands to method calls
        if line.startswith("/"):
            parts = line[1:].split(None, 1)
            if parts:
                cmd = parts[0]
                args = parts[1] if len(parts) > 1 else ""
                return f"{cmd} {args}"

        return line


def main() -> None:
    """Main entry point for the theory CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="ACrQ Theory Manager CLI")
    parser.add_argument(
        "--file",
        "-f",
        type=Path,
        default=Path("theory.json"),
        help="Theory file to use (default: theory.json)",
    )
    parser.add_argument(
        "--llm", choices=["openai", "anthropic", "mock"], help="Enable LLM evaluator"
    )

    args = parser.parse_args()

    # Create and configure CLI
    cli = TheoryCLI(theory_file=args.file)

    if args.llm:
        cli.do_llm(args.llm)

    # Run interactive loop
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print()  # Just print newline for clean exit
        sys.exit(0)


if __name__ == "__main__":
    main()
