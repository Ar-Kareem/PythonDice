import pytest
import math

import randvar
from randvar import RV, Seq, roll, output

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

def test_RV_init_empty():
    a = RV((), ())
    b = RV([], [])
    c = RV.from_seq(Seq())
    d = RV.from_rvs(rvs=[])
    e = RV.from_rvs(rvs=[RV([], [])])
    assert (a.vals, a.probs) == ((0, ), (1, ))
    assert (b.vals, b.probs) == ((0, ), (1, ))
    assert (c.vals, c.probs) == ((0, ), (1, ))
    assert (d.vals, d.probs) == ((0, ), (1, ))
    assert (e.vals, e.probs) == ((0, ), (1, ))

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
    assert RV.dices_are_equal(a, RV(gv, gp))

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

@pytest.mark.parametrize("rv, mean, std", [
    (roll(6)+roll(5), 6.5, 2.22),
])
def test_RV_mean_fail(rv, mean, std):
    assert rv.mean() == mean
    assert round(rv.std(), 2) == std

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

@pytest.mark.parametrize("v, p, cdf_probs", [
    ((1, ), (1, ), (1, )),
    ((1, 2, 3), (1, 1, 1), (1, 2, 3)),
    ((2, 1, 3), (1, 1, 1), (1, 2, 3)),
    ((1, 2, 3), (2, 2, 2), (1, 2, 3)),
    ((1, 2, 3), (4, 4, 2), (2, 4, 5)),
    ((1.1, 2.1, 3.1), (1, 1, 1), (1, 2, 3)),
    ([], [], (1, )),
    ((1, 1, 3), (1, 5, 1), (6, 7)),
    ((1, 1, 3, 3), (2, 6, 2, 4), (4, 7)),
    ((3, 3, 1, 1), (2, 6, 2, 4), (3, 7)),
    ((3, 1, 3, 1), (2, 6, 2, 4), (5, 7)),
    ((3, 1, 3, 1, 5), (2, 6, 2, 4, 0), (5, 7)),
    ((1, 1, 1, 1), (2, 6, 2, 4), (1, )),
])
def test_RV_CDF(v, p, cdf_probs):
    a = RV(v, p)
    b = a.get_cdf()
    assert (b.vals, b.probs) == (a.vals, cdf_probs)

@pytest.mark.parametrize("cdf_cut, rv, rv_res", [
    (0,     RV((1, 2, 3), (1, 9, 90)),            ((1, .01), (2, .09), (3, .9),  )), 
    (0.05,  RV((1, 2, 3), (1, 9, 90)),            (          (2, .09), (3, .9),  )),
    (0.05,  RV((1, 2, 3), (9, 1, 90)),            ((1, .09),           (3, .9),  )),
    (0.05,  RV((1, 2, 3), (90, 1, 9)),            ((1, .9),            (3, .09), )),
    (0.095, RV((1, 2, 3), (90, 1, 9)),            ((1, .9),            (3, .09), )),
    (0.099, RV((1, 2, 3), (90, 1, 9)),            ((1, .9),            (3, .09), )),
    (0.1,   RV((1, 2, 3), (90, 1, 9)),            ((1, .9),                      )),
    (0.15,  RV((1, 2, 3), (1, 9, 90)),            (                    (3, .9),  )),
    (0.999, RV((1, 2, 3), (1, 9, 90)),            (                    (3, .9),  )),

    (0,     RV((1, 2, 3), (1, 90, 9)),            ((1, .01), (2, .9), (3, .09),  )), 
    (0.005, RV((1, 2, 3), (1, 90, 9)),            ((1, .01), (2, .9), (3, .09),  )), 
    (0.01,  RV((1, 2, 3), (1, 90, 9)),            ((1, .01), (2, .9), (3, .09),  )), 
    (0.0101,RV((1, 2, 3), (1, 90, 9)),            (          (2, .9), (3, .09),  )), 
    (0.011, RV((1, 2, 3), (1, 90, 9)),            (          (2, .9), (3, .09),  )), 
    (0.095, RV((1, 2, 3), (1, 90, 9)),            (          (2, .9), (3, .09),  )), 
    (0.1,   RV((1, 2, 3), (1, 90, 9)),            (          (2, .9),           )), 
    (0.5,   RV((1, 2, 3), (1, 90, 9)),            (          (2, .9),           )), 
    (0.999, RV((1, 2, 3), (1, 90, 9)),            (          (2, .9),           )), 
])
def test_RV_pdf(cdf_cut, rv: RV, rv_res):
    vp = rv.get_vals_probs(cdf_cut)
    assert vp == rv_res, f'{vp} != {rv_res} | {cdf_cut}'


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

@pytest.mark.parametrize("n, m, res", [
    (2, 2, roll(2)+roll(2)), 
    (1, 2, roll(2)), 
    (1, 3, roll(3)), 
    (3, 4, roll(4)+roll(4)+roll(4)), 
    (2, 4, RV((2, 3, 4, 5, 6, 7, 8), (1, 2, 3, 4, 3, 2, 1))), 
])
def test_roll_int_int(n, m, res):
    assert RV.dices_are_equal(roll(n, m), res)


@pytest.mark.parametrize("roll, res", [
    (roll(Seq(2, Seq(3, 2, roll(3)))),          RV((1, 2, 3), (1, 3, 2))), 
    (roll(2, roll(2, 2)),                       RV((4, 5, 6, 7, 8), (1, 4, 6, 4, 1))), 
    (roll(2, Seq(roll(2, 2))),                  RV((4, 5, 6, 7, 8), (1, 2, 3, 2, 1))), 
    (Seq(roll(2, 2), roll(2, 4)),               RV(range(2, 9), (2, 2, 2, 1, 1, 1, 1))), 

    # N d [N|SEQ|DIE]
    (roll(2, 3),                      RV((2, 3, 4, 5, 6), (1, 2, 3, 2, 1))), 
    (roll(2, Seq(1, 5, 5)),           RV((2, 6, 10), (1, 4, 4))), 
    (roll(2, roll(3, 4)),             RV(range(6, 25), (1, 6, 21, 56, 120, 216, 336, 456, 546, 580, 546, 456, 336, 216, 120, 56, 21, 6, 1))), 
    # SEQ d [N|SEQ|DIE]
    (roll(Seq(1, 2), 3),              roll(1, 3)+roll(2, 3)), 
    (roll(Seq(1, 2), Seq(2, 3)),      RV((6, 7, 8, 9), (1, 3, 3, 1))), 
    (roll(Seq(1, 2), roll(2, 2)),     RV((6, 7, 8, 9, 10, 11, 12), (1, 6, 15, 20, 15, 6, 1))), 
    # DIE d [N|SEQ|DIE]
    (roll(roll(2, 2), 2),             RV((2, 3, 4, 5, 6, 7, 8), (4, 12, 17, 16, 10, 4, 1))), 
    (roll(roll(2, 2), Seq(5, 7)),     RV((10, 12, 14, 15, 17, 19, 20, 21, 22, 24, 26, 28), (4, 8, 4, 4, 12, 12, 1, 4, 4, 6, 4, 1))), 
    (roll(roll(2), roll(2)),          RV((1, 2, 3, 4), (2, 3, 2, 1))), 
    (roll(roll(2, 2), roll(2)),       RV((2, 3, 4, 5, 6, 7, 8), (4, 12, 17, 16, 10, 4, 1))), 
    (roll(roll(2, 2), roll(2, 2)),    RV(range(4, 17), (16, 64, 104, 112, 137, 168, 148, 104, 78, 56, 28, 8, 1))), 
])
def test_roll_seq_rv(roll, res):
    assert RV.dices_are_equal(roll, res), f'{roll}'


@pytest.mark.parametrize("a, b", [
    (roll(2, -3),   RV((-6, -5, -4, -3, -2), (1, 2, 3, 2, 1))),
    (roll(-2, 6),   -roll(2, 6)),
    (roll(2, -6),   -roll(2, 6)),
    (roll(-2, -6),  roll(2, 6)),
    (roll(0, 6),    RV.from_const(0)),
    (roll(2, 0),    RV.from_const(0)),
    (roll(0, 0),    RV.from_const(0)),
])
def test_roll2_negative(a, b):
    assert RV.dices_are_equal(a, b)


@pytest.mark.parametrize("d, r", [
    (roll(6), 1),
    (roll(2, 6), 2),
    (roll(3, 6), 3),

    (roll(4, 6), 4),
    (roll(1, roll(4, 6)), 4),
    (roll(1, roll(2, roll(4, 6))), 2),

    (roll(roll(2 ,4), 6), 1),
    (roll(roll(2 ,4), roll(4, 6)), 1),
    (roll(roll(2 ,4), roll(2, roll(4, 6))), 1),

    (roll(1, Seq(2, 3, 3)), 1),
    (roll(Seq(2, 3, 3)), 1),
    (roll(Seq(2), Seq(2, 3, 3)), 2),
    (roll(Seq(2, 3), Seq(2, 3, 3)), 5),

    (roll(2, 2), 2),
    (roll(2)+roll(2), 1),
    (roll(1, roll(2, 2)), 2),
    (roll(1, roll(2)+roll(2)), 1),
])
def test_dice_len(d, r):
    assert len(d) == r

def test_roll_1_not_change_len():
    a = roll(3, 4)
    assert len(a) == 3
    a = roll(2, a)
    assert len(a) == 2
    a = roll(1, a)
    assert len(a) == 2, 'rolling once should not change the length'

def test_output():
    b = roll(2, 6)
    assert b.output(cdf_cut=10, print_=False) == output(b, cdf_cut=10, print_=False)
    assert b.output(cdf_cut=10, print_=False) != output(b, print_=False)

# TODO test comparison operators
# TODO test arithmetic operators


@pytest.mark.parametrize("l, r, l_at_r", [
    (1,         roll(2, 4),   RV((1, 2, 3, 4), (1, 3, 5, 7))),   # NUM @ DIE
    (1,         roll(2, 2),   RV((1, 2), (1, 3))),   # NUM @ DIE
    (1,    roll(2)+roll(2),   RV((2, 3, 4), (1, 2, 1))),   # NUM @ (DIE+DIE)
    (2,    roll(2)+roll(2),   RV((0, ), (1, ))),   # NUM @ (DIE+DIE)
    (Seq(1, 2), roll(2, 4),   RV((2, 3, 4, 5, 6, 7, 8), (1, 2, 3, 4, 3, 2, 1))),   # SEQ @ DIE
    (Seq(1,2),  roll(3, 6),   RV((2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), (1, 3, 7, 12, 19, 27, 34, 36, 34, 27, 16))),   # SEQ @ DIE [in docs]
    (3,         roll(2, 4),   RV((0, ), (1, ))),   # NUM @ DIE OOB
    (1,         roll(3, 6),   RV((1, 2, 3, 4, 5, 6), (1, 7, 19, 37, 61, 91))),   # NUM @ DIE [in docs]
    (3,         roll(3, 6),   RV((1, 2, 3, 4, 5, 6), (91, 61, 37, 19, 7, 1))),   # NUM @ DIE [in docs]
    (0,         roll(6),      RV((0, ), (1, ))),   # NUM @ DIE OOB
    (1,         roll(6),      roll(6)),   # NUM @ DIE single dice
    (2,         roll(6),      RV((0, ), (1, ))),   # NUM @ DIE OOB
])
def test_matmul(l, r, l_at_r):
    assert RV.dices_are_equal(l @ r, l_at_r), f'{l} @ {r} ! = {l_at_r}'

@pytest.mark.parametrize("rhs", [
    1, Seq(1, 2), roll(2, 2)
])
def test_FAIL_die_matmul(rhs):
    with pytest.raises(Exception):
        roll(2, 4) @ rhs


def test_truncate():
    a = roll(6) / roll(6)
    b = RV(a.vals, a.probs, truncate=False)
    c = RV(a.vals, a.probs, truncate=True)
    randvar.RV_AUTO_TRUNC = True
    d = roll(6) / roll(6)
    assert RV.dices_are_equal(a, b)
    assert RV.dices_are_equal(c, d)
    assert not RV.dices_are_equal(a, c)
    assert not RV.dices_are_equal(a, d)
    assert not RV.dices_are_equal(b, c)
    assert not RV.dices_are_equal(b, d)
    randvar.RV_AUTO_TRUNC = False

def test_fast_matmul():
    r = (2@roll(4, (roll(4) + roll(3, 8) + roll(12)))).get_vals_probs(cdf_cut=0.5)  # type: ignore
    assert '|'.join(f'{v}:{p:.4f}' for v, p in r) == '22:0.0976|23:0.1124|24:0.1186|25:0.1148|26:0.1019'