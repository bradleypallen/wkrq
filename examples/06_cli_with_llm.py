#!/usr/bin/env python3
"""
Demonstration of Theory CLI with automatic .env detection and LLM integration.

This example shows how the CLI:
1. Automatically loads .env files
2. Detects available LLM providers
3. Allows dynamic API key configuration
"""

import os
import sys
from pathlib import Path

# Ensure we can import wkrq
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def demo_cli_features():
    """Demonstrate the enhanced CLI features."""
    print("=" * 70)
    print("THEORY CLI WITH LLM INTEGRATION")
    print("=" * 70)
    
    print("\n1. AUTOMATIC .ENV DETECTION")
    print("-" * 40)
    print("""
The CLI automatically searches for .env files:
- In the current directory
- Up to 3 parent directories
- Loads API keys automatically
""")
    
    # Check what's available
    env_status = []
    if os.getenv('OPENAI_API_KEY'):
        env_status.append("✓ OpenAI API key found")
    if os.getenv('ANTHROPIC_API_KEY'):
        env_status.append("✓ Anthropic API key found")
    
    if env_status:
        for status in env_status:
            print(status)
    else:
        print("ℹ No API keys found in environment")
    
    print("\n2. ENHANCED /llm COMMAND")
    print("-" * 40)
    print("""
New /llm command features:

  /llm list                    # Show available providers
  /llm status                  # Show current LLM configuration
  /llm openai                  # Use OpenAI with env API key
  /llm anthropic               # Use Anthropic with env API key
  /llm openai sk-abc123...     # Provide API key directly
  /llm mock                    # Use mock evaluator for testing
""")
    
    print("\n3. INTERACTIVE SESSION EXAMPLE")
    print("-" * 40)
    print("""
Start the CLI with:
  python -m wkrq.theory_cli

Example session:
""")
    
    example_session = """
theory> /llm list
Available LLM providers:
  - openai    : OpenAI GPT models
  - anthropic : Anthropic Claude models
  - mock      : Mock evaluator for testing

✓ OpenAI API key found in environment
✓ Anthropic API key found in environment

theory> /llm openai
✓ LLM evaluator enabled: openai
  Using API key from environment

theory> /assert Mars is a planet
✓ Asserted: S0001
  NL: Mars is a planet
  Formula: Planet(mars)

theory> /assert Pluto is a planet
✓ Asserted: S0002
  NL: Pluto is a planet
  Formula: Planet(pluto)

theory> /check
Checking satisfiability...

✓ SATISFIABLE

⚠ Found 1 GLUT(S) (conflicting evidence):
  - Planet(pluto)
    • t:Planet(pluto)
    • t:Planet*(pluto)  [from LLM: Pluto is not a planet]

theory> /report
[Full analysis with gluts and gaps detected by LLM]
"""
    
    print(example_session)
    
    print("\n4. PROGRAMMATIC USAGE")
    print("-" * 40)
    print("""
You can also use the TheoryManager directly in code:
""")
    
    code_example = '''
from wkrq import TheoryManager
from wkrq.llm_integration import create_llm_tableau_evaluator

# Create manager with LLM
llm = create_llm_tableau_evaluator('openai')
manager = TheoryManager(llm_evaluator=llm)

# Add statements
manager.assert_statement("Socrates is a human")
manager.assert_statement("All humans are mortal")

# Check and analyze
satisfiable, info_states = manager.check_satisfiability()
gluts = [s for s in info_states if s.state == 'glut']
gaps = [s for s in info_states if s.state == 'gap']
'''
    
    print(code_example)
    
    print("\n5. BENEFITS OF LLM INTEGRATION")
    print("-" * 40)
    print("""
With LLM integration, the system can:

• Detect real-world inconsistencies
  - "Pluto is a planet" vs astronomical classification
  
• Identify knowledge gaps
  - Predicates the LLM has no information about
  
• Provide semantic validation
  - Check if formal derivations match reality
  
• Handle paraconsistent reasoning
  - Manage conflicting evidence without explosion
  
• Bridge formal logic and common sense
  - Combine deductive reasoning with world knowledge
""")


def main():
    """Run the demonstration."""
    demo_cli_features()
    
    print("\n" + "=" * 70)
    print("TRY IT YOURSELF")
    print("=" * 70)
    print("""
To start the interactive CLI:

    python -m wkrq.theory_cli

The CLI will:
1. Automatically load your .env file
2. Detect available LLM providers
3. Let you manage theories with natural language
4. Provide real-world knowledge validation via LLMs
""")


if __name__ == "__main__":
    main()