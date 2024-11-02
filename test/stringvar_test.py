from typing import Iterable
import pytest

from dice_calc import settings_reset, get_seq
from dice_calc.string_rvs import StringVal


@pytest.fixture(autouse=True)
def settings_reset_fixture():
  settings_reset()


def test_init():
  a = StringVal(('a', 'b'), {'a': 1, 'b': 2})
  b = StringVal(('a', 'b'), {'a': 1, 'b': 2})
  c = StringVal(('b', 'a'), {'b': 2, 'a': 1})
  d = StringVal(('a', 'b', 'c'), {'a': 1, 'b': 2, 'c': 3})
  assert a == b
  assert a == c
  assert b == c
  assert a != d
  assert b != d
  assert c != d


def test_format():
  a = StringVal(('a', 'b'), {'a': 1, 'b': 2})
  assert f'{a}' == 'a + 2*b'


def test_compare():
  a = StringVal(('a', 'b'), {'a': 1, 'b': 2})
  b = StringVal(('b', 'a'), {'b': 2, 'a': 1})
  c = StringVal(('b', 'a'), {'b': 1, 'a': 1})
  assert a == b
  assert a <= b
  assert a >= b
  assert not (a < b)
  assert not (a > b)
  assert not (a != b)

  assert a > c
  assert a >= c
  assert not (a < c)
  assert not (a <= c)
  assert not (a == c)
  assert a != c


def test_hash():
  a = StringVal(('a', 'b'), {'a': 1, 'b': 2})
  c = StringVal(('b', 'a'), {'b': 1, 'a': 1})
  d = StringVal(('a', 'b', 'c'), {'a': 1, 'b': 2, 'c': 3})
  assert hash(a) != hash(c)
  assert hash(a) != hash(d)
  assert hash(c) != hash(d)
  assert hash(a) == hash(a)
  assert hash(c) == hash(c)
  assert hash(d) == hash(d)


def test_get_seq():
  a = get_seq('a', 'b')
  b = get_seq('a', 'b')
  c = get_seq(1, 2)
  d = get_seq(1, 2)
  e = get_seq(1, 2, 'a', 'b')
  assert a == b
  assert c == d
  assert a != c
  assert a != e
  assert c != e
  assert isinstance(a, Iterable), 'get_seq must return an iterable'
  assert a == get_seq(a)
  assert e == get_seq(e)
