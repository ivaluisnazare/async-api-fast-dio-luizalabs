import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_two_plus_two_equals_four():
    result = 2 + 2
    assert result == 4
