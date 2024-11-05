from typing import Union
import pytest

from dice_calc import anydice_casting, roll, RV, Seq, settings_reset, T_N, T_S, T_D


@pytest.fixture(autouse=True)
def settings_reset_fixture():
    settings_reset()




@anydice_casting()
def f1(inp: T_N):
    assert isinstance(inp, int)
    return inp
@anydice_casting()
def f2(inp: T_S):
    assert isinstance(inp, Seq)
    return inp
@anydice_casting()
def f3(inp: T_D):
    assert isinstance(inp, RV)
    return inp
@anydice_casting()
def f4(inp:list):
    assert isinstance(inp, list)
    return inp



def test_cast_die():
    a = roll(4)
    f2(a)  # type: ignore

def test_cast_die_rolled_as_sequence():
    a = roll(Seq(1, 2), 2)
    f2(a)  # type: ignore

def test_cast_die_rolled_as_die():
    a = roll(roll(2), 2)
    f2(a)  # type: ignore

def test_cast_iter_to_seq():
    r = f2([1])  # type: ignore
    r.sum()
    r = f4([1])  # type: ignore
    assert type(r) == list

# int parameter
@pytest.mark.parametrize("s1, s2", [
    (7, 7),
    (Seq(1, 4), 5),
    (roll(2, 2), RV((2, 3, 4), (1, 2, 1))),
])
def test_cast_to_int(s1, s2):
    if isinstance(s2, RV):
        assert RV.dices_are_equal(f1(s1), s2)
    else:
        assert f1(s1) == s2

@pytest.mark.parametrize("s1, s2", [
    (7, Seq(7)),
    (Seq(1, 4), Seq(1, 4)),
    (roll(2, 2), RV((2, 3, 4), (1, 2, 1))),
])
def test_cast_to_seq(s1, s2):
    if isinstance(s2, RV):
        assert RV.dices_are_equal(f2(s1), s2)
    elif isinstance(s2, Seq):
        assert Seq.seqs_are_equal(f2(s1), s2)

@pytest.mark.parametrize("s1, s2", [
    (7, RV((7, ), (1, ))),
    (Seq(1, 4), RV((1, 4), (1, 1))),
    (roll(2, 2), roll(2, 2)),
])
def test_cast_to_rv(s1, s2):
    assert RV.dices_are_equal(f3(s1), s2)

def test_cast_multiple_to_seq():
    @anydice_casting()
    def count(VALUES: T_S, SEQUENCE: T_S, *args):
        COUNT = 0
        for P in range(1, len(VALUES)+1):
            COUNT = COUNT + (P@VALUES == SEQUENCE)
        return COUNT

    a = count(VALUES=roll(3, 2), SEQUENCE=roll(2, 2))  # type: ignore
    b = count(roll(3, 2), SEQUENCE=roll(2, 2))  # type: ignore
    c = count(roll(3, 2), roll(2, 2), 1, 1, 1)  # type: ignore
    dd = RV(vals=(0, 2, 3, 4, 6), probs=(1, 3, 8, 3, 1))  # manual
    assert RV.dices_are_equal(a, b) and RV.dices_are_equal(b, c) and RV.dices_are_equal(c, dd), 'casting multiple dices to sequence'

def test2_cast_to_seq():
    @anydice_casting()
    def cast(M: T_S):
        return M+1
    a = cast(roll(2, 2))  # type: ignore
    assert RV.dices_are_equal(a, roll(2, 2)+1), 'casting single dice to sequence'


def test_cast_dice_to_seq_then_roll():
    @anydice_casting()
    def p(SEQUENCE: T_S):
        return roll(3, SEQUENCE)
    assert RV.dices_are_equal(p(roll(2, 3)), RV(range(3, 10), (2, 1, 2, 2, 2, 1, 2))), 'return dice after casting'  # type: ignore

def test_cast_dice_to_seq():
    @anydice_casting()
    def p(SEQUENCE: T_S):
        return SEQUENCE
    assert RV.dices_are_equal(p(Seq(1, 2, 2, 3)), RV((1, 2, 3), (1, 2, 1)))
    assert RV.dices_are_equal(p(roll(2, 2)), RV((2, 3, 4), (1, 2, 1)))  # type: ignore
    assert RV.dices_are_equal(p(roll(2)+roll(2)), RV((2, 3, 4), (1, 2, 1)))  # type: ignore


@pytest.mark.parametrize("rv, vals, probs", [
    (roll(5, 8),  (1, 999), (15961, 16807)), 
    (roll(8)+roll(8)+roll(8)+roll(8)+roll(8), (999, ), (1, ) ), 
    (roll(8), (1, 999), (1, 7) ), 
    (roll(2, 8), (1, 999), (15, 49) ), 
    (roll(8)+roll(8), (1, 999), (1, 63) ), 
])
def test_cast_dice_to_seq_more(rv, vals, probs):
    @anydice_casting()
    def b(S: T_S):
        if S == 2:
            return 1
        return 999
    a = b(rv)
    assert (a.vals, a.probs) == (vals, probs)  # type: ignore

def test_cast_then_matmul():
    @anydice_casting()
    def count(V, SEQUENCE: T_S, *args):
        return V@SEQUENCE
    assert RV.dices_are_equal(count(1, roll(2, 4)), RV((1, 2, 3, 4), (1, 3, 5, 7))), 'NUM @ DICED SEQ'  # type: ignore
    assert RV.dices_are_equal(1@roll(2, 4), RV((1, 2, 3, 4), (1, 3, 5, 7))), 'NUM @ DICED SEQ'

def test_almost_zero():
    @anydice_casting()
    def a (N: T_N):
        if N == 1000:
            return 1
        return 2
    D: RV = a(roll(1000, 2))  # type: ignore
    assert (i>=1 for i in D.probs)

def test_cast_return_None():
    @anydice_casting()
    def f(A: T_N) -> Union[int, None]:
        if A > 2:
            return A
    assert RV.dices_are_equal( f(roll(2, 2)) , RV((3, 4), (2, 1)) )  # type: ignore

@pytest.mark.run(order=-1)
@pytest.mark.timeout(2)
def test_time():
    @anydice_casting()
    def a(n: T_N):
        return 0
    a(roll(1_000))  # type: ignore

@pytest.mark.run(order=-1)
@pytest.mark.timeout(5)
def test_time_memoize():
    for _ in range(1000):  # ~240 second @ 3.6ghz without memoize | 0.5 second with memoize
        roll(100, 10)

@pytest.mark.run(order=-1)
def test_cast_server_error():
    def f(s: T_S):
        return Seq(1, 2)@s
    a: RV =  f(roll(13, RV.from_seq([1, 1, 1, 2, 2, 3, 10, 11, 12, 13, 14, 15, 16])))  # CAUSES SERVER ERROR ON website  # type: ignore
    assert a.vals == (2,3,4,5,6,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32)
    assert a.probs == (1594323,13817466,1212200069,3166919392,8666162766,6908733,3173828125,28298170368,28298170368,28298170368,28298170368,28298170368,28291261635,25124342243,55530146023,151638563245,424568633113,865055027200,1963811844073,3643285803885,7429836001303,12820063266387,23629358946363,37127984923120,59470493235141,75109736929955,79972595385853)
