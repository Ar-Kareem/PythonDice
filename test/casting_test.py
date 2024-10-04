import pytest

import randvar
from randvar import RV, Seq, roll, anydice_casting

@anydice_casting()
def f1(inp:int):
    assert isinstance(inp, int)
    return inp
@anydice_casting()
def f2(inp:Seq):
    assert isinstance(inp, Seq)
    return inp
@anydice_casting()
def f3(inp:RV):
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
    def count(VALUES:Seq, SEQUENCE:Seq, *args):
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
    def cast(M:Seq):
        return M+1
    a = cast(roll(2, 2))  # type: ignore
    assert RV.dices_are_equal(a, roll(2, 2)+1), 'casting single dice to sequence'


def test_cast_dice_to_seq_then_roll():
    @anydice_casting()
    def p(SEQUENCE:Seq):
        return roll(3, SEQUENCE)
    assert RV.dices_are_equal(p(roll(2, 3)), RV(range(3, 10), (2, 1, 2, 2, 2, 1, 2))), 'return dice after casting'  # type: ignore

def test_cast_dice_to_seq():
    @anydice_casting()
    def p(SEQUENCE:Seq):
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
    def b(S:Seq):
        if S == 2:
            return 1
        return 999
    a = b(rv)
    assert (a.vals, a.probs) == (vals, probs)

def test_cast_then_matmul():
    @randvar.anydice_casting()
    def count(V, SEQUENCE:Seq, *args):
        return V@SEQUENCE
    assert RV.dices_are_equal(count(1, roll(2, 4)), RV((1, 2, 3, 4), (1, 3, 5, 7))), 'NUM @ DICED SEQ'  # type: ignore
    assert RV.dices_are_equal(1@roll(2, 4), RV((1, 2, 3, 4), (1, 3, 5, 7))), 'NUM @ DICED SEQ'

@pytest.mark.timeout(2)
def test_time():
    @randvar.anydice_casting()
    def a(n:int):
        return 0
    a(roll(100_000))  # type: ignore

def test_almost_zero():
    @anydice_casting()
    def a (N:int):
        if N == 1000:
            return 1
        return 2
    D: RV = a(roll(1000, 2))  # type: ignore
    assert (i>=1 for i in D.probs)

def test_cast_return_None():
    @anydice_casting()
    def f(A:int) -> int|None:
        if A > 2:
            return A
    assert RV.dices_are_equal( f(roll(2, 2)) , RV((3, 4), (2, 1)) )  # type: ignore
