import pytest

from randvar import Seq


def test_at_num():
    assert Seq(2, 3) @ 1234 == 5


@pytest.mark.parametrize("l1, l2, i", [
    ((2, ), (1, 2, 3), 2),
    ((1, 2), (2, 3, 999, 999), 5),
    ((-1000, 2, 2, 1000), (2, 3, 4, 5), 6),
    ((1, 3), (2, 4, 6), 8),
    ((1, 2, 2), (2, 4, 6), 10), 
])
def test_seq_at_seq(l1, l2, i):
    assert Seq(*l1) @ Seq(*l2) == i

@pytest.mark.parametrize("n, l2, i", [
    (1, (2, 4, 6), 2),
    (3, (2, 4, 6), 6),
])
def test_num_at_seq(n, l2, i):
    assert n @ Seq(*l2) == i


@pytest.mark.parametrize("l1, l2, b", [
    ((1, 2), (1, 2), True),
    ((1, ), (1, ), True),
    ((1, 1), (1, 1), True),
    ((1, 1), (1, 2), False),
    ((1, 1), (1, ), False),
    ((1, ), (1, 1), False),
])
def test_seq_eq(l1, l2, b):
    bb = Seq(*l1) == Seq(*l2)
    assert bb == b, f'{l1} == {l2}'

@pytest.mark.parametrize("l1, l2, b", [
    ((1, 2), (2, 1), True),
    ((1, ), (1, 1), True),
    ((1, 1), (1, 1, 1), True),
    ((1, 1), (1, 1), False),
    ((1, 1), (1, 2), True),
    ((1, 1), (1, ), True),
])
def test_seq_ne(l1, l2, b):
    bb = Seq(*l1) != Seq(*l2)
    assert bb == b, f'{l1} != {l2}'

@pytest.mark.parametrize("l1, l2, b", [
    ((1, 2), (1, 2), False),
    ((1, 2), (1, 2, 3), False),
    ((1, 2), (1, 1), False),
    ((1, 2), (1, ), False),
    ((1, 2), (0, 1), True),
    ((2, 2), (1, ), True),
])
def test_seq_gt(l1, l2, b):
    bb = Seq(*l1) > Seq(*l2)
    assert bb == b, f'{l1} > {l2}'

@pytest.mark.parametrize("l1, l2, b", [
    ((1, 2), (1, 2), True),
    ((1, 2), (1, 2, 3), False),
    ((1, 2), (1, 1), True),
    ((1, 2), (1, ), True),
    ((1, 2), (0, 1), True),
    ((2, 2), (1, ), True),
    ((1, 3), (1, 2), True),
    ((2, 2), (1, ), True),
    ((1, ), (1, 2), False),
])
def test_seq_ge(l1, l2, b):
    bb = Seq(*l1) >= Seq(*l2)
    assert bb == b, f'{l1} >= {l2}'

@pytest.mark.parametrize("l1, l2, b", [
    ((0, ), (1, 2), True),
    ((0, 1), (1, 2, 3), True),
    ((0, 0), (1, ), False),
    ((1, 2), (1, 2), False),
    ((1, 1), (1, 2, 3), False),
])
def test_seq_lt(l1, l2, b):
    bb = Seq(*l1) < Seq(*l2)
    assert bb == b, f'{l1} < {l2}'

@pytest.mark.parametrize("l1, l2, b", [
    ((0, ), (1, 2), True),
    ((1, 2), (1, 2), True),
    ((1, 2, 3), (1, 2), False),
    ((0, 1), (1, 2, 3), True),
    ((0, 0), (1, ), False),
    ((1, 1), (1, 2, 3), True),
    ((1, 1), (1, 2), True),
    ((1, 1), (1, ), False),
    ((1, 2), (0, 1), False),
    ((2, 2), (1, ), False),
    ((1, 3), (1, 2), False),
    ((2, 2), (1, ), False),
    ((1, ), (1, 2), True),
])
def test_seq_le(l1, l2, b):
    bb = Seq(*l1) <= Seq(*l2)
    assert bb == b, f'{l1} <= {l2}'

