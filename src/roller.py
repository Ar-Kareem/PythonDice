from typing import Union, Iterable
import random

from .randvar import RV
from .seq import Seq
from . import blackrv
from .typings import T_isr


def roll(n: Union[T_isr, str], d: Union[T_isr, None] = None) -> Union[RV, blackrv.BlankRV]:
  """Roll n dice of d sides

  Args:
      n (T_isr | str): number of dice to roll, if string then it must be 'ndm' where n and m are integers
      d (T_isr, optional): number of sides of the dice (or the dice itself). Defaults to None which is equivalent to roll(1, n)

  Returns:
      RV: RV of the result of rolling n dice of d sides
  """
  if isinstance(n, str):  # either rolL('ndm') or roll('dm')
    assert d is None, 'if n is a string, then d must be None'
    nm1, nm2 = n.split('d')
    if nm1 == '':
      nm1 = 1
    n, d = int(nm1), int(nm2)

  if d is None:  # if only one argument, then roll it as a dice once
    n, d = 1, n

  # make sure all iters are Seq
  if isinstance(d, Iterable) and not isinstance(d, Seq):
    d = Seq(*d)
  if isinstance(n, Iterable) and not isinstance(n, Seq):
    n = Seq(*n)
  if isinstance(d, blackrv.BlankRV):  # SPECIAL CASE: XdY where Y is BlankRV => BlankRV
    return blackrv.BlankRV()
  if isinstance(n, blackrv.BlankRV):  # SPECIAL CASE: XdY where X is BlankRV => Special BlankRV see https://anydice.com/program/395da
    return blackrv.BlankRV(_special_null=True)
  if isinstance(d, Seq) and len(d) == 0:  # SPECIAL CASE: Xd{} => BlankRV
    return blackrv.BlankRV()
  # both arguments are now exactly int|Seq|RV
  result = _roll(n, d)  # ROLL!
  assert not isinstance(result, blackrv.BlankRV), 'should never happen!'
  # below is only used for the __str__ method
  _LHS = n if isinstance(n, int) else (n.sum() if isinstance(n, Seq) else 0)
  if isinstance(d, int):
    _RHS = d
  elif isinstance(d, Seq):
    _RHS = '{}' if len(d) == 0 else '{?}'
  elif isinstance(d, RV):
    _d_LHS, _d_RHS = d._str_LHS_RHS
    _RHS = _d_RHS if _d_LHS == 1 and isinstance(_d_RHS, int) else '{?}'  # so that 2d(1d2) and (2 d (1 d ( {1} d 2))) all evaluate to '2d2'
  result._str_LHS_RHS = (_LHS, _RHS)
  return result


def _roll(n: Union[int, Seq, RV], d: Union[int, Seq, RV]) -> Union[RV, blackrv.BlankRV]:
  if isinstance(d, int):
    if d > 0:
      d = RV.from_seq(range(1, d + 1))
    elif d == 0:
      d = RV.from_const(0)
    else:
      d = RV.from_seq([range(d, 0)])
  elif isinstance(d, Seq):
    d = RV.from_seq(d)

  if isinstance(n, Seq):
    s = n.sum()
    assert isinstance(s, int), 'cant roll non-int number of dice'
    return roll(s, d)
  if isinstance(n, RV):
    assert all(isinstance(v, int) for v in n.vals), 'RV must have int values to roll other dice'
    dies = tuple(roll(int(v), d) for v in n.vals)
    result = RV.from_rvs(rvs=dies, weights=n.probs)
    assert not isinstance(result, blackrv.BlankRV), 'should never happen!'
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


def roller(rv: T_isr, count: Union[int, None] = None):
  if isinstance(rv, int) or isinstance(rv, Iterable) or isinstance(rv, bool):
    rv = RV.from_seq([rv])
  assert isinstance(rv, RV), 'rv must be a RV'
  # roll using random.choices
  if count is None:
    return random.choices(rv.vals, rv.probs)[0]
  return tuple(random.choices(rv.vals, rv.probs)[0] for _ in range(count))


def myrange(left, right):
    if isinstance(left, RV):
        raise TypeError(f'A sequence range must begin with a number, while you provided "{left}".')
    if isinstance(right, RV):
        raise TypeError(f'A sequence range must begin with a number, while you provided "{right}".')
    return range(left, right + 1)
