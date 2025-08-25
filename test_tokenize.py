import sys
sys.path.insert(0, 'src')
from wkrq.acrq_parser import ACrQParser

parser = ACrQParser('[forall X Sedan(X)]~Van(X)', None)
tokens = parser._tokenize('[forall X Sedan(X)]~Van(X)')
print('Tokens:', tokens)
