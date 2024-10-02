import pytest

from randvar import Seq, roll, anydice_casting


@anydice_casting()
def f(s:Seq):
    return s

def test_cast_die():
    a = roll(4)
    f(a)  # type: ignore

def test_cast_die_rolled_as_sequence():
    a = roll(Seq(1, 2), 2)
    f(a)  # type: ignore

def test_cast_die_rolled_as_die():
    a = roll(roll(2), 2)
    f(a)  # type: ignore
