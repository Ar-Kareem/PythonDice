import pytest
import math

from randvar import RV, roll

@pytest.mark.parametrize("vals,probs", [
    ([], []),
    ((0, ), (1, )),
    ((1, ), (1, )),
    ((2, ), (1, )),
    ((1, 2), (1, 1)),
    ((1, 2, 3), (1, 1, 1)),
    ((1, 2, 3), (2, 2, 2)),
])
def test_RV_init(vals, probs):
    RV(vals, probs)

@pytest.mark.parametrize("vals,probs", [
    ([1], []),
    ([], [1]),
    ([1, 2], [1]),
    ([1], [1, 1]),
    ([1, 1, 1], [1, 1]),
    ([1, 1], [1, -1]),
    ([1, 1], [1, 1.1]),
])
def test_RV_init_fail(vals, probs):
    with pytest.raises(Exception):
        RV(vals, probs)

def test_probability_zero_RV():
    a = RV((1, 2, 777), (1, 1, 0))
    assert (a.vals, a.probs) == ((1, 2), (1, 1))

@pytest.mark.parametrize("v, p, gv, gp", [
    ((1, ), (1, ), (1, ), (1, )),
    ((1, 2, 3), (1, 1, 1), (1, 2, 3), (1, 1, 1)),
    ((2, 1, 3), (1, 1, 1), (1, 2, 3), (1, 1, 1)),
    ((1, 2, 3), (2, 2, 2), (1, 2, 3), (1, 1, 1)),
    ((1, 2, 3), (4, 4, 2), (1, 2, 3), (2, 2, 1)),
    ((1.1, 2.1, 3.1), (1, 1, 1), (1.1, 2.1, 3.1), (1, 1, 1)),
    ([], [], (0, ), (1, )),
    ((1, 1, 3), (1, 5, 1), (1, 3), (6, 1)),
    ((1, 1, 3, 3), (2, 6, 2, 4), (1, 3), (4, 3)),
    ((3, 3, 1, 1), (2, 6, 2, 4), (1, 3), (3, 4)),
    ((3, 1, 3, 1), (2, 6, 2, 4), (1, 3), (5, 2)),
    ((3, 1, 3, 1, 5), (2, 6, 2, 4, 0), (1, 3), (5, 2)),
    ((1, 1, 1, 1), (2, 6, 2, 4), (1, ), (1, )),
])
def test_RV_equality(v, p, gv, gp):
    a = RV(v, p)
    assert (a.vals, a.probs) == (gv, gp)

@pytest.mark.parametrize("n", [
    1, 2, 3, 4, 5, 6, 8, 20, 100, 200, 201
])
def test_RV_from_const(n):
    a = RV.from_const(n)
    assert (a.vals, a.probs) == ((n, ), (1, ))

# TODO test from_seq
# TODO test from_rvs

@pytest.mark.parametrize("v, p, sum_p", [
    ((1, ), (1, ), 1),
    ((1, 2, 3), (1, 1, 1), 3),
    ((2, 1, 3), (1, 1, 1), 3),
    ((1, 2, 3), (2, 2, 2), 3),
    ((1, 2, 3), (4, 4, 2), 5),
    ((1.1, 2.1, 3.1), (1, 1, 1), 3),
    ([], [], 1),
    ((1, 1, 3), (1, 5, 1), 7),
    ((1, 1, 3, 3), (2, 6, 2, 4), 7),
    ((3, 3, 1, 1), (2, 6, 2, 4), 7),
    ((3, 1, 3, 1), (2, 6, 2, 4), 7),
    ((3, 1, 3, 1, 5), (2, 6, 2, 4, 0), 7),
    ((1, 1, 1, 1), (2, 6, 2, 4), 1),
])
def test_RV_sum_probs(v, p, sum_p):
    a = RV(v, p)
    assert a._get_sum_probs() == sum_p

@pytest.mark.parametrize("v, p, mean", [
    ((1, ), (1, ), 1),
    ((1, 2, 3), (1, 1, 1), 2),
    ((2, 1, 3), (1, 1, 1), 2),
    ((1, 2, 3), (2, 2, 2), 2),
    ((1, 2, 3), (4, 4, 2), 9/5),
    ((1.1, 2.1, 3.1), (1, 1, 1), 2.1),
    ([], [], 0),
    ((1, 1, 3), (1, 5, 1), 9/7),
    ((1, 1, 3, 3), (2, 6, 2, 4), 13/7),
    ((3, 3, 1, 1), (2, 6, 2, 4), 15/7),
    ((3, 1, 3, 1), (2, 6, 2, 4), 11/7),
    ((3, 1, 3, 1, 5), (2, 6, 2, 4, 0), 11/7),
    ((1, 1, 1, 1), (2, 6, 2, 4), 1),
])
def test_RV_mean(v, p, mean):
    a = RV(v, p)
    assert a.mean() == mean

@pytest.mark.parametrize("v, p, std", [
    ((1, ), (1, ), 0),
    ((1, 2, 3), (1, 1, 1), math.sqrt(2/3)),
    ((2, 1, 3), (1, 1, 1), math.sqrt(2/3)),
    ((1, 2, 3), (2, 2, 2), math.sqrt(2/3)),
    ((1, 2, 3), (4, 4, 2), math.sqrt(0.56)),
    ((1.1, 2.1, 3.1), (1, 1, 1), math.sqrt(2/3)),
    ([], [], 0),
    ((1, 1, 3), (1, 5, 1), math.sqrt(24/49)),
    ((1, 1, 3, 3), (2, 6, 2, 4), math.sqrt(48/49)),
    ((3, 3, 1, 1), (2, 6, 2, 4), math.sqrt(48/49)),
    ((3, 1, 3, 1), (2, 6, 2, 4), math.sqrt(40/49)),
    ((3, 1, 3, 1, 5), (2, 6, 2, 4, 0), math.sqrt(40/49)),
    ((1, 1, 1, 1), (2, 6, 2, 4), 0),
])
def test_RV_std(v, p, std):
    a = RV(v, p)
    assert abs(a.std() - std) < 1e-10, a.std()**2  # type: ignore




@pytest.mark.parametrize("n", [
    1, 2, 3, 4, 5, 6, 8, 20, 100, 200, 201
])
def test_roll1(n):
    r = roll(n)
    assert len(r.probs) == n
    assert len(r.vals) == n
    assert r.probs == tuple([1] * n)
    assert r.vals == tuple(range(1, n + 1))

@pytest.mark.parametrize("n", [
    1, 2, 3, 4, 5, 6, 8, 20, 100, 200, 201
])
def test_roll1_negative(n):
    r = roll(-n)
    assert len(r.probs) == n
    assert len(r.vals) == n
    assert r.probs == tuple([1] * n)
    assert r.vals == tuple(range(-n, 0))

def test_roll1_zero():
    r = roll(0)
    assert r.probs == (1, )
    assert r.vals == (0, )

def test_dices_are_equal_DD():
    d1 = roll(6)
    d2 = roll(6)
    dnot = roll(7)
    assert RV.dices_are_equal(d1, d2)
    assert not RV.dices_are_equal(d1, dnot)
    assert not RV.dices_are_equal(d2, dnot)

# def test_RV_operations():
#     r = roll(6)
#     assert False




