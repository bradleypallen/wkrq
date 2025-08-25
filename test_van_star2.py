import sys
sys.path.insert(0, 'src')
from wkrq import parse_acrq_formula, SyntaxMode

# Parse the universal formula
formula = parse_acrq_formula('[forall X Sedan(X)]~Van(X)', SyntaxMode.MIXED)
matrix = formula.matrix

print(f'Matrix: {matrix}')
print(f'Matrix type: {type(matrix).__name__}')
print(f'Matrix positive_name: {matrix.positive_name}')
print(f'Matrix negative_name: {matrix.negative_name}')  
print(f'Matrix is_negative: {matrix.is_negative}')
print(f'Matrix get_base_name(): {matrix.get_base_name()}')
print(f'Matrix predicate_name (inherited): {matrix.predicate_name}')
