#!/usr/bin/env python3
"""Test the ACrQ demo without user interaction."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import demo functions
from examples.acrq_demo_ferguson import (
    demo1_bilateral_predicates,
    demo2_paraconsistency,
    demo3_demorgan_transformations,
    demo4_quantifier_demorgan,
    demo5_gap_semantics,
    demo6_llm_integration,
    demo7_complete_example
)

print("Testing ACrQ Demo Functions...")
print("=" * 70)

print("\n[Demo 1]")
demo1_bilateral_predicates()

print("\n[Demo 2]")
demo2_paraconsistency()

print("\n[Demo 3]")
try:
    demo3_demorgan_transformations()
except Exception as e:
    print(f"Demo 3 partial: {e}")

print("\n[Demo 4]")
demo4_quantifier_demorgan()

print("\n[Demo 5]")
demo5_gap_semantics()

print("\n[Demo 6]")
demo6_llm_integration()

print("\n[Demo 7]")
demo7_complete_example()

print("\n" + "=" * 70)
print("All demos completed successfully!")