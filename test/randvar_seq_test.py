from typing import Iterable
import pytest

from src import randvar
from src.randvar import Seq, RV, roll


@pytest.fixture(autouse=True)
def settings_reset():
    randvar.settings_reset()


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


_operation_list_params = [
    (4, 4, 3, 3),
    (4, 4, 10, 10),
    ((4, ), 4, 10, 10),
    ((2, 2, ), 4, 10, 10),
    (4, 4, (10, ), 10),
    (4, 4, (2, 8, ), 10),
    ((4, ), 4, (10, ), 10),
    ((1, 3, ), 4, (10, ), 10),
    ((1, 3, ), 4, (5, 5, ), 10),
    ((1, 3, ), 4, (1, 4, 5, ), 10),
    ((1, 3, ), 4, (1, (2, 2), 5, ), 10),
    ((1, (1, 2), ), 4, (1, (2, (1, 1), 1), 4, ), 10),
    (4, 4, (1, (2, (1, 1), 1), 4, ), 10),
    ((1, (1, 2), ), 4, 10, 10),
]

@pytest.mark.parametrize("s1, t1, s2, t2", _operation_list_params)
def test_seq_arith_plus(s1, t1, s2, t2):
    if isinstance(s1, Iterable):
        s1 = Seq(*s1)
    if isinstance(s2, Iterable):
        s2 = Seq(*s2)
    assert s1 + s2 == t1 + t2, f'{s1} + {s2}'
    assert s2 + s1 == t2 + t1, f'{s2} + {s1}'

@pytest.mark.parametrize("s1, t1, s2, t2", _operation_list_params)
def test_seq_arith_minus(s1, t1, s2, t2):
    if isinstance(s1, Iterable):
        s1 = Seq(*s1)
    if isinstance(s2, Iterable):
        s2 = Seq(*s2)
    assert s1 - s2 == t1 - t2, f'{s1} - {s2}'
    assert s2 - s1 == t2 - t1, f'{s2} - {s1}'

@pytest.mark.parametrize("s1, t1, s2, t2", _operation_list_params)
def test_seq_arith_times(s1, t1, s2, t2):
    if isinstance(s1, Iterable):
        s1 = Seq(*s1)
    if isinstance(s2, Iterable):
        s2 = Seq(*s2)
    assert s1 * s2 == t1 * t2, f'{s1} * {s2}'
    assert s2 * s1 == t2 * t1, f'{s2} * {s1}'

@pytest.mark.parametrize("s1, t1, s2, t2", _operation_list_params)
def test_seq_arith_div(s1, t1, s2, t2):
    if isinstance(s1, Iterable):
        s1 = Seq(*s1)
    if isinstance(s2, Iterable):
        s2 = Seq(*s2)
    assert s1 / s2 == t1 / t2, f'{s1} / {s2}'
    assert s2 / s1 == t2 / t1, f'{s2} / {s1}'

@pytest.mark.parametrize("s1, t1, s2, t2", _operation_list_params)
def test_seq_arith_floordiv(s1, t1, s2, t2):
    if isinstance(s1, Iterable):
        s1 = Seq(*s1)
    if isinstance(s2, Iterable):
        s2 = Seq(*s2)
    assert s1 // s2 == t1 // t2, f'{s1} // {s2}'
    assert s2 // s1 == t2 // t1, f'{s2} // {s1}'

@pytest.mark.parametrize("s1, t1, s2, t2", _operation_list_params)
def test_seq_arith_pow(s1, t1, s2, t2):
    if isinstance(s1, Iterable):
        s1 = Seq(*s1)
    if isinstance(s2, Iterable):
        s2 = Seq(*s2)
    assert s1 ** s2 == t1 ** t2, f'{s1} ** {s2}'
    assert s2 ** s1 == t2 ** t1, f'{s2} ** {s1}'

@pytest.mark.parametrize("s1, t1, s2, t2", _operation_list_params)
def test_seq_arith_mod(s1, t1, s2, t2):
    if isinstance(s1, Iterable):
        s1 = Seq(*s1)
    if isinstance(s2, Iterable):
        s2 = Seq(*s2)
    assert s1 % s2 == t1 % t2, f'{s1} % {s2}'
    assert s2 % s1 == t2 % t1, f'{s2} % {s1}'



@pytest.mark.parametrize("l1, l2, b", [
    ((1, 2), (1, 2), True),
    ((1, ), (1, ), True),
    ((1, 1), (1, 1), True),
    ((1, 1), (1, 2), False),
    ((1, 1), (1, ), False),
    ((1, ), (1, 1), False),
])
def test_seq_comp_eq(l1, l2, b):
    bb = Seq(*l1) == Seq(*l2)
    assert bb == b, f'{l1} == {l2} should be {b}'

@pytest.mark.parametrize("l1, n, b", [
    ((roll(2, 3), 10), 1, False),
    ((roll(2, 3), 10), 2, True),
    ((roll(2, 3), 10), 6, True),
    ((roll(2, 3), 10), 7, False),
    ((roll(2, 3), 10), 9, False),
    ((roll(2, 3), 10), 10, True),
])
def test_seq_comp_eq(l1, n, b):
    bb = Seq(*l1) == n
    assert bb == b, f'{l1} == {n} should be {b}'



@pytest.mark.parametrize("l1, l2, b", [
    ((1, 2), (2, 1), True),
    ((1, ), (1, 1), True),
    ((1, 1), (1, 1, 1), True),
    ((1, 1), (1, 1), False),
    ((1, 1), (1, 2), True),
    ((1, 1), (1, ), True),
])
def test_seq_comp_ne(l1, l2, b):
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
def test_seq_comp_gt(l1, l2, b):
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
def test_seq_comp_ge(l1, l2, b):
    bb = Seq(*l1) >= Seq(*l2)
    assert bb == b, f'{l1} >= {l2}'

@pytest.mark.parametrize("l1, l2, b", [
    ((0, ), (1, 2), True),
    ((0, 1), (1, 2, 3), True),
    ((0, 0), (1, ), False),
    ((1, 2), (1, 2), False),
    ((1, 1), (1, 2, 3), False),
])
def test_seq_comp_lt(l1, l2, b):
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
def test_seq_comp_le(l1, l2, b):
    bb = Seq(*l1) <= Seq(*l2)
    assert bb == b, f'{l1} <= {l2}'

def test_create_RV_from_seq():
    assert RV.dices_are_equal(RV.from_seq(Seq(2, roll(2, 2))), RV((2, 3, 4), (2, 1, 1)))


def test_seq_and_rv_op():
    assert RV.dices_are_equal(Seq([1, 2, 5]) + roll(2, 6), RV(tuple(range(10, 21)), (1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1))), 'seq + roll'
    assert RV.dices_are_equal(Seq([1, 2, 5]) > roll(2, 6), RV((0, 1), (5, 7))), 'seq > roll'
    assert RV.dices_are_equal(roll(2, 6) < Seq([1, 2, 5]), RV((0, 1), (5, 7))), 'roll < seq'
