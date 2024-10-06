import pytest

import randvar
from randvar import RV, Seq, anydice_casting, output, roll, settings_set
from parser.parse_and_exec import pipeline


settings_set('RV_IGNORE_ZERO_PROBS', True)
bv = (0, 1)

@pytest.mark.parametrize("code,res", [
('''
output ((1d4-1) | (1d2-1))
''', [RV(bv, (125, 875))]
),('''
output {2}&(1d2-1)
''', [RV(bv, (1, 1))]
),('''
output {2,-2}&(1d2-1)
''', [RV(bv, (1, 0))]
),('''
output {2}&{2,-1}
''', [1]
),('''
output {2,-2}&{2,-2}
''', [0]
),])
def test_parse_and_exec(code, res):
    i = 0
    def check_res(x):
        nonlocal i
        expected = res[i]
        print(x)
        assert type(x) == type(expected), f'types expected {type(expected)} got {type(x)}'
        if not isinstance(x, tuple):
            x = [x]
            expected = [expected]
        for a, b in zip(x, expected):
            if isinstance(a, RV):
                assert a.vals == b.vals, f'expected vals {b.vals} got {a.vals}'
                assert a.probs == b.probs, f'expected probs {b.probs} got {a.probs}'
            else:
                assert a == b, f'expected {b} got {a}'
        i += 1
    pipeline(code, global_vars={'output': lambda x: check_res(x)})
