import pytest

import randvar
from randvar import RV, Seq, anydice_casting, output, roll
from parser.parse_and_exec import pipeline


@pytest.mark.parametrize("code,res", [
('''
output ((1d4-1) | (1d2-1))
''', [RV((0, 1), (125, 875))]),
('''
output ((1d4-1) | (1d2-1))
''', [RV((0, 1), (125, 875))]),

])
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

