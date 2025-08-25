import sys
sys.path.insert(0, 'src')

# Monkey-patch to add debug
from wkrq.acrq_parser import ACrQParser, MixedMode

orig_parse_restricted = ACrQParser._parse_restricted_quantifier

def debug_parse_restricted(self):
    print("DEBUG: Entering _parse_restricted_quantifier")
    print(f"  Current token: {self.current_token}")
    
    result = orig_parse_restricted(self)
    
    print(f"DEBUG: Result matrix: {result.matrix}")
    print(f"  Matrix type: {type(result.matrix).__name__}")
    if hasattr(result.matrix, 'positive_name'):
        print(f"  Matrix positive_name: {result.matrix.positive_name}")
        print(f"  Matrix is_negative: {result.matrix.is_negative}")
    
    return result

ACrQParser._parse_restricted_quantifier = debug_parse_restricted

# Now parse
from wkrq import parse_acrq_formula, SyntaxMode
formula = parse_acrq_formula('[forall X Sedan(X)]~Van(X)', SyntaxMode.MIXED)
print(f'\nFinal formula: {formula}')
