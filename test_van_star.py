import sys
sys.path.insert(0, 'src')
from wkrq import parse_acrq_formula, SyntaxMode
from wkrq.formula import Constant

# Parse the universal formula
formula = parse_acrq_formula('[forall X Sedan(X)]~Van(X)', SyntaxMode.MIXED)
print(f'Original formula: {formula}')
print(f'Matrix: {formula.matrix}')
print(f'Matrix repr: {repr(formula.matrix)}')

# Check what string representation looks like
matrix_str = str(formula.matrix)
print(f'\nString of matrix: {matrix_str}')

# Now if we re-parse that string...
reparsed = parse_acrq_formula(matrix_str, SyntaxMode.MIXED)
print(f'\nReparsed from string: {reparsed}')
print(f'Reparsed type: {type(reparsed).__name__}')
print(f'Reparsed positive_name: {reparsed.positive_name}')
print(f'Reparsed negative_name: {reparsed.negative_name}')
print(f'Reparsed is_negative: {reparsed.is_negative}')
