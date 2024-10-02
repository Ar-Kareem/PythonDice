import pytest

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
])
def test_RV_init_fail(vals, probs):
    with pytest.raises(Exception):
        RV(vals, probs)

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


def test_probability_zero_RV():
    a = RV((1, 2, 777), (1, 1, 0))
    b = roll(2)
    assert RV.dices_are_equal(a ,b) == True


