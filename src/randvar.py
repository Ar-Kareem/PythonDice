# from __future__ import annotations

import operator
import math
from typing import Callable, Iterable, Union
from itertools import combinations_with_replacement, accumulate
from collections import defaultdict
import logging

from . import factory
from .typings import MetaStr, T_if, T_ifs, T_ifsr, MetaRV, MetaSeq, T_S
from .settings import SETTINGS
from . import blackrv
from . import utils
from . import output
from . import decorators

logger = logging.getLogger(__name__)


class RV(MetaRV):
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
    zipped = RV._get_zip(vals, probs)
    # print('before', len(zipped))
    newzipped = RV._get_new_zipped(zipped, skip_zero_probs)
    # print('after', len(newzipped))
    return RV._get_normalized(newzipped, normalize)

  @staticmethod
  def _get_zip(v, p):
    return sorted(zip(v, p), reverse=True)

  @staticmethod
  def _get_new_zipped(zipped, skip_zero_probs):
    newzipped: list[tuple[float, int]] = []
    for i in range(len(zipped) - 1, 0, -1):
      if zipped[i][0] == zipped[i - 1][0]:  # add the two probs, go to next
        zipped[i - 1] = (zipped[i - 1][0], zipped[i - 1][1] + zipped[i][1])
      else:
        newzipped.append(zipped[i])
    if len(zipped) > 0:
      newzipped.append(zipped[0])
    if skip_zero_probs:
      newzipped = [v for v in newzipped if v[1] != 0]
    return newzipped

  @staticmethod
  def _get_normalized(newzipped, normalize):
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
  def from_seq(s: Iterable[T_ifs]):
    if not isinstance(s, MetaSeq):
      s = factory.get_seq(*s)
    if len(s) == 0:
      return RV([0], [1])
    return RV(s._seq, [1] * len(s))

  @staticmethod
  def from_rvs(rvs: Iterable[Union['int', 'float', MetaRV, MetaSeq, None]], weights: Union[Iterable[int], None] = None) -> MetaRV:
    rvs = tuple(rvs)
    if weights is None:
      weights = [1] * len(rvs)
    weights = tuple(weights)
    blank_inds = set(i for i, x in enumerate(rvs) if isinstance(x, blackrv.BlankRV) or x is None)
    rvs = tuple(x for i, x in enumerate(rvs) if i not in blank_inds)
    weights = tuple(w for i, w in enumerate(weights) if i not in blank_inds)
    if len(rvs) == 0:
      return blackrv.BlankRV()
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

  def filter(self, obj: T_ifsr):
    to_filter = set(factory.get_seq(obj))
    vp = tuple((v, p) for v, p in zip(self.vals, self.probs) if v not in to_filter)
    if len(vp) == 0:
        return RV.from_const(0)
    vals, probs = zip(*vp)
    assert all(isinstance(p, int) for p in probs), 'should not happen'
    probs_int: tuple[int] = probs  # type: ignore  assertion above
    return RV(vals, probs_int)

  def get_vals_probs(self, cdf_cut: float = 0):
    '''Get the values and their probabilities, if cdf_cut is given, then remove the maximum bottom n values that sum to less than cdf_cut'''
    assert 0 <= cdf_cut < 1, 'cdf_cut must be in [0, 1)'
    s = self._get_sum_probs()
    vals_probs: list[tuple[Union[float, str], float]] = list((v, p / s) for v, p in zip(self.vals, self.probs))
    # convert strings representing numbers as "string"
    for i, (v, p) in enumerate(vals_probs):
      if isinstance(v, MetaStr):
        vals_probs[i] = (f'"{v}"', p) if v.is_number() else (f'{v}', p)
    if cdf_cut > 0:  # cut the bottom vals/probs and when stop total cut probs is less than cdf_cut
      sorted_vals_probs = sorted(vals_probs, key=lambda x: x[1])
      accumelated_probs = tuple(accumulate(sorted_vals_probs, lambda x, y: (y[0], x[1] + y[1]), initial=(0, 0)))
      vals_to_cut = set(v for v, p in accumelated_probs if p < cdf_cut)
      vals_probs = list((v, p) for v, p in vals_probs if v not in vals_to_cut)
    return tuple(vals_probs)

  def get_cdf(self):
    '''Get CDF as RV where CDF(x) = P(X <= x)'''
    cdf_vals = self.vals
    cdf_probs = accumulate(self.probs)
    return type(self)(cdf_vals, cdf_probs)

  def output(self, *args, **kwargs):
    return output.output(self, *args, **kwargs)

  def _get_sum_probs(self, force=False):
    if self.sum_probs is None or force:
      self.sum_probs = sum(self.probs)
    return self.sum_probs

  def _get_expanded_possible_rolls(self):
    N, D = self._source_roll, self._source_die  # N rolls of D
    if N == 1:  # answer is simple (ALSO cannot use simplified formula for probs and bottom code WILL cause errors)
      return tuple(factory.get_seq(i) for i in D.vals), D.probs
    pdf_dict = {v: p for v, p in zip(D.vals, D.probs)}
    vals, probs = [], []
    FACTORIAL_N = utils.factorial(N)
    for roll in combinations_with_replacement(D.vals[::-1], N):
      vals.append(factory.get_seq(_INTERNAL_SEQ_VALUE=roll))
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
    if isinstance(other, blackrv.BlankRV):  # let BlankRV handle the operation
      return NotImplemented
    if isinstance(other, Iterable):
      if not isinstance(other, MetaSeq):
        other = factory.get_seq(*other)
      other = other.sum()
    if not isinstance(other, MetaRV):
      return RV([operation(v, other) for v in self.vals], self.probs)
    new_vals, new_probs = _rdict.fast_convolve((self.vals, self.probs), (other.vals, other.probs), operation)
    res = RV(new_vals, new_probs)
    res = _INTERNAL_PROB_LIMIT_VALS(res)
    return res

  def _rconvolve(self, other: T_ifsr, operation: Callable[[float, float], float]):
    if isinstance(other, blackrv.BlankRV):  # let BlankRV handle the operation
      return NotImplemented
    assert not isinstance(other, MetaRV)
    if isinstance(other, Iterable):
      if not isinstance(other, MetaSeq):
        other = factory.get_seq(*other)
      other = other.sum()
    return RV([operation(other, v) for v in self.vals], self.probs)

  def __matmul__(self, other: T_ifs):
    # ( self:RV @ other ) thus not allowed,
    raise TypeError(f'A position selector must be either a number or a sequence, but you provided "{other}"')

  def __rmatmul__(self, other):
    # ( other @ self:RV )
    # DOCUMENTATION: https://anydice.com/docs/introspection/  look for "Accessing" -> "Collections of dice" and "A single die"
    assert not isinstance(other, RV), 'unsupported operand type(s) for @: RV and RV'
    other = factory.get_seq([other])
    assert all(isinstance(i, int) for i in other._seq), 'indices must be integers'
    if len(other) == 1:  # only one index, return the value at that index
      k = other._seq[0]
      assert isinstance(k, int), 'unsupported operand type(s) for @: float and RV'
      return self._source_die._get_kth_order_statistic(self._source_roll, k)
    return _sum_at(self, other)  # type: ignore  anydice_casting

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
    return output.output(self, print_=False)

  @staticmethod
  def dices_are_equal(d1: T_ifsr, d2: T_ifsr):
    if isinstance(d1, blackrv.BlankRV) or isinstance(d2, blackrv.BlankRV):
      return isinstance(d1, blackrv.BlankRV) and isinstance(d2, blackrv.BlankRV)
    if isinstance(d1, (int, float)) or isinstance(d1, Iterable):
      d1 = RV.from_seq([d1])
    if isinstance(d2, (int, float)) or isinstance(d2, Iterable):
      d2 = RV.from_seq([d2])
    return d1.vals == d2.vals and d1.probs == d2.probs


@decorators.anydice_type_casting()
def _sum_at(orig: T_S, locs: T_S):
  return sum(orig[int(i)] for i in locs)


class _rdict:
  def __init__(self):
    self.d = {}

  def __setitem__(self, key, value):
    # in below comparisons, __setitem__ is called 6 million times
    # without using _rdict | 8.35 s
    # super().__setitem__(key, self.get(key, 0) + value)  # slowest code, self is subclass of dict | 4.43 s
    # self.d[key] = self.d.get(key, 0) + value  # slow code | 3.15 s
    # fastest code | 2.08 s
    if key in self.d:
      self.d[key] += value
    else:
      self.d[key] = value

  def to_tuples(self):
    sorted_items = sorted(self.d.items())
    keys, values = zip(*sorted_items) if sorted_items else ((), ())
    return keys, values

  @staticmethod
  def fast_convolve(items1: tuple[tuple, tuple], items2: tuple[tuple, tuple], operation: Callable[[float, float], float]):
    if operation == operator.add:
      return _rdict.__fast_convolve_op_add(items1, items2)
    d = _rdict()
    for k1, v1 in zip(*items1):
      for k2, v2 in zip(*items2):
        d[operation(k1, k2)] = v1 * v2
    return d.to_tuples()

  @staticmethod
  def __fast_convolve_op_add(items1, items2):
    """Since 'add' is the most common operation, we can optimize it by not calling operation() every iter of the N^2 algorithm"""
    d = _rdict()
    for k1, v1 in zip(*items1):
      for k2, v2 in zip(*items2):
        d[k1 + k2] = v1 * v2
    return d.to_tuples()


def _INTERNAL_PROB_LIMIT_VALS(rv: RV, sum_limit: float = 10e30):
  sum_ = rv._get_sum_probs()
  if sum_ <= sum_limit:
    return rv
  normalizing_const = int(10e10 * (sum_ // sum_limit))
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
