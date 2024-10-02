import pytest

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
    else:
        assert f2(s1) == s2

@pytest.mark.parametrize("s1, s2", [
    (7, RV((7, ), (1, ))),
    (Seq(1, 4), RV((1, 4), (1, 1))),
    (roll(2, 2), roll(2, 2)),
])
def test_cast_to_rv(s1, s2):
    assert RV.dices_are_equal(f3(s1), s2)
