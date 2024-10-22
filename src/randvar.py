# from __future__ import annotations

import operator
import math
from typing import Callable, Iterable, Union
from itertools import zip_longest, product, combinations_with_replacement, accumulate
import inspect
from collections import defaultdict
import logging
import random

from . import utils


logger = logging.getLogger(__name__)


# TYPE DEFINITIONS
T_if = Union[int, float]
T_ifs = Union[T_if, Iterable['T_ifs']]  # recursive type
T_is = Union[int, Iterable['T_is']]  # recursive type

T_isr = Union[T_is, 'RV', 'BlankRV']
T_ifr = Union[T_if, 'RV', 'BlankRV']
T_ifsr = Union[T_ifs, 'RV', 'BlankRV']

T_s = Iterable['T_ifs']  # same as T_ifs but excludes int and float (not iterable)


# SETTINGS
DEFAULT_SETTINGS = {
  'RV_TRUNC': False,  # if True, then RV will automatically truncate values to ints (replicate anydice behavior)
  'RV_IGNORE_ZERO_PROBS': False,  # if True, then RV remove P=0 vals when creating RVs (False by default in anydice)
  'DEFAULT_OUTPUT_WIDTH': 180,  # default width of output
  'DEFAULT_PRINT_FN': print,  # default print function
  'INTERNAL_CURR_DEPTH': 0,  # internal use only, for max_func_depth decorator
  'INTERNAL_CURR_DEPTH_WARNING_PRINTED': False,  # used with the above

  'position order': 'highest first',  # 'highest first' or 'lowest first'
  'explode depth': 2,  # can only be set to a positive integer (the default is 2)
  'maximum function depth': 10  # can only be set to a positive integer (the default is 10)
}
SETTINGS = DEFAULT_SETTINGS.copy()


def settings_set(name, value):
  if name == "position order":
    assert value in ("highest first", "lowest first"), 'position order must be "highest first" or "lowest first"'
  elif name == "explode depth":
    assert isinstance(value, int) and value > 0, '"explode depth" can only be set to a positive integer (the default is 2) got ' + str(value)
  elif name == "maximum function depth":
    assert isinstance(value, int) and value > 0, '"maximum function depth" can only be set to a positive integer (the default is 10) got ' + str(value)
  elif name in ('RV_TRUNC', 'RV_IGNORE_ZERO_PROBS'):
    if isinstance(value, str):
      assert value.lower() in ('true', 'false'), 'value must be "True" or "False"'
      value = value.lower() == 'true'
    assert isinstance(value, bool), 'value must be a boolean'
  elif name == 'DEFAULT_OUTPUT_WIDTH':
    assert isinstance(value, int) and value > 0, 'DEFAULT_OUTPUT_WIDTH must be a positive integer'
  elif name == 'DEFAULT_PRINT_FN':
    assert callable(value), 'DEFAULT_PRINT_FN must be a callable'
  else:
    assert False, f'invalid setting name: {name}'
  SETTINGS[name] = value


def settings_reset():
  SETTINGS.clear()
  SETTINGS.update(DEFAULT_SETTINGS)


class RV:
  def __init__(self, vals: Iterable[float], probs: Iterable[int], truncate=None):
    vals, probs = list(vals), tuple(probs)
    assert len(vals) == len(probs), 'vals and probs must be the same length'
    for i, v in enumerate(vals):  # convert elems in vals bool to int
      if isinstance(v, bool):
        vals[i] = int(v)

    if truncate or (truncate is None and SETTINGS['RV_TRUNC']):
      vals = tuple(int(v) for v in vals)
    self.vals, self.probs = RV._sort_and_group(vals, probs, skip_zero_probs=SETTINGS['RV_IGNORE_ZERO_PROBS'], normalize=True)
    if len(self.vals) == 0:  # if no values, then add 0
      self.vals, self.probs = (0, ), (1, )
    self.sum_probs = None
    # by default, 1 roll of current RV
    self._source_roll = 1
    self._source_die = self

    self._str_LHS_RHS: tuple[T_if, Union[T_if, str]] = (1, '{?}')  # used for __str__

  @staticmethod
  def _sort_and_group(vals: Iterable[float], probs: Iterable[int], skip_zero_probs, normalize):
    assert all(isinstance(p, int) and p >= 0 for p in probs), 'probs must be non-negative integers'
    zipped = sorted(zip(vals, probs), reverse=True)
    newzipped: list[tuple[float, int]] = []
    for i in range(len(zipped) - 1, -1, -1):
      if skip_zero_probs and zipped[i][1] == 0:
        continue
      if i > 0 and zipped[i][0] == zipped[i - 1][0]:  # add the two probs, go to next
        zipped[i - 1] = (zipped[i - 1][0], zipped[i - 1][1] + zipped[i][1])
      else:
        newzipped.append(zipped[i])
    vals = tuple(v[0] for v in newzipped)
    probs = tuple(v[1] for v in newzipped)
    if normalize:
      gcd = math.gcd(*probs)
      if gcd > 1:  # simplify probs
        probs = tuple(p // gcd for p in probs)
    return vals, probs

  @staticmethod
  def from_const(val: T_if):
    return RV([val], [1])

  @staticmethod
  def from_seq(s: T_s):
    if not isinstance(s, Seq):
      s = Seq(*s)
    if len(s) == 0:
      return RV([0], [1])
    return RV(s._seq, [1] * len(s))

  @staticmethod
  def from_rvs(rvs: Iterable[Union['int', 'float', 'Seq', 'RV', 'BlankRV', None]], weights: Union[Iterable[int], None] = None) -> Union['RV', 'BlankRV']:
    rvs = tuple(rvs)
    if weights is None:
      weights = [1] * len(rvs)
    weights = tuple(weights)
    blank_inds = set(i for i, x in enumerate(rvs) if isinstance(x, BlankRV) or x is None)
    rvs = tuple(x for i, x in enumerate(rvs) if i not in blank_inds)
    weights = tuple(w for i, w in enumerate(weights) if i not in blank_inds)
    if len(rvs) == 0:
      return BlankRV()
    assert len(rvs) == len(weights)
    prob_sums = tuple(sum(r.probs) if isinstance(r, RV) else 1 for r in rvs)
    PROD = math.prod(prob_sums)  # to normalize probabilities such that the probabilities for each individual RV sum to const (PROD) and every probability is an int
    res_vals, res_probs = [], []
    for weight, prob_sum, rv in zip(weights, prob_sums, rvs):
      if isinstance(rv, RV):
        res_vals.extend(rv.vals)
        res_probs.extend(p * weight * (PROD // prob_sum) for p in rv.probs)
      else:
        res_vals.append(rv)
        res_probs.append(weight * PROD)  # prob_sum is 1
    result = RV(res_vals, res_probs)
    result = _INTERNAL_PROB_LIMIT_VALS(result)
    return result

  def set_source(self, roll: int, die: 'RV'):
    self._source_roll = roll
    self._source_die = die

  def mean(self):
    if self._get_sum_probs() == 0:
      return None
    return sum(v * p for v, p in zip(self.vals, self.probs)) / self._get_sum_probs()

  def std(self):
    if self._get_sum_probs() == 0:  # if no probabilities, then std does not exist
      return None
    EX2 = (self**2).mean()
    EX = self.mean()
    assert EX2 is not None and EX is not None, 'mean must be defined to calculate std'
    var = EX2 - EX**2  # E[X^2] - E[X]^2
    return math.sqrt(var) if var >= 0 else 0

  def filter(self, seq: T_ifsr):
    to_filter = set(Seq(seq))
    vp = tuple((v, p) for v, p in zip(self.vals, self.probs) if v not in to_filter)
    if len(vp) == 0:
        return RV.from_const(0)
    vals, probs = zip(*vp)
    return RV(vals, probs)

  def get_vals_probs(self, cdf_cut: float = 0):
    '''Get the values and their probabilities, if cdf_cut is given, then remove the maximum bottom n values that sum to less than cdf_cut'''
    assert 0 <= cdf_cut < 1, 'cdf_cut must be in [0, 1)'
    s = self._get_sum_probs()
    vals_probs = tuple((v, p / s) for v, p in zip(self.vals, self.probs))
    if cdf_cut > 0:  # cut the bottom vals/probs and when stop total cut probs is less than cdf_cut
      sorted_vals_probs = sorted(vals_probs, key=lambda x: x[1])
      accumelated_probs = tuple(accumulate(sorted_vals_probs, lambda x, y: (y[0], x[1] + y[1]), initial=(0, 0)))
      vals_to_cut = set(v for v, p in accumelated_probs if p < cdf_cut)
      vals_probs = tuple((v, p) for v, p in vals_probs if v not in vals_to_cut)
    return vals_probs

  def get_cdf(self):
    '''Get CDF as RV where CDF(x) = P(X <= x)'''
    cdf_vals = self.vals
    cdf_probs = accumulate(self.probs)
    return RV(cdf_vals, cdf_probs)

  def output(self, *args, **kwargs):
    return output(self, *args, **kwargs)

  def _get_sum_probs(self, force=False):
    if self.sum_probs is None or force:
      self.sum_probs = sum(self.probs)
    return self.sum_probs

  def _get_expanded_possible_rolls(self):
    N, D = self._source_roll, self._source_die  # N rolls of D
    if N == 1:  # answer is simple (ALSO cannot use simplified formula for probs and bottom code WILL cause errors)
      return tuple(Seq(i) for i in D.vals), D.probs
    pdf_dict = {v: p for v, p in zip(D.vals, D.probs)}
    vals, probs = [], []
    FACTORIAL_N = utils.factorial(N)
    for roll in combinations_with_replacement(D.vals[::-1], N):
      vals.append(Seq(_INTERNAL_SEQ_VALUE=roll))
      counts = defaultdict(int)  # fast counts
      cur_roll_probs = 1  # this is p(x_1)*...*p(x_n) where [x_1,...,x_n] is the current roll, if D is a uniform then this = 1 and is not needed.
      comb_with_repl_denominator = 1
      for v in roll:
        cur_roll_probs *= pdf_dict[v]
        counts[v] += 1
        comb_with_repl_denominator *= counts[v]
      cur_roll_combination_count = FACTORIAL_N // comb_with_repl_denominator
      # UNOPTIMIZED:
      # counts = {v: roll.count(v) for v in set(roll)}
      # cur_roll_combination_count = FACTORIAL_N // math.prod(utils.factorial(c) for c in counts.values())
      # cur_roll_probs = math.prod(pdf_dict[v]**c for v, c in counts.items())  # if D is a uniform then this = 1 and is not needed.
      probs.append(cur_roll_combination_count * cur_roll_probs)
    return vals, probs

  def _apply_operation(self, operation: Callable[[float], float]):
    return RV([operation(v) for v in self.vals], self.probs)

  def _convolve(self, other: T_ifsr, operation: Callable[[float, float], float]):
    if isinstance(other, BlankRV):  # let BlankRV handle the operation
      return NotImplemented
    if isinstance(other, Iterable):
      if not isinstance(other, Seq):
        other = Seq(*other)
      other = other.sum()
    if not isinstance(other, RV):
      return RV([operation(v, other) for v in self.vals], self.probs)
    new_vals = tuple(operation(v1, v2) for v1 in self.vals for v2 in other.vals)
    new_probs = tuple(p1 * p2 for p1 in self.probs for p2 in other.probs)
    res = RV(new_vals, new_probs)
    res = _INTERNAL_PROB_LIMIT_VALS(res)
    return res

  def _rconvolve(self, other: T_ifsr, operation: Callable[[float, float], float]):
    if isinstance(other, BlankRV):  # let BlankRV handle the operation
      return NotImplemented
    assert not isinstance(other, RV)
    if isinstance(other, Iterable):
      if not isinstance(other, Seq):
        other = Seq(*other)
      other = other.sum()
    return RV([operation(other, v) for v in self.vals], self.probs)

  def __matmul__(self, other: T_ifs):
    # ( self:RV @ other ) thus not allowed,
    raise TypeError(f'A position selector must be either a number or a sequence, but you provided "{other}"')

  def __rmatmul__(self, other: T_is):
    # ( other @ self:RV )
    # DOCUMENTATION: https://anydice.com/docs/introspection/  look for "Accessing" -> "Collections of dice" and "A single die"
    assert not isinstance(other, RV), 'unsupported operand type(s) for @: RV and RV'
    other = Seq([other])
    assert all(isinstance(i, int) for i in other._seq), 'indices must be integers'
    if len(other) == 1:  # only one index, return the value at that index
      k: int = other._seq[0]  # type: ignore
      return self._source_die._get_kth_order_statistic(self._source_roll, k)
    return _sum_at(self, other)  # type: ignore

  def _get_kth_order_statistic(self, draws: int, k: int):
    '''Get the k-th smallest value of n draws: k@RV where RV is n rolls of a die'''
    # k-th largest value of n draws: γ@RV where RV is n rolls of a die | FOR DISCRETE (what we need): https://en.wikipedia.org/wiki/Order_statistic#Dealing_with_discrete_variables
    cdf = self.get_cdf().probs  # P(X <= x)
    sum_probs = self._get_sum_probs()
    p1 = tuple(cdf_x - p_x for p_x, cdf_x in zip(self.probs, cdf))  # P(X < x)
    p2 = self.probs  # P(X = x)
    p3 = tuple(sum_probs - cdf_x for cdf_x in cdf)  # P(X > x)

    N = draws
    if SETTINGS["position order"] == "highest first":
      k = N - k + 1  # wikipedia uses (k)-th smallest, we want (k)-th largest
    if k < 1 or k > N:
      return 0

    def get_x(xi, k):
      return sum(math.comb(N, j) * (p3[xi]**j * (p1[xi] + p2[xi])**(N - j) - (p2[xi] + p3[xi])**j * p1[xi]**(N - j)) for j in range(N - k + 1))
    res_prob = [get_x(xi, k) for xi in range(len(self.vals))]
    res = RV(self.vals, res_prob)
    res = _INTERNAL_PROB_LIMIT_VALS(res)
    return res

  # operators
  def __add__(self, other: T_ifsr):
    return self._convolve(other, operator.add)

  def __radd__(self, other: T_ifsr):
    return self._rconvolve(other, operator.add)

  def __sub__(self, other: T_ifsr):
    return self._convolve(other, operator.sub)

  def __rsub__(self, other: T_ifsr):
    return self._rconvolve(other, operator.sub)

  def __mul__(self, other: T_ifsr):
    return self._convolve(other, operator.mul)

  def __rmul__(self, other: T_ifsr):
    return self._rconvolve(other, operator.mul)

  def __floordiv__(self, other: T_ifsr):
    return self._convolve(other, operator.floordiv)

  def __rfloordiv__(self, other: T_ifsr):
    return self._rconvolve(other, operator.floordiv)

  def __truediv__(self, other: T_ifsr):
    return self._convolve(other, operator.truediv)

  def __rtruediv__(self, other: T_ifsr):
    return self._rconvolve(other, operator.truediv)

  def __pow__(self, other: T_ifsr):
    return self._convolve(other, operator.pow)

  def __rpow__(self, other: T_ifsr):
    return self._rconvolve(other, operator.pow)

  def __mod__(self, other: T_ifsr):
    return self._convolve(other, operator.mod)

  def __rmod__(self, other: T_ifsr):
    return self._rconvolve(other, operator.mod)

  # comparison operators
  def __eq__(self, other: T_ifsr):
    return self._convolve(other, lambda x, y: 1 if x == y else 0)

  def __ne__(self, other: T_ifsr):
    return self._convolve(other, lambda x, y: 1 if x != y else 0)

  def __lt__(self, other: T_ifsr):
    return self._convolve(other, lambda x, y: 1 if x < y else 0)

  def __le__(self, other: T_ifsr):
    return self._convolve(other, lambda x, y: 1 if x <= y else 0)

  def __gt__(self, other: T_ifsr):
    return self._convolve(other, lambda x, y: 1 if x > y else 0)

  def __ge__(self, other: T_ifsr):
    return self._convolve(other, lambda x, y: 1 if x >= y else 0)

  # boolean operators
  def __or__(self, other: T_ifsr):
    return self._convolve(other, lambda x, y: 1 if x or y else 0)

  def __ror__(self, other: T_ifsr):
    return self._rconvolve(other, lambda x, y: 1 if x or y else 0)

  def __and__(self, other: T_ifsr):
    return self._convolve(other, lambda x, y: 1 if x and y else 0)

  def __rand__(self, other: T_ifsr):
    return self._rconvolve(other, lambda x, y: 1 if x and y else 0)

  def __bool__(self):
    raise TypeError('Boolean values can only be numbers, but you provided RV')

  def __len__(self):
    # number of rolls that created this RV
    return self._source_roll

  def __hash__(self):
    return hash((self.vals, self.probs))

  def __pos__(self):
    return self

  def __neg__(self):
    return 0 - self

  def __invert__(self):
    return RV.from_const(1) if (self.vals, self.probs) == ((0, ), (1, )) else RV.from_const(0)

  def __abs__(self):
    return self._apply_operation(abs)

  def __round__(self, n=0):
    return self._apply_operation(lambda x: round(x, n))

  def __floor__(self):
    return self._apply_operation(math.floor)

  def __ceil__(self):
    return self._apply_operation(math.ceil)

  def __trunc__(self):
    return self._apply_operation(math.trunc)

  def __str__(self):
    # all the nuanced rules are kind of complex; simply took tons of trial and error with pytests for all possible combinations
    s, d = self._str_LHS_RHS
    if isinstance(s, float) or isinstance(d, float):  # __str__ doesn't support floats
      return 'd{?}'
    LHS = str(abs(s)) if (s is not None and abs(s) > 1) else ''
    if isinstance(d, int):
      sign = '' if (s * d) >= 0 else '-'
      RHS = '{0..0}' if (s * d == 0) else str(abs(d))
      return sign + LHS + 'd' + RHS
    if d == '{}':  # rolled an empty seq
      return 'd{}'
    elif s == 0:
      return 'd{0..0}'
    return LHS + 'd{?}'

  def __repr__(self):
    return output(self, print_=False)

  @staticmethod
  def dices_are_equal(d1: T_ifsr, d2: T_ifsr):
    if isinstance(d1, BlankRV) or isinstance(d2, BlankRV):
      return isinstance(d1, BlankRV) and isinstance(d2, BlankRV)
    if isinstance(d1, (int, float)) or isinstance(d1, Iterable):
      d1 = RV.from_seq([d1])
    if isinstance(d2, (int, float)) or isinstance(d2, Iterable):
      d2 = RV.from_seq([d2])
    return d1.vals == d2.vals and d1.probs == d2.probs


class BlankRV:
  def __init__(self, _special_null=False):
    self._special_null = _special_null  # makes it such that it's _special_null,  in operations like (X**2 + 1) still is blank (X). see https://anydice.com/program/395da

  def mean(self):
    return 0

  def std(self):
    return 0

  def output(self, *args, **kwargs):
    return output(self, *args, **kwargs)

  def __matmul__(self, other: T_ifs):
    # ( self:RV @ other ) thus not allowed,
    raise TypeError(f'A position selector must be either a number or a sequence, but you provided "{other}"')

  def __rmatmul__(self, other: T_is):
    if self._special_null:
      return 0 if other != 1 else self
    return self

  def __add__(self, other: T_ifsr):
    if self._special_null:
      return self
    return other

  def __radd__(self, other: T_ifsr):
    if self._special_null:
      return self
    return other

  def __sub__(self, other: T_ifsr):
    if self._special_null:
      return self
    if isinstance(other, Iterable):
      other = Seq(*other).sum()
    return (-other)

  def __rsub__(self, other: T_ifsr):
    if self._special_null:
      return self
    return other

  def __mul__(self, other: T_ifsr):
    return self

  def __rmul__(self, other: T_ifsr):
    return self

  def __floordiv__(self, other: T_ifsr):
    return self

  def __rfloordiv__(self, other: T_ifsr):
    return self

  def __truediv__(self, other: T_ifsr):
    return self

  def __rtruediv__(self, other: T_ifsr):
    return self

  def __pow__(self, other: T_ifsr):
    return self

  def __rpow__(self, other: T_ifsr):
    return self

  def __mod__(self, other: T_ifsr):
    return self

  def __rmod__(self, other: T_ifsr):
    return self

  # comparison operators
  def __eq__(self, other: T_ifsr):
    if self._special_null:
      return 1
    return self

  def __ne__(self, other: T_ifsr):
    if self._special_null:
      return 1
    return self

  def __lt__(self, other: T_ifsr):
    if self._special_null:
      return 1
    return self

  def __le__(self, other: T_ifsr):
    if self._special_null:
      return 1
    return self

  def __gt__(self, other: T_ifsr):
    if self._special_null:
      return 1
    return self

  def __ge__(self, other: T_ifsr):
    if self._special_null:
      return 1
    return self

  # boolean operators
  def __or__(self, other: T_ifsr):
    if self._special_null:
      return 1
    return self if isinstance(other, BlankRV) else other

  def __ror__(self, other: T_ifsr):
    if self._special_null:
      return 1
    return self if isinstance(other, BlankRV) else other

  def __and__(self, other: T_ifsr):
    if self._special_null:
      return 1
    return self

  def __rand__(self, other: T_ifsr):
    if self._special_null:
      return 1
    return self

  def __bool__(self):
    raise TypeError('Boolean values can only be numbers, but you provided RV')

  def __len__(self):
    if self._special_null:
      return 1
    return 0

  def __pos__(self):
    return self

  def __neg__(self):
    return self

  def __invert__(self):
    if self._special_null:
      return 1
    return self

  def __abs__(self):
    return self

  def __round__(self, n=0):
    return self

  def __floor__(self):
    return self

  def __ceil__(self):
    return self

  def __trunc__(self):
    return self

  def __str__(self):
    if self._special_null:
      return 'd{?}'
    return 'd{}'

  def __repr__(self):
    return output(self, print_=False)


class Seq(Iterable):
  def __init__(self, *source: T_ifsr, _INTERNAL_SEQ_VALUE=None):
    self._sum = None
    self._one_indexed = 1
    if _INTERNAL_SEQ_VALUE is not None:  # used for internal optimization only
      self._seq: tuple[T_if, ...] = _INTERNAL_SEQ_VALUE  # type: ignore
      return
    flat = tuple(utils.flatten(source))
    flat_rvs = [x for x in flat if isinstance(x, RV) and not isinstance(x, BlankRV)]  # expand RVs
    flat_rv_vals = [v for rv in flat_rvs for v in rv.vals]
    flat_else: list[T_if] = [x for x in flat if not isinstance(x, (RV, BlankRV))]
    assert all(isinstance(x, (int, float)) for x in flat_else), 'Seq must be made of numbers and RVs. Seq:' + str(flat_else)
    self._seq = tuple(flat_else + flat_rv_vals)

  def sum(self):
    if self._sum is None:
      self._sum = sum(self._seq)
    return self._sum

  def set_one_indexed(self, one_indexed: bool):
    self._one_indexed = 1 if one_indexed else 0

  def __str__(self):
    return '{?}'

  def __repr__(self):
    return f'Seq({repr(self._seq)})'

  def __iter__(self):
    return iter(self._seq)

  def __len__(self):
    return len(self._seq)

  def __invert__(self):
    return 1 if self.sum() == 0 else 0

  def __getitem__(self, i: int):
    return self._seq[i - self._one_indexed] if 0 <= i - self._one_indexed < len(self._seq) else 0

  def __matmul__(self, other: T_ifsr):
    if isinstance(other, RV):  # ( self:SEQ @ other:RV ) thus RV takes priority
      return other.__rmatmul__(self)
    # access at indices in other ( self @ other )
    if isinstance(other, (int, float)):
      other = Seq([int(d) for d in str(other)])  # SEQ @ int  thus convert int to sequence using base 10
    if not isinstance(other, Seq):
      other = Seq(other)
    assert all(isinstance(i, int) for i in self._seq), 'indices must be integers'
    return sum(other[int(i)] for i in self._seq)

  def __rmatmul__(self, other: T_ifs):
    if isinstance(other, RV):  # ( other:RV @ self:SEQ ) thus not allowed,
      raise TypeError(f'A position selector must be either a number or a sequence, but you provided "{other}"')
    # access in my indices ( other @ self )
    if isinstance(other, (int, float)):
      return self[int(other)]
    if not isinstance(other, Seq):
      other = Seq(other)
    assert all(isinstance(i, int) for i in other._seq), 'indices must be integers'
    return sum(self[int(i)] for i in other._seq)

  # operators
  def __add__(self, other: T_ifs):
    return operator.add(self.sum(), other)

  def __radd__(self, other: T_ifs):
    return operator.add(other, self.sum())

  def __sub__(self, other: T_ifs):
    return operator.sub(self.sum(), other)

  def __rsub__(self, other: T_ifs):
    return operator.sub(other, self.sum())

  def __mul__(self, other: T_ifs):
    return operator.mul(self.sum(), other)

  def __rmul__(self, other: T_ifs):
    return operator.mul(other, self.sum())

  def __floordiv__(self, other: T_ifs):
    return operator.floordiv(self.sum(), other)

  def __rfloordiv__(self, other: T_ifs):
    return operator.floordiv(other, self.sum())

  def __truediv__(self, other: T_ifs):
    return operator.truediv(self.sum(), other)

  def __rtruediv__(self, other: T_ifs):
    return operator.truediv(other, self.sum())

  def __pow__(self, other: T_ifs):
    return operator.pow(self.sum(), other)

  def __rpow__(self, other: T_ifs):
    return operator.pow(other, self.sum())

  def __mod__(self, other: T_ifs):
    return operator.mod(self.sum(), other)

  def __rmod__(self, other: T_ifs):
    return operator.mod(other, self.sum())

  # comparison operators
  def __eq__(self, other: T_ifsr):
    return self._compare_to(other, operator.eq)

  def __ne__(self, other: T_ifsr):
    return self._compare_to(other, operator.ne)

  def __lt__(self, other: T_ifsr):
    return self._compare_to(other, operator.lt)

  def __le__(self, other: T_ifsr):
    return self._compare_to(other, operator.le)

  def __gt__(self, other: T_ifsr):
    return self._compare_to(other, operator.gt)

  def __ge__(self, other: T_ifsr):
    return self._compare_to(other, operator.ge)

  # boolean operators
  def __or__(self, other: T_ifsr):
    return int((self.sum() != 0) or (other != 0)) if isinstance(other, (int, float)) else operator.or_(self.sum(), other)

  def __ror__(self, other: T_ifsr):
    return int((self.sum() != 0) or (other != 0)) if isinstance(other, (int, float)) else operator.or_(other, self.sum())

  def __and__(self, other: T_ifsr):
    return int((self.sum() != 0) and (other != 0)) if isinstance(other, (int, float)) else operator.and_(self.sum(), other)

  def __rand__(self, other: T_ifsr):
    return int((self.sum() != 0) and (other != 0)) if isinstance(other, (int, float)) else operator.and_(other, self.sum())

  def _compare_to(self, other: T_ifsr, operation: Callable[[float, T_ifr], bool]):
    if isinstance(other, RV):
      return operation(self.sum(), other)
    if isinstance(other, Iterable):
      if not isinstance(other, Seq):  # convert to Seq if not already
        other = Seq(*other)
      if operation == operator.ne:  # special case for NE, since it is ∃ as opposed to ∀ like the others
        return not self._compare_to(other, operator.eq)
      return all(operation(x, y) for x, y in zip_longest(self._seq, other._seq, fillvalue=float('-inf')))
    # if other is a number
    return sum(1 for x in self._seq if operation(x, other))

  @staticmethod
  def seqs_are_equal(s1: T_ifs, s2: T_ifs):
    assert not isinstance(s1, RV) and not isinstance(s2, RV), 'cannot compare Seq with RV'
    if not isinstance(s1, Seq):
      s1 = Seq(s1)
    if not isinstance(s2, Seq):
      s2 = Seq(s2)
    return s1._seq == s2._seq


def anydice_casting(verbose=False):  # noqa: C901
  # verbose = True
  # in the documenation of the anydice language https://anydice.com/docs/functions
  # it states that "The behavior of a function depends on what type of value it expects and what type of value it actually receives."
  # Thus there are 9 scenarios for each parameters
  # expect: int, actual: int  =  no change
  # expect: int, actual: seq  =  seq.sum()
  # expect: int, actual: rv   =  MUST CALL FUNCTION WITH EACH VALUE OF RV ("If a die is provided, then the function will be invoked for all numbers on the die – or the sums of a collection of dice – and the result will be a new die.")
  # expect: seq, actual: int  =  [int]
  # expect: seq, actual: seq  =  no change
  # expect: seq, actual: rv   =  MUST CALL FUNCTION WITH SEQUENCE OF EVERY ROLL OF THE RV ("If Expecting a sequence and dice are provided, then the function will be invoked for all possible sequences that can be made by rolling those dice. In that case the result will be a new die.")  # noqa: E501
  # expect: rv, actual: int   =  dice([int])
  # expect: rv, actual: seq   =  dice(seq)
  # expect: rv, actual: rv    =  no change
  def decorator(func):
    def wrapper(*args, **kwargs):
      args, kwargs = list(args), dict(kwargs)
      fullspec = inspect.getfullargspec(func)
      arg_names = fullspec.args  # list of arg names  for args (not kwargs)
      param_annotations = fullspec.annotations  # (arg_names): (arg_type)  that have been annotated

      hard_params = {}  # update parameters that are easy to update, keep the hard ones for later
      combined_args = list(enumerate(args)) + list(kwargs.items())
      if verbose:
        logger.debug(f'#args {len(combined_args)}')
      for k, arg_val in combined_args:
        arg_name = k if isinstance(k, str) else (arg_names[k] if k < len(arg_names) else None)  # get the name of the parameter (args or kwargs)
        if arg_name not in param_annotations:  # only look for annotated parameters
          if verbose:
            logger.debug(f'no anot {k}')
          continue
        expected_type = param_annotations[arg_name]
        actual_type = type(arg_val)
        new_val = None
        if expected_type not in (int, Seq, RV):
          if verbose:
            logger.debug(f'not int seq rv {k}')
          continue
        if isinstance(arg_val, BlankRV):  # EDGE CASE abort calling if casting int/Seq to BlankRV  (https://github.com/Ar-Kareem/PythonDice/issues/11)
          if expected_type in (int, Seq):
            if verbose:
              logger.debug(f'abort calling func due to BlankRV! {k}')
            return BlankRV(_special_null=True)
          continue  # casting BlankRV to RV means the function IS called and nothing changes
        casted_iter_to_seq = False
        if isinstance(arg_val, Iterable) and not isinstance(arg_val, Seq):  # if val is iter then need to convert to Seq
          arg_val = Seq(*arg_val)
          new_val = arg_val
          actual_type = Seq
          casted_iter_to_seq = True
        if (expected_type, actual_type) == (int, Seq):
          new_val = arg_val.sum()
        elif (expected_type, actual_type) == (int, RV):
          hard_params[k] = (arg_val, expected_type)
          continue
        elif (expected_type, actual_type) == (Seq, int):
          new_val = Seq([arg_val])
        elif (expected_type, actual_type) == (Seq, RV):
          hard_params[k] = (arg_val, expected_type)
          if verbose:
            logger.debug(f'EXPL {k}')
          continue
        elif (expected_type, actual_type) == (RV, int):
          new_val = RV.from_const(arg_val)  # type: ignore
        elif (expected_type, actual_type) == (RV, Seq):
          new_val = RV.from_seq(arg_val)
        elif not casted_iter_to_seq:  # no cast made and one of the two types is not known, no casting needed
          if verbose:
            logger.debug(f'no cast, {k}, {expected_type}, {actual_type}')
          continue
        if isinstance(k, str):
          kwargs[k] = new_val
        else:
          args[k] = new_val
        if verbose:
          logger.debug('cast {k}')
      if verbose:
        logger.debug(f'hard {[(k, v[1]) for k, v in hard_params.items()]}')
      if not hard_params:
        return func(*args, **kwargs)

      var_name = tuple(hard_params.keys())
      all_rolls_and_probs = []
      for k in var_name:
        v, expected_type = hard_params[k]
        assert isinstance(v, RV), 'expected type RV'
        if expected_type == Seq:
          r, p = v._get_expanded_possible_rolls()
        elif expected_type == int:
          r, p = v.vals, v.probs
        else:
          raise ValueError(f'casting RV to {expected_type} not supported')
        all_rolls_and_probs.append(zip(r, p))
      # FINALLY take product of all possible rolls
      all_rolls_and_probs = product(*all_rolls_and_probs)

      res_vals: list[Union[RV, BlankRV, Seq, int, float, None]] = []
      res_probs: list[int] = []
      for rolls_and_prob in all_rolls_and_probs:
        rolls = tuple(r for r, _ in rolls_and_prob)
        prob = math.prod(p for _, p in rolls_and_prob)
        # will update args and kwargs with each possible roll using var_name
        for k, v in zip(var_name, rolls):
          if isinstance(k, str):
            kwargs[k] = v
          else:
            args[k] = v
        val: T_ifsr = func(*args, **kwargs)  # single result of the function call
        if isinstance(val, Iterable):
          if not isinstance(val, Seq):
            val = Seq(*val)
          val = val.sum()
        if verbose:
          logger.debug(f'val {val} prob {prob}')
        res_vals.append(val)
        res_probs.append(prob)
      return RV.from_rvs(rvs=res_vals, weights=res_probs)
    return wrapper
  return decorator


def max_func_depth():
  # decorator to limit the depth of the function calls
  def decorator(func):
    def wrapper(*args, **kwargs):
      if SETTINGS['INTERNAL_CURR_DEPTH'] >= SETTINGS['maximum function depth']:
        msg = 'The maximum function depth was exceeded, results are truncated.'
        if not SETTINGS['INTERNAL_CURR_DEPTH_WARNING_PRINTED']:
          logger.warning(msg)
          print(msg)
          SETTINGS['INTERNAL_CURR_DEPTH_WARNING_PRINTED'] = True
        return BlankRV()
      SETTINGS['INTERNAL_CURR_DEPTH'] += 1
      res = func(*args, **kwargs)
      SETTINGS['INTERNAL_CURR_DEPTH'] -= 1
      return res if res is not None else BlankRV()
    return wrapper
  return decorator


@anydice_casting()
def _sum_at(orig: Seq, locs: Seq):
  return sum(orig[int(i)] for i in locs)


def myrange(left, right):
    if isinstance(left, RV):
        raise TypeError(f'A sequence range must begin with a number, while you provided "{left}".')
    if isinstance(right, RV):
        raise TypeError(f'A sequence range must begin with a number, while you provided "{right}".')
    return range(left, right + 1)


def roll(n: Union[T_isr, str], d: Union[T_isr, None] = None) -> Union[RV, BlankRV]:
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
  if isinstance(d, BlankRV):  # SPECIAL CASE: XdY where Y is BlankRV => BlankRV
    return BlankRV()
  if isinstance(n, BlankRV):  # SPECIAL CASE: XdY where X is BlankRV => Special BlankRV see https://anydice.com/program/395da
    return BlankRV(_special_null=True)
  if isinstance(d, Seq) and len(d) == 0:  # SPECIAL CASE: Xd{} => BlankRV
    return BlankRV()
  # both arguments are now exactly int|Seq|RV
  result = _roll(n, d)  # ROLL!
  assert not isinstance(result, BlankRV), 'should never happen!'
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


def _roll(n: Union[int, Seq, RV], d: Union[int, Seq, RV]) -> Union[RV, BlankRV]:
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
    assert not isinstance(result, BlankRV), 'should never happen!'
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


def _INTERNAL_PROB_LIMIT_VALS(rv: RV, sum_limit: float = 10e30):
  sum_ = rv._get_sum_probs()
  if sum_ <= sum_limit:
    return rv
  normalizing_const = int(10e10 * sum_ // sum_limit)
  logger.warning(f'WARNING reducing probabilities | sum limit {sum_limit}, sum{sum_:.1g}, NORMALIZING BY {normalizing_const:.1g} | from my calc, abs err <= {1 / (sum_ / normalizing_const - 1)}')
  # napkin math for the error. int(x) = x - x_ϵ where x_ϵ∈[0,1) is for the rounding error. Don't quote me on this math, not 100% sure.
  # P(x_i )=p_i/(∑p_i )  before normalization (p_i is an integer probability unbounded)
  # P(x_i )=p_i/(∑▒Nint(p_i/N) )  after normalization
  # abs err=p_i*(∑▒〖Nint(p_i/N)-∑p_i 〗)/(∑p_i*∑▒Nint(p_i/N) )
  # int(x)=x-x_ϵ  where x_ϵ∈[0,1)
  # abs err=p_i*(∑▒〖(p_i/N-(p_i/N)_eps )-(∑p_i)/N〗)/(∑p_i*∑▒(p_i/N-(p_i/N)_eps ) )
  # =p_i*((∑▒p_i/N-∑▒(p_i/N)_eps )-(∑p_i)/N)/(∑p_i*(∑▒p_i/N-∑▒(p_i/N)_eps ) )=p_i/(∑p_i )*(∑▒(p_i/N)_eps )/((∑▒p_i/N-∑▒(p_i/N)_eps ) )≤p_i/(∑p_i )*1/((∑▒p_i/CN-1) )≤1/(((∑▒p_i )/N-1) )

  rv.probs = tuple(p // normalizing_const for p in rv.probs)
  rv._get_sum_probs(force=True)  # force update sum
  return rv


def output(rv: Union[T_isr, None], named=None, show_pdf=True, blocks_width=None, print_=True, print_fn=None, cdf_cut=0):
  if isinstance(rv, Seq) and len(rv) == 0:  # empty sequence plotted as empty
    rv = BlankRV()
  if isinstance(rv, int) or isinstance(rv, Iterable) or isinstance(rv, bool):
    rv = RV.from_seq([rv])
  if blocks_width is None:
    blocks_width = SETTINGS['DEFAULT_OUTPUT_WIDTH']

  result = ''
  if named is not None:
    result += named + ' '

  if rv is None or isinstance(rv, BlankRV):
    result += '\n' + '-' * (blocks_width + 8)
    if print_:
      if print_fn is None:
        SETTINGS['DEFAULT_PRINT_FN'](result)
      else:
        print_fn(result)
      return
    else:
      return result
  assert isinstance(rv, RV), f'rv must be a RV {rv}'

  mean = rv.mean()
  mean = round(mean, 2) if mean is not None else None
  std = rv.std()
  std = round(std, 2) if std is not None else None
  result += f'{mean} ± {std}'
  if show_pdf:
    vp = rv.get_vals_probs(cdf_cut / 100)
    max_val_len = max(len(str(v)) for v, _ in vp)
    blocks = max(0, blocks_width - max_val_len)
    for v, p in vp:
      result += '\n' + f"{v:>{max_val_len}}: {100 * p:>5.2f}  " + ('█' * round(p * blocks))
    result += '\n' + '-' * (blocks_width + 8)
  if print_:
    if print_fn is None:
      SETTINGS['DEFAULT_PRINT_FN'](result)
    else:
      print_fn(result)
    return
  else:
    return result


def roller(rv: T_isr, count: Union[int, None] = None):
  if isinstance(rv, int) or isinstance(rv, Iterable) or isinstance(rv, bool):
    rv = RV.from_seq([rv])
  assert isinstance(rv, RV), 'rv must be a RV'
  # roll using random.choices
  if count is None:
    return random.choices(rv.vals, rv.probs)[0]
  return tuple(random.choices(rv.vals, rv.probs)[0] for _ in range(count))
