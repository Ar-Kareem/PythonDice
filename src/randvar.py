# from __future__ import annotations

import operator
import math
from typing import Sequence, Iterable
from itertools import zip_longest, product, combinations_with_replacement
import inspect

import utils

RV_AUTO_TRUNC = False  # if True, then RV will automatically truncate values to ints (replicate anydice behavior)

class RV:
  def __init__(self, vals: Sequence[float], probs: Sequence[int], truncate=None):
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
  def _sort_and_group(vals: Sequence[float], probs: Sequence[int], skip_zero_probs=True, normalize=True):
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
  def from_const(val: int|float):
    return RV([val], [1])

  @staticmethod
  def from_seq(s: Iterable):
    if not isinstance(s, Seq):
      s = Seq(*s)
    if len(s) == 0:
      return RV([0], [1])
    return RV(s._seq, [1]*len(s))

  @staticmethod
  def from_rvs(rvs: Sequence['RV'], weights: Sequence[int]|None=None) -> 'RV':
    if weights is None:
      weights = [1]*len(rvs)
    assert len(rvs) == len(weights)
    prob_sums = tuple(sum(r.probs) for r in rvs)
    PROD = math.prod(prob_sums)  # to normalize probabilities such that the probabilities for each individual RV sum to const (PROD) and every probability is an int
    # combine all possibilities into one RV
    res_vals = tuple(list(r.vals) for r in rvs)
    res_probs = tuple([x*weight*(PROD//prob_sum) for x in rv.probs] for weight, prob_sum, rv in zip(weights, prob_sums, rvs))
    result = RV(sum(res_vals, []), sum(res_probs, []))
    return result


  def set_source(self, roll, die):
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

  def _get_sum_probs(self):
    if self.sum_probs is None:
      self.sum_probs = sum(self.probs)
    return self.sum_probs

  def _get_expanded_possible_rolls_LEGACY_SLOW(self) -> tuple[tuple[tuple[float, ...]|float, ...], tuple[int, ...]]:
    N, D = self._source_roll, self._source_die  # N rolls of D
    all_rolls_and_probs = tuple(product(zip(D.vals, D.probs), repeat=N))
    vals = []
    probs = []
    for roll in all_rolls_and_probs:
      vals.append(tuple(sorted((v for v, _ in roll))))
      probs.append(math.prod(p for _, p in roll))
    return RV._sort_and_group(vals, probs, skip_zero_probs=True, normalize=True)

  def _get_expanded_possible_rolls(self) -> tuple[tuple[tuple[float, ...]|float, ...], tuple[int, ...]]:
    N, D = self._source_roll, self._source_die  # N rolls of D
    all_rolls_and_probs = tuple(combinations_with_replacement(D.vals, N))
    vals = []
    probs = []
    FACTORIAL_N = utils.factorial(N)
    for roll in all_rolls_and_probs:
      vals.append(Seq(sorted(roll, reverse=True)))
      counts = {v: roll.count(v) for v in roll}
      probs.append(FACTORIAL_N // math.prod(utils.factorial(c) for c in counts.values()))
    return RV._sort_and_group(vals, probs, skip_zero_probs=True, normalize=True)

  def _apply_operation(self, operation):
    return RV([operation(v) for v in self.vals], self.probs)
  def _convolve(self, other, operation):
    if isinstance(other, Seq):
      other = other.sum()
    if not isinstance(other, RV):
      return RV([operation(v, other) for v in self.vals], self.probs)
    new_vals = tuple(operation(v1, v2) for v1 in self.vals for v2 in other.vals)
    new_probs = tuple(p1*p2 for p1 in self.probs for p2 in other.probs)
    return RV(new_vals, new_probs)
  def _rconvolve(self, other, operation):
    assert not isinstance(other, RV)
    if isinstance(other, Seq):
      other = other.sum()
    return RV([operation(other, v) for v in self.vals], self.probs)

  def  __rmatmul__(self, other):
    # ( other @ self:RV )
    # DOCUMENTATION: https://anydice.com/docs/introspection/  look for "Accessing" -> "Collections of dice" and "A single die"
    # ignore type error because of the decorator
    return _sum_at(self, other) # type: ignore

  def __add__(self, other):
    return self._convolve(other, operator.add)
  def __radd__(self, other):
    return self._rconvolve(other, operator.add)
  def __sub__(self, other):
    return self._convolve(other, operator.sub)
  def __rsub__(self, other):
    return self._rconvolve(other, operator.sub)
  def __mul__(self, other):
    return self._convolve(other, operator.mul)
  def __rmul__(self, other):
    return self._rconvolve(other, operator.mul)
  def __floordiv__(self, other):
    return self._convolve(other, operator.floordiv)
  def __rfloordiv__(self, other):
    return self._rconvolve(other, operator.floordiv)
  def __truediv__(self, other):
    return self._convolve(other, operator.truediv)
  def __rtruediv__(self, other):
    return self._rconvolve(other, operator.truediv)
  def __pow__(self, other):
    return self._convolve(other, operator.pow)
  def __rpow__(self, other):
    return self._rconvolve(other, operator.pow)
  def __mod__(self, other):
    return self._convolve(other, operator.mod)
  def __rmod__(self, other):
    return self._rconvolve(other, operator.mod)

  def __eq__(self, other):
    return self._convolve(other, lambda x, y: 1 if x == y else 0)
  def __ne__(self, other):
    return self._convolve(other, lambda x, y: 1 if x != y else 0)
  def __lt__(self, other):
    return self._convolve(other, lambda x, y: 1 if x < y else 0)
  def __le__(self, other):
    return self._convolve(other, lambda x, y: 1 if x <= y else 0)
  def __gt__(self, other):
    return self._convolve(other, lambda x, y: 1 if x > y else 0)
  def __ge__(self, other):
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
  def dices_are_equal(d1, d2):
    if isinstance(d1, int) or isinstance(d1, Iterable):
      d1 = RV.from_seq([d1])
    if isinstance(d2, int) or isinstance(d2, Iterable):
      d2 = RV.from_seq([d2])
    return d1.vals == d2.vals and d1.probs == d2.probs

class Seq(Iterable):
  def __init__(self, *source):
    flat = tuple(utils.flatten(source))
    flat_rvs = [v for x in flat if isinstance(x, RV) for v in x.vals]  # expand RVs
    flat_else: list[int|float] = [x for x in flat if not isinstance(x, RV)]
    assert all(isinstance(x, (int, float)) for x in flat_else), 'Seq must be made of numbers and RVs'
    self._seq = tuple(flat_else + flat_rvs)
    self._one_indexed = 1  # 1 is True, 0 is False
    self._sum = None

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
  def __getitem__(self, i):
    return self._seq[i-self._one_indexed] if 0 <= i-self._one_indexed < len(self._seq) else 0

  def  __matmul__(self, other):
    if isinstance(other, RV):  # ( self:SEQ @ other:RV ) thus RV takes priority
      return other.__rmatmul__(self)
    # access at indices in other ( self @ other )
    if not isinstance(other, Seq):
      other = Seq(other)
    return sum(other[i] for i in self._seq)
  def __rmatmul__(self, other):
    if isinstance(other, RV):  # ( other:RV @ self:SEQ ) thus not allowed,
      raise TypeError('unsupported operand type(s) for @: RV and Seq')
    # access in my indices ( other @ self )
    if isinstance(other, int):
      return self[other]
    if not isinstance(other, Seq):
      other = Seq(other)
    return sum(self[i] for i in other._seq)

  def __add__(self, other):
    return operator.add(self.sum(), other)
  def __radd__(self, other):
    return operator.add(other, self.sum())
  def __sub__(self, other):
    return operator.sub(self.sum(), other)
  def __rsub__(self, other):
    return operator.sub(other, self.sum())
  def __mul__(self, other):
    return operator.mul(self.sum(), other)
  def __rmul__(self, other):
    return operator.mul(other, self.sum())
  def __floordiv__(self, other):
    return operator.floordiv(self.sum(), other)
  def __rfloordiv__(self, other):
    return operator.floordiv(other, self.sum())
  def __truediv__(self, other):
    return operator.truediv(self.sum(), other)
  def __rtruediv__(self, other):
    return operator.truediv(other, self.sum())
  def __pow__(self, other):
    return operator.pow(self.sum(), other)
  def __rpow__(self, other):
    return operator.pow(other, self.sum())
  def __mod__(self, other):
    return operator.mod(self.sum(), other)
  def __rmod__(self, other):
    return operator.mod(other, self.sum())

  def __eq__(self, other):
    return self._compare_to(other, operator.eq)
  def __ne__(self, other):
    return self._compare_to(other, operator.ne)
  def __lt__(self, other):
    return self._compare_to(other, operator.lt)
  def __le__(self, other):
    return self._compare_to(other, operator.le)
  def __gt__(self, other):
    return self._compare_to(other, operator.gt)
  def __ge__(self, other):
    return self._compare_to(other, operator.ge)

  def _compare_to(self, other, operation):
    if isinstance(other, RV):
      return operation(self.sum(), other)
    if isinstance(other, Iterable):
      if not isinstance(other, Seq):  # convert to Seq if not already
        other = Seq(*other)
      if operation == operator.ne: # special case for NE, since it is ∃ as opposed to ∀ like the others
        return not self._compare_to(other, operator.eq)
      return all(operation(x, y) for x, y in zip_longest(self._seq, other, fillvalue=float('-inf')))
    # if other is a number
    return sum(1 for x in self._seq if operation(x, other))

  @staticmethod
  def seqs_are_equal(s1, s2):
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
          new_val = RV.from_const(arg_val)
        elif (expected_type, actual_type) == (RV, Seq):
          new_val = RV.from_seq(arg_val)
        else:  # one of the types is not int, Seq, or RV or no casting needed
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

      res_vals: list[RV] = []
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
        val: int|float|Seq|RV = func(*args, **kwargs)  # single result of the function call
        if isinstance(val, Seq):
          val = val.sum()
        if not isinstance(val, RV):
          val = RV([val], [1])
        res_vals.append(val)
        res_probs.append(prob)
      return RV.from_rvs(rvs=res_vals, weights=res_probs)
    return wrapper
  return decorator

@anydice_casting()
def _sum_at(orig: Seq, locs: Seq):
  return sum(orig[i] for i in locs)

def roll(n: int|Iterable|RV, d: int|Iterable|RV|None=None) -> RV:
  if d is None:  # if only one argument, then roll it as a dice once
    return roll(1, n)
  if isinstance(n, Iterable):
    if not isinstance(n, Seq):
      n = Seq(*n)  # convert to Seq if not already, to flatten
    vals = list(n)
    assert all(isinstance(v, int) for v in vals), 'Seq must have int values to roll other dice'
    result = sum((roll(i, d) for i in vals), start=RV.from_const(0))
    result.set_source(n.sum(), d)
    return result
  if isinstance(n, RV):
    assert all(isinstance(v, int) for v in n.vals), 'RV must have int values to roll other dice'
    dies = tuple(roll(int(v), d) for v in n.vals)
    result = RV.from_rvs(rvs=dies, weights=n.probs)
    result.set_source(1, d)
    return result
  if isinstance(d, int):
    if d > 0:
      d = RV.from_seq(range(1, d+1))
    elif d == 0:
      d = RV.from_const(0)
    else:
      d = RV.from_seq([range(d, 0)])
  elif isinstance(d, Iterable):
    d = RV.from_seq(d)
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


def output(rv: RV|Iterable|int, named=None, show_pdf=True, blocks_width=170, print_=True):
  if isinstance(rv, int) or isinstance(rv, Iterable):
    rv = RV.from_seq([rv])
  result = ''
  if named is not None:
    result += named + ' '

  sum_p = sum(rv.probs)
  mean = rv.mean()
  mean = round(mean, 2) if mean is not None else None
  std = rv.std()
  std = round(std, 2) if std is not None else None
  result += f'{mean} ± {std}'
  if show_pdf:
    for v, p in zip(rv.vals, rv.probs):
      result += '\n' + f"{v:.2g}: {100*p/sum_p:.2f}  " + ('█'*round(p/sum_p * blocks_width))
    result += '\n' + '-'*blocks_width
  if print_:
    print(result)
  else:
    return result
