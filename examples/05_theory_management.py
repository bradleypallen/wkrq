#!/usr/bin/env python3
"""
Theory Management Example - Natural Language Knowledge Base with ACrQ.

This example demonstrates a complete workflow for:
1. Asserting natural language statements to a theory
2. Translating them to ACrQ formulas
3. Checking satisfiability and detecting gluts/gaps
4. Inferring new knowledge
5. Managing theory updates
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wkrq.theory_manager import TheoryManager, NaturalLanguageTranslator
from wkrq.llm_integration import create_llm_tableau_evaluator


def demo_basic_theory():
    """Demonstrate basic theory management."""
    print("=" * 70)
    print("BASIC THEORY MANAGEMENT DEMO")
    print("=" * 70)
    
    # Create a theory manager
    manager = TheoryManager(theory_file=Path("demo_theory.json"))
    manager.clear()  # Start fresh
    
    print("\n1. ASSERTING NATURAL LANGUAGE STATEMENTS")
    print("-" * 40)
    
    # Assert some statements
    statements = [
        "Socrates is a human",
        "All humans are mortal",
        "Pluto is a planet",
        "Pluto is not a planet",  # This creates a glut!
    ]
    
    for nl in statements:
        stmt = manager.assert_statement(nl)
        print(f"✓ {stmt.id}: {stmt.natural_language}")
        if stmt.formula:
            print(f"  → {stmt.formula}")
    
    print("\n2. CHECKING SATISFIABILITY")
    print("-" * 40)
    
    satisfiable, info_states = manager.check_satisfiability()
    print(f"Theory is: {'SATISFIABLE' if satisfiable else 'UNSATISFIABLE'}")
    
    # Check for gluts and gaps
    gluts = [s for s in info_states if s.state == 'glut']
    gaps = [s for s in info_states if s.state == 'gap']
    
    if gluts:
        print(f"\n⚠ Found {len(gluts)} GLUT(S):")
        for glut in gluts:
            print(f"  - {glut.predicate}: conflicting evidence")
    
    if gaps:
        print(f"\n⚠ Found {len(gaps)} GAP(S):")
        for gap in gaps:
            print(f"  - {gap.predicate}: no evidence")
    
    print("\n3. INFERENCE")
    print("-" * 40)
    
    inferred = manager.infer_consequences()
    if inferred:
        print(f"Inferred {len(inferred)} new statement(s):")
        for stmt in inferred:
            print(f"  {stmt.id}: {stmt.natural_language}")
    else:
        print("No new consequences inferred")
    
    # Save the theory
    manager.save()
    print(f"\n✓ Theory saved to {manager.theory_file}")


def demo_advanced_reasoning():
    """Demonstrate advanced reasoning with quantifiers."""
    print("\n" + "=" * 70)
    print("ADVANCED REASONING DEMO")
    print("=" * 70)
    
    manager = TheoryManager(theory_file=Path("advanced_theory.json"))
    manager.clear()
    
    print("\n1. BUILDING A KNOWLEDGE BASE")
    print("-" * 40)
    
    # Build a more complex theory
    knowledge = [
        # Facts
        "Tweety is a bird",
        "Tweety is a penguin",
        "Opus is a penguin",
        
        # Rules
        "All birds can fly",
        "All penguins are birds",
        "Penguins cannot fly",  # Exception to the rule!
    ]
    
    for nl in knowledge:
        stmt = manager.assert_statement(nl)
        print(f"✓ {stmt.natural_language}")
    
    print("\n2. ANALYZING THE THEORY")
    print("-" * 40)
    
    report = manager.get_report()
    print(report)


def demo_with_llm():
    """Demonstrate theory management with LLM integration."""
    print("\n" + "=" * 70)
    print("LLM-ENHANCED THEORY DEMO")
    print("=" * 70)
    
    # Try to get an LLM evaluator
    llm_evaluator = None
    for provider in ["mock", "openai", "anthropic"]:
        try:
            llm_evaluator = create_llm_tableau_evaluator(provider)
            if llm_evaluator:
                print(f"✓ Using {provider} LLM evaluator")
                break
        except:
            continue
    
    if not llm_evaluator:
        print("⚠ No LLM evaluator available, skipping demo")
        return
    
    manager = TheoryManager(
        theory_file=Path("llm_theory.json"),
        llm_evaluator=llm_evaluator
    )
    manager.clear()
    
    print("\n1. ASSERTING FACTS ABOUT THE WORLD")
    print("-" * 40)
    
    facts = [
        "Mars is a planet",
        "Pluto orbits the sun",
        "All things that orbit the sun and are spherical are planets",
    ]
    
    for fact in facts:
        stmt = manager.assert_statement(fact)
        print(f"✓ {stmt.natural_language}")
    
    print("\n2. LLM-ENHANCED REASONING")
    print("-" * 40)
    
    satisfiable, info_states = manager.check_satisfiability()
    
    print(f"Theory satisfiability: {'YES' if satisfiable else 'NO'}")
    print("\nThe LLM evaluator provides real-world knowledge:")
    print("- It knows Mars is indeed a planet")
    print("- It knows Pluto's controversial status")
    print("- It can detect when formal rules conflict with reality")
    
    # Show any gluts from LLM knowledge
    gluts = [s for s in info_states if s.state == 'glut']
    if gluts:
        print(f"\n⚠ LLM detected {len(gluts)} conflict(s) with formal rules:")
        for glut in gluts:
            print(f"  - {glut.predicate}")


def demo_natural_language_patterns():
    """Show the natural language patterns that can be translated."""
    print("\n" + "=" * 70)
    print("NATURAL LANGUAGE TRANSLATION PATTERNS")
    print("=" * 70)
    
    translator = NaturalLanguageTranslator()
    
    examples = [
        # Simple predicates
        ("Socrates is a human", "Human(socrates)"),
        ("Mars is red", "Red(mars)"),
        
        # Negations
        ("Pluto is not a planet", "~Planet(pluto)"),
        ("Bob is not happy", "~Happy(bob)"),
        
        # Relations
        ("Alice loves Bob", "Loves(alice, bob)"),
        ("Earth orbits Sun", "Orbits(earth, sun)"),
        
        # Conditionals
        ("If Socrates is a human then Socrates is mortal", 
         "Human(socrates) -> Mortal(socrates)"),
        
        # Universals
        ("All humans are mortal", "[forall X Human(X)]Mortal(X)"),
        ("Every bird can fly", "[forall X Bird(X)]Fly(X)"),
        
        # Existentials
        ("Some bird is red", "[exists X Bird(X)]Red(X)"),
        
        # Conjunctions
        ("Tweety is a bird and a penguin", "Bird(tweety) & Penguin(tweety)"),
        
        # Disjunctions
        ("Opus is a bird or a fish", "Bird(opus) | Fish(opus)"),
    ]
    
    print("\nSupported patterns:")
    print("-" * 40)
    
    for nl, expected in examples:
        result = translator.translate(nl)
        status = "✓" if result else "✗"
        print(f"{status} '{nl}'")
        if result:
            print(f"   → {result}")
        else:
            print(f"   (Cannot translate)")
    
    print("\nNote: Complex statements may require manual formula specification")
    print("or LLM-based translation for best results.")


def demo_interactive_session():
    """Show how to use the interactive CLI."""
    print("\n" + "=" * 70)
    print("INTERACTIVE CLI USAGE")
    print("=" * 70)
    
    print("""
To use the interactive theory manager, run:

    python -m wkrq.theory_cli

Then use slash commands to manage your theory:

    theory> /assert Socrates is a human
    ✓ Asserted: S0001
      NL: Socrates is a human
      Formula: Human(socrates)

    theory> /assert All humans are mortal
    ✓ Asserted: S0002
      NL: All humans are mortal
      Formula: [forall X Human(X)]Mortal(X)

    theory> /check
    ✓ SATISFIABLE
    No gluts or gaps detected

    theory> /infer
    ✓ Inferred 1 new statement(s):
      I0003: Inferred: Mortal(socrates) is t
            → Mortal(socrates)

    theory> /report
    [Shows comprehensive analysis]

    theory> /save my_theory.json
    ✓ Theory saved to my_theory.json

The CLI provides a complete environment for:
- Building theories incrementally
- Testing logical consistency
- Detecting conflicting evidence (gluts)
- Identifying knowledge gaps
- Inferring new facts
- Persisting theories to disk
""")


def main():
    """Run all demonstrations."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     Theory Management with ACrQ - Comprehensive Example          ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # Run demos
    demo_basic_theory()
    demo_advanced_reasoning()
    demo_with_llm()
    demo_natural_language_patterns()
    demo_interactive_session()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
The Theory Manager provides a complete system for:

1. **Natural Language Input**: Express knowledge in plain English
2. **Automatic Translation**: Convert to ACrQ logical formulas
3. **Persistent Storage**: Save and load theories from JSON files
4. **Satisfiability Checking**: Verify logical consistency
5. **Gap Detection**: Find missing knowledge
6. **Glut Detection**: Identify conflicting evidence
7. **Inference Engine**: Derive new facts from existing knowledge
8. **LLM Integration**: Enhance with real-world knowledge
9. **Interactive CLI**: Manage theories with slash commands

This enables building sophisticated knowledge bases that can:
- Handle incomplete information (gaps)
- Manage conflicting evidence (gluts)
- Reason paraconsistently without explosion
- Integrate formal logic with real-world knowledge
""")
    
    # Clean up demo files
    for f in ["demo_theory.json", "advanced_theory.json", "llm_theory.json"]:
        p = Path(f)
        if p.exists():
            p.unlink()
            print(f"✓ Cleaned up {f}")


if __name__ == "__main__":
    main()