# from __future__ import annotations

import operator
import math
from typing import Callable, Iterable, Union
from itertools import zip_longest, product, combinations_with_replacement
import inspect

import utils

RV_AUTO_TRUNC = False  # if True, then RV will automatically truncate values to ints (replicate anydice behavior)

T_if = int|float
T_ifs = T_if|Iterable['T_ifs']  # recursive type
T_is = int|Iterable['T_is']  # recursive type

T_isr = Union[T_is, 'RV']
T_ifr = Union[T_if, 'RV']
T_ifsr = Union[T_ifs, 'RV']

T_s = Iterable['T_ifs']  # same as T_ifs but excludes int and float (not iterable)

class RV:
  def __init__(self, vals: Iterable[float], probs: Iterable[int], truncate=None):
    vals, probs = tuple(vals), tuple(probs)
    assert len(vals) == len(probs), 'vals and probs must be the same length'
    if truncate or (truncate is None and RV_AUTO_TRUNC):
      vals = tuple(int(v) for v in vals)
    self.vals, self.probs = RV._sort_and_group(vals, probs, skip_zero_probs=True, normalize=True)
    if len(self.vals) == 0:  # if no values, then add 0
      self.vals, self.probs = (0, ), (1, )
    self.sum_probs = None
    # by default, 1 roll of current RV
    self._source_roll = 1
    self._source_die = self

  @staticmethod
  def _sort_and_group(vals: Iterable[float], probs: Iterable[int], skip_zero_probs, normalize):
    assert all(isinstance(p, int) and p >= 0 for p in probs), 'probs must be non-negative integers'
    zipped = sorted(zip(vals, probs), reverse=True)
    newzipped: list[tuple[float, int]] = []
    for i in range(len(zipped)-1, -1, -1):
      if skip_zero_probs and zipped[i][1] == 0:
        continue
      if i > 0 and zipped[i][0] == zipped[i-1][0]: # add the two probs, go to next
        zipped[i-1] = (zipped[i-1][0], zipped[i-1][1]+zipped[i][1])
      else:
        newzipped.append(zipped[i])
    vals = tuple(v[0] for v in newzipped)
    probs = tuple(v[1] for v in newzipped)
    if normalize:
      gcd = math.gcd(*probs)
      if gcd > 1:  # simplify probs
        probs = tuple(p//gcd for p in probs)
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
    return RV(s._seq, [1]*len(s))

  @staticmethod
  def from_rvs(rvs: Iterable['int|float|RV'], weights: Iterable[int]|None=None) -> 'RV':
    rvs = tuple(rvs)
    if weights is None:
      weights = [1]*len(rvs)
    weights = tuple(weights)
    assert len(rvs) == len(weights)
    prob_sums = tuple(sum(r.probs) if isinstance(r, RV) else 1 for r in rvs)
    PROD = math.prod(prob_sums)  # to normalize probabilities such that the probabilities for each individual RV sum to const (PROD) and every probability is an int
    res_vals, res_probs = [], []
    for weight, prob_sum, rv in zip(weights, prob_sums, rvs):
      if isinstance(rv, RV):
        res_vals.extend(rv.vals)
        res_probs.extend(p*weight*(PROD//prob_sum) for p in rv.probs)
      else:
        res_vals.append(rv)
        res_probs.append(weight*PROD)  # prob_sum is 1
    result = RV(res_vals, res_probs)
    return result


  def set_source(self, roll: int, die: 'RV'):
    self._source_roll = roll
    self._source_die = die

  def mean(self):
    if self._get_sum_probs() == 0:
      return None
    return sum(v*p for v, p in zip(self.vals, self.probs)) / self._get_sum_probs()

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
        return RV((), ())
    vals, probs = zip(*vp)
    return RV(vals, probs)

  def get_vals_probs(self, cdf_cut: float=0):
    '''Get the values and their probabilities, if cdf_cut is given, then remove the maximum bottom n values that sum to less than cdf_cut'''
    assert 0 <= cdf_cut < 1, 'cdf_cut must be in [0, 1)'
    s = self._get_sum_probs()
    vals_probs = tuple((v, p/s) for v, p in zip(self.vals, self.probs))
    if cdf_cut > 0:  # cut the bottom vals/probs and when stop total cut probs is less than cdf_cut
      sorted_vals_probs = sorted(vals_probs, key=lambda x: x[1])
      from itertools import accumulate
      accumelated_probs = tuple(accumulate(sorted_vals_probs, lambda x, y: (y[0], x[1]+y[1]), initial=(0, 0)))
      vals_to_cut = set(v for v, p in accumelated_probs if p < cdf_cut)
      vals_probs = tuple((v, p) for v, p in vals_probs if v not in vals_to_cut)
    return vals_probs

  def get_cdf(self):
    '''Get CDF as RV where CDF(x) = P(X <= x)'''
    cdf_vals = self.vals
    from itertools import accumulate
    cdf_probs = accumulate(self.probs)
    return RV(cdf_vals, cdf_probs)

  def output(self, *args, **kwargs):
    return output(self, *args, **kwargs)

  def _get_sum_probs(self):
    if self.sum_probs is None:
      self.sum_probs = sum(self.probs)
    return self.sum_probs

  def _get_expanded_possible_rolls(self):
    N, D = self._source_roll, self._source_die  # N rolls of D
    if N == 1:  # answer is simple (ALSO cannot use simplified formula for probs and bottom code WILL cause errors)
      return tuple(Seq(i) for i in D.vals), D.probs
    all_rolls_and_probs = tuple(combinations_with_replacement(D.vals, N))
    pdf_dict = {v: p for v, p in zip(D.vals, D.probs)}
    vals = []
    probs = []
    FACTORIAL_N = utils.factorial(N)
    for roll in all_rolls_and_probs:
      vals.append(Seq(sorted(roll, reverse=True)))  # TODO sort_and_group getting a list[Seq] instead of list[float], can this cause errors? in groupping because of ==?
      counts = {v: roll.count(v) for v in roll}
      cur_roll_combination_count = FACTORIAL_N // math.prod(utils.factorial(c) for c in counts.values())
      cur_roll_probs = math.prod(pdf_dict[v]**c for v, c in counts.items())  # if D is a uniform then this = 1 and is not needed.
      probs.append(cur_roll_combination_count * cur_roll_probs)
    return RV._sort_and_group(vals, probs, skip_zero_probs=True, normalize=True)

  def _apply_operation(self, operation: Callable[[float], float]):
    return RV([operation(v) for v in self.vals], self.probs)
  def _convolve(self, other:T_ifsr, operation: Callable[[float, float], float]):
    if isinstance(other, Iterable):
      if not isinstance(other, Seq):
        other = Seq(*other)
      other = other.sum()
    if not isinstance(other, RV):
      return RV([operation(v, other) for v in self.vals], self.probs)
    new_vals = tuple(operation(v1, v2) for v1 in self.vals for v2 in other.vals)
    new_probs = tuple(p1*p2 for p1 in self.probs for p2 in other.probs)
    return RV(new_vals, new_probs)
  def _rconvolve(self, other:T_ifsr, operation: Callable[[float, float], float]):
    assert not isinstance(other, RV)
    if isinstance(other, Iterable):
      if not isinstance(other, Seq):
        other = Seq(*other)
      other = other.sum()
    return RV([operation(other, v) for v in self.vals], self.probs)

  def  __rmatmul__(self, other:T_is):
    # ( other @ self:RV )
    # DOCUMENTATION: https://anydice.com/docs/introspection/  look for "Accessing" -> "Collections of dice" and "A single die"
    assert not isinstance(other, RV), 'unsupported operand type(s) for @: RV and RV'
    other = Seq([other])
    assert all(isinstance(i, int) for i in other._seq), 'indices must be integers'
    if len(other) == 1:  # only one index, return the value at that index
      k: int = other._seq[0] # type: ignore
      return self._source_die._get_kth_order_statistic(self._source_roll, k)
    return _sum_at(self, other) # type: ignore 

  def _get_kth_order_statistic(self, draws: int, k: int):
    '''Get the k-th smallest value of n draws: k@RV where RV is n rolls of a die'''
    # k-th largest value of n draws: γ@RV where RV is n rolls of a die | FOR DISCRETE (what we need): https://en.wikipedia.org/wiki/Order_statistic#Dealing_with_discrete_variables
    N = draws
    k = N - k + 1  # wikipedia uses (k)-th smallest, we want (k)-th largest
    cdf = self.get_cdf().probs  # P(X <= x)
    sum_probs = self._get_sum_probs()
    p1 = tuple(cdf_x-p_x for p_x, cdf_x in zip(self.probs, cdf))  # P(X < x)
    p2 = self.probs # P(X = x)
    p3 = tuple(sum_probs-cdf_x for cdf_x in cdf)  # P(X > x)
    def get_x(xi, k):
      return sum(math.comb(N, j) * (p3[xi]**j * (p1[xi]+p2[xi])**(N-j) - (p2[xi]+p3[xi])**j * p1[xi]**(N-j)) for j in range(N-k +1))
    res_prob = [get_x(xi, k) for xi in range(len(self.vals))]
    return RV(self.vals, res_prob)

  def __add__(self, other:T_ifsr):
    return self._convolve(other, operator.add)
  def __radd__(self, other:T_ifsr):
    return self._rconvolve(other, operator.add)
  def __sub__(self, other:T_ifsr):
    return self._convolve(other, operator.sub)
  def __rsub__(self, other:T_ifsr):
    return self._rconvolve(other, operator.sub)
  def __mul__(self, other:T_ifsr):
    return self._convolve(other, operator.mul)
  def __rmul__(self, other:T_ifsr):
    return self._rconvolve(other, operator.mul)
  def __floordiv__(self, other:T_ifsr):
    return self._convolve(other, operator.floordiv)
  def __rfloordiv__(self, other:T_ifsr):
    return self._rconvolve(other, operator.floordiv)
  def __truediv__(self, other:T_ifsr):
    return self._convolve(other, operator.truediv)
  def __rtruediv__(self, other:T_ifsr):
    return self._rconvolve(other, operator.truediv)
  def __pow__(self, other:T_ifsr):
    return self._convolve(other, operator.pow)
  def __rpow__(self, other:T_ifsr):
    return self._rconvolve(other, operator.pow)
  def __mod__(self, other:T_ifsr):
    return self._convolve(other, operator.mod)
  def __rmod__(self, other:T_ifsr):
    return self._rconvolve(other, operator.mod)

  def __eq__(self, other:T_ifsr):
    return self._convolve(other, lambda x, y: 1 if x == y else 0)
  def __ne__(self, other:T_ifsr):
    return self._convolve(other, lambda x, y: 1 if x != y else 0)
  def __lt__(self, other:T_ifsr):
    return self._convolve(other, lambda x, y: 1 if x < y else 0)
  def __le__(self, other:T_ifsr):
    return self._convolve(other, lambda x, y: 1 if x <= y else 0)
  def __gt__(self, other:T_ifsr):
    return self._convolve(other, lambda x, y: 1 if x > y else 0)
  def __ge__(self, other:T_ifsr):
    return self._convolve(other, lambda x, y: 1 if x >= y else 0)

  def __bool__(self):
    assert all(v in (0, 1) for v in self.vals)
    return len(self.vals) == 1 and self.vals[0] == 1
  def __len__(self):
    # number of rolls that created this RV
    return self._source_roll
  def __hash__(self):
    return hash((self.vals, self.probs))

  def __pos__(self):
    return self
  def __neg__(self):
    return 0 - self
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

  def __repr__(self):
    return output(self, print_=False)

  @staticmethod
  def dices_are_equal(d1:T_ifsr, d2:T_ifsr):
    if isinstance(d1, (int, float)) or isinstance(d1, Iterable):
      d1 = RV.from_seq([d1])
    if isinstance(d2, (int, float)) or isinstance(d2, Iterable):
      d2 = RV.from_seq([d2])
    return d1.vals == d2.vals and d1.probs == d2.probs

class Seq(Iterable):
  def __init__(self, *source: T_ifsr):
    flat = tuple(utils.flatten(source))
    flat_rvs = [v for x in flat if isinstance(x, RV) for v in x.vals]  # expand RVs
    flat_else: list[T_if] = [x for x in flat if not isinstance(x, RV)]
    assert all(isinstance(x, (int, float)) for x in flat_else), 'Seq must be made of numbers and RVs'
    self._seq = tuple(flat_else + flat_rvs)
    self._sum = None
    self.set_one_indexed(True)

  def sum(self):
    if self._sum is None:
      self._sum = sum(self._seq)
    return self._sum
  def set_one_indexed(self, one_indexed: bool):
    self._one_indexed = 1 if one_indexed else 0

  def __repr__(self):
    return str(self._seq)
  def __iter__(self):
    return iter(self._seq)
  def __len__(self):
    return len(self._seq)
  def __getitem__(self, i: int):
    return self._seq[i-self._one_indexed] if 0 <= i-self._one_indexed < len(self._seq) else 0

  def  __matmul__(self, other: T_ifsr):
    if isinstance(other, RV):  # ( self:SEQ @ other:RV ) thus RV takes priority
      return other.__rmatmul__(self)
    # access at indices in other ( self @ other )
    if isinstance(other, (int, float)):
      other = Seq([int(d) for d in str(other)])  # SEQ @ int  thus convert int to sequence using base 10
    if not isinstance(other, Seq):
      other = Seq(other)
    assert all(isinstance(i, int) for i in self._seq), 'indices must be integers'
    return sum(other[int(i)] for i in self._seq)
  def __rmatmul__(self, other:T_ifs):
    if isinstance(other, RV):  # ( other:RV @ self:SEQ ) thus not allowed,
      raise TypeError('unsupported operand type(s) for @: RV and Seq')
    # access in my indices ( other @ self )
    if isinstance(other, (int, float)):
      return self[int(other)]
    if not isinstance(other, Seq):
      other = Seq(other)
    assert all(isinstance(i, int) for i in other._seq), 'indices must be integers'
    return sum(self[int(i)] for i in other._seq)

  def __add__(self, other:T_ifs):
    return operator.add(self.sum(), other)
  def __radd__(self, other:T_ifs):
    return operator.add(other, self.sum())
  def __sub__(self, other:T_ifs):
    return operator.sub(self.sum(), other)
  def __rsub__(self, other:T_ifs):
    return operator.sub(other, self.sum())
  def __mul__(self, other:T_ifs):
    return operator.mul(self.sum(), other)
  def __rmul__(self, other:T_ifs):
    return operator.mul(other, self.sum())
  def __floordiv__(self, other:T_ifs):
    return operator.floordiv(self.sum(), other)
  def __rfloordiv__(self, other:T_ifs):
    return operator.floordiv(other, self.sum())
  def __truediv__(self, other:T_ifs):
    return operator.truediv(self.sum(), other)
  def __rtruediv__(self, other:T_ifs):
    return operator.truediv(other, self.sum())
  def __pow__(self, other:T_ifs):
    return operator.pow(self.sum(), other)
  def __rpow__(self, other:T_ifs):
    return operator.pow(other, self.sum())
  def __mod__(self, other:T_ifs):
    return operator.mod(self.sum(), other)
  def __rmod__(self, other:T_ifs):
    return operator.mod(other, self.sum())

  def __eq__(self, other:T_ifsr):
    return self._compare_to(other, operator.eq)
  def __ne__(self, other:T_ifsr):
    return self._compare_to(other, operator.ne)
  def __lt__(self, other:T_ifsr):
    return self._compare_to(other, operator.lt)
  def __le__(self, other:T_ifsr):
    return self._compare_to(other, operator.le)
  def __gt__(self, other:T_ifsr):
    return self._compare_to(other, operator.gt)
  def __ge__(self, other:T_ifsr):
    return self._compare_to(other, operator.ge)

  def _compare_to(self, other:T_ifsr, operation: Callable[[float, T_ifr], bool]):
    if isinstance(other, RV):
      return operation(self.sum(), other)
    if isinstance(other, Iterable):
      if not isinstance(other, Seq):  # convert to Seq if not already
        other = Seq(*other)
      if operation == operator.ne: # special case for NE, since it is ∃ as opposed to ∀ like the others
        return not self._compare_to(other, operator.eq)
      return all(operation(x, y) for x, y in zip_longest(self._seq, other._seq, fillvalue=float('-inf')))
    # if other is a number
    return sum(1 for x in self._seq if operation(x, other))

  @staticmethod
  def seqs_are_equal(s1:T_ifs, s2:T_ifs):
    assert not isinstance(s1, RV) and not isinstance(s2, RV), 'cannot compare Seq with RV'
    if not isinstance(s1, Seq):
      s1 = Seq(s1)
    if not isinstance(s2, Seq):
      s2 = Seq(s2)
    return s1._seq == s2._seq

def anydice_casting(verbose=False):
  # in the documenation of the anydice language https://anydice.com/docs/functions
  # it states that "The behavior of a function depends on what type of value it expects and what type of value it actually receives."
  # Thus there are 9 scenarios for each parameters
  # expect: int, actual: int  =  no change
  # expect: int, actual: seq  =  seq.sum()
  # expect: int, actual: rv   =  MUST CALL FUNCTION WITH EACH VALUE OF RV ("If a die is provided, then the function will be invoked for all numbers on the die – or the sums of a collection of dice – and the result will be a new die.")
  # expect: seq, actual: int  =  [int]
  # expect: seq, actual: seq  =  no change
  # expect: seq, actual: rv   =  MUST CALL FUNCTION WITH SEQUENCE OF EVERY ROLL OF THE RV ("If Expecting a sequence and dice are provided, then the function will be invoked for all possible sequences that can be made by rolling those dice. In that case the result will be a new die.")
  # expect: rv, actual: int   =  dice([int])
  # expect: rv, actual: seq   =  dice(seq)
  # expect: rv, actual: rv    =  no change
  def decorator(func):
    def wrapper(*args, **kwargs):
      args, kwargs = list(args), dict(kwargs)
      fullspec = inspect.getfullargspec(func)
      arg_names = fullspec.args  # list of arg names  for args (not kwargs)
      param_annotations = fullspec.annotations  # (arg_names): (arg_type)  that have been annotated

      hard_params = {} # update parameters that are easy to update, keep the hard ones for later
      combined_args = list(enumerate(args)) + list(kwargs.items())
      if verbose: print('#args', len(combined_args))
      for k, arg_val in combined_args:
        arg_name = k if isinstance(k, str) else (arg_names[k] if k < len(arg_names) else None)  # get the name of the parameter (args or kwargs)
        if arg_name not in param_annotations:  # only look for annotated parameters
          if verbose: print('no anot', k)
          continue
        expected_type = param_annotations[arg_name]
        actual_type = type(arg_val)
        new_val = None
        if expected_type not in (int, Seq, RV):
          if verbose: print('not int seq rv', k)
          continue
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
          if verbose: print('EXPL', k)
          continue
        elif (expected_type, actual_type) == (RV, int):
          new_val = RV.from_const(arg_val)  # type: ignore
        elif (expected_type, actual_type) == (RV, Seq):
          new_val = RV.from_seq(arg_val)
        elif not casted_iter_to_seq:  # no cast made and one of the two types is not known, no casting needed
          if verbose: print('no cast', k, expected_type, actual_type)
          continue
        if isinstance(k, str):
          kwargs[k] = new_val
        else:
          args[k] = new_val
        if verbose: print('cast', k)
      if verbose: print('hard', list(hard_params.keys()))
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

      res_vals: list[RV|int|float] = []
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
        if val is None:
          continue
        if isinstance(val, Iterable):
          if not isinstance(val, Seq):
            val = Seq(*val)
          val = val.sum()
        res_vals.append(val)
        res_probs.append(prob)
      return RV.from_rvs(rvs=res_vals, weights=res_probs)
    return wrapper
  return decorator

@anydice_casting()
def _sum_at(orig: Seq, locs: Seq):
  return sum(orig[int(i)] for i in locs)

def roll(n: T_isr|str, d: T_isr|None=None) -> RV:
  if isinstance(n, str):  # either rolL('ndm') or roll('dm')
    assert d is None, 'if n is a string, then d must be None'
    nm1, nm2 = n.split('d')
    if nm1 == '':
      nm1 = 1
    return roll(int(nm1), int(nm2))

  if d is None:  # if only one argument, then roll it as a dice once
    return roll(1, n)
  if isinstance(d, int):
    if d > 0:
      d = RV.from_seq(range(1, d+1))
    elif d == 0:
      d = RV.from_const(0)
    else:
      d = RV.from_seq([range(d, 0)])
  elif isinstance(d, Iterable):
    d = RV.from_seq(d)

  if isinstance(n, Iterable):
    if not isinstance(n, Seq):
      n = Seq(*n)  # convert to Seq if not already, to flatten and take sum
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

_MEMOIZED = {}
def _roll_int_rv(n: int, d: RV) -> RV:
  if (n, d) in _MEMOIZED:
    return _MEMOIZED[(n, d)]
  if n < 0:
    return -_roll_int_rv(-n, d)
  if n == 0:
    return RV.from_const(0)
  if n == 1:
    return d
  half = _roll_int_rv(n//2, d)
  full = half+half
  if n%2 == 1:
    full = full + d
  full.set_source(n, d)
  _MEMOIZED[(n, d)] = full
  return full


def output(rv: T_isr, named=None, show_pdf=True, blocks_width=170, print_=True, cdf_cut=0):
  if isinstance(rv, int) or isinstance(rv, Iterable):
    rv = RV.from_seq([rv])
  result = ''
  if named is not None:
    result += named + ' '

  mean = rv.mean()
  mean = round(mean, 2) if mean is not None else None
  std = rv.std()
  std = round(std, 2) if std is not None else None
  result += f'{mean} ± {std}'
  if show_pdf:
    vp = rv.get_vals_probs(cdf_cut/100)
    max_val_len = max(len(str(v)) for v, _ in vp)
    blocks = max(0, blocks_width - max_val_len)
    for v, p in vp:
      result += '\n' + f"{v:>{max_val_len}}: {100*p:>5.2f}  " + ('█'*round(p * blocks))
    result += '\n' + '-' * (blocks_width + 8)
  if print_:
    print(result)
  else:
    return result
