import sys
sys.path.insert(0, 'src')
from wkrq.acrq_parser import ACrQParser, SyntaxMode

# Test parsing just ~Van(X)
parser = ACrQParser('~Van(X)', SyntaxMode.MIXED)
result = parser.parse()
print(f'~Van(X) parsed to: {result}')
print(f'Type: {type(result).__name__}')
if hasattr(result, 'positive_name'):
    print(f'positive_name: {result.positive_name}')
    print(f'negative_name: {result.negative_name}')
    print(f'is_negative: {result.is_negative}')
