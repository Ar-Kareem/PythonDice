from typing import Union, Iterable
import random
import math

from .typings import T_ifsr, MetaRV, MetaSeq
from . import factory
from .randvar import RV
from . import blackrv


def roll(n: Union[T_ifsr, str], d: Union[T_ifsr, str, None] = None) -> MetaRV:
  """Roll n dice of d sides

  Args:
      n (T_ifsr | str): number of dice to roll, if string then it must be 'ndm' where n and m are integers
      d (T_ifsr, optional): number of sides of the dice (or the dice itself). Defaults to None which is equivalent to roll(1, n)

  Returns:
      RV: RV of the result of rolling n dice of d sides
  """
  if isinstance(n, str):  # either rolL('ndm') or roll('dm')
    assert d is None, 'if n is a string, then d must be None'
    n, d = _parse_from_str(n)
  if isinstance(d, str):
    d = factory.get_seq([d])

  if d is None:  # if only one argument, then roll it as a dice once
    n, d = 1, n

  # handle floats
  if isinstance(n, float):
    n = math.ceil(n)
  if isinstance(d, float):
    d = factory.get_seq(d)
  # make sure all iters are Seq
  if isinstance(d, Iterable) and not isinstance(d, MetaSeq):
    d = factory.get_seq(*d)
  if isinstance(n, Iterable) and not isinstance(n, MetaSeq):
    n = factory.get_seq(*n)
  # handle special cases with BlankRV
  if isinstance(d, blackrv.BlankRV):  # SPECIAL CASE: XdY where Y is BlankRV => BlankRV
    return blackrv.BlankRV()
  if isinstance(n, blackrv.BlankRV):  # SPECIAL CASE: XdY where X is BlankRV => Special BlankRV see https://anydice.com/program/395da
    return blackrv.BlankRV(_special_null=True)
  if isinstance(d, MetaSeq) and len(d) == 0:  # SPECIAL CASE: Xd{} => BlankRV
    return blackrv.BlankRV()
  if isinstance(d, MetaRV):
    assert isinstance(d, RV), 'd must be a RV if its MetaRV'
  if isinstance(n, MetaRV):
    assert isinstance(n, RV), 'n must be a RV if its MetaRV'
  # both arguments are now exactly int|Seq|RV
  result = _roll(n, d)  # ROLL!
  result._str_LHS_RHS = _setup_str_LHS_RHS(n, d)  # only used for the __str__ method
  return result


def _roll(n: Union[int, MetaSeq, RV], d: Union[int, MetaSeq, RV]) -> MetaRV:
  if isinstance(d, int):
    if d > 0:
      d = RV.from_seq(range(1, d + 1))
    elif d == 0:
      d = RV.from_const(0)
    else:
      d = RV.from_seq([range(d, 0)])
  elif isinstance(d, MetaSeq):
    d = RV.from_seq(d)

  if isinstance(n, MetaSeq):
    s = n.sum()
    assert isinstance(s, int), 'cant roll non-int number of dice'
    return roll(s, d)
  if isinstance(n, RV):
    assert all(isinstance(v, int) for v in n.vals), 'RV must have int values to roll other dice'
    dies = tuple(roll(int(v), d) for v in n.vals)
    result = RV.from_rvs(rvs=dies, weights=n.probs)
    result.set_source(1, d)
    return result
  return _roll_int_rv(n, d)


_MEMOIZED_ROLLS = {}


def _roll_int_rv(n: int, d: RV) -> RV:
  if n < 0:
    return -_roll_int_rv(-n, d)
  if n == 0:
    return RV.from_const(0)
  if n == 1:
    return d
  if (n, d.vals, d.probs) in _MEMOIZED_ROLLS:
    return _MEMOIZED_ROLLS[(n, d.vals, d.probs)]
  half = _roll_int_rv(n // 2, d)
  full = half + half
  if n % 2 == 1:
    full = full + d
  full.set_source(n, d)
  _MEMOIZED_ROLLS[(n, d.vals, d.probs)] = full
  return full


def _parse_from_str(s: str):
    nm1, nm2 = s.split('d')
    if nm1 == '':
      nm1 = 1
    n, d = int(nm1), int(nm2)
    return n, d


def _setup_str_LHS_RHS(n, d):
  _LHS = n if isinstance(n, int) else (n.sum() if isinstance(n, MetaSeq) else 0)
  if isinstance(d, int):
    _RHS = d
  elif isinstance(d, MetaSeq):
    _RHS = '{}' if len(d) == 0 else '{?}'
  elif isinstance(d, MetaRV):
    _d_LHS, _d_RHS = d._str_LHS_RHS
    _RHS = _d_RHS if _d_LHS == 1 and isinstance(_d_RHS, int) else '{?}'  # so that 2d(1d2) and (2 d (1 d ( {1} d 2))) all evaluate to '2d2'
  return _LHS, _RHS


def roller(rv: T_ifsr, count: Union[int, None] = None):
  rv = factory.get_rv(rv)
  # roll using random.choices
  if count is None:
    return random.choices(rv.vals, rv.probs)[0]
  return tuple(random.choices(rv.vals, rv.probs)[0] for _ in range(count))


def myrange(left, right):
    if isinstance(left, MetaRV):
        raise TypeError(f'A sequence range must begin with a number, while you provided "{left}".')
    if isinstance(right, MetaRV):
        raise TypeError(f'A sequence range must begin with a number, while you provided "{right}".')
    return range(int(left), int(right) + 1)
