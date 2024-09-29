import operator
import math
from typing import Sequence, Iterable
import utils
from itertools import zip_longest

class RV:
  def __init__(self, vals: Sequence[float], probs: Sequence[int]):
    zipped = sorted(zip(vals, probs), reverse=True)
    newzipped: list[tuple[float, int]] = []
    for i in range(len(zipped)-1, -1, -1):
      if i > 0 and zipped[i][0] == zipped[i-1][0]: # add the two probs, go to next
        zipped[i-1] = (zipped[i-1][0], zipped[i-1][1]+zipped[i][1])
      else:
        newzipped.append(zipped[i])
    self.vals = tuple(v[0] for v in newzipped)
    self.probs = tuple(v[1] for v in newzipped)
    assert all(isinstance(p, int) and p >= 0 for p in self.probs), 'probs must be non-negative integers'
    gcd = math.gcd(*self.probs)
    self.probs = tuple(p//gcd for p in self.probs)

  def mean(self):
    sum_p = sum(self.probs)
    if sum_p == 0:
      return None
    return sum(v*p for v, p in zip(self.vals, self.probs)) / sum_p
  def std(self):
    mean = self.mean()
    mean_X2 = RV(tuple(v**2 for v in self.vals), self.probs).mean()
    if mean is None or mean_X2 is None:
      return None
    var = mean_X2 - mean**2
    return math.sqrt(var)
  def convolve(self, other, operation):
    if isinstance(other, Seq):
      other = other.sum()
    if not isinstance(other, RV):
      return RV([operation(v, other) for v in self.vals], self.probs)
    new_vals = tuple(operation(v1, v2) for v1 in self.vals for v2 in other.vals)
    new_probs = tuple(p1*p2 for p1 in self.probs for p2 in other.probs)
    return RV(new_vals, new_probs)
  def rconvolve(self, other, operation):
    assert not isinstance(other, RV)
    if isinstance(other, Seq):
      other = other.sum()
    return RV([operation(other, v) for v in self.vals], self.probs)

  def __add__(self, other):
    return self.convolve(other, operator.add)
  def __radd__(self, other):
    return self.rconvolve(other, operator.add)
  def __sub__(self, other):
    return self.convolve(other, operator.sub)
  def __rsub__(self, other):
    return self.rconvolve(other, operator.sub)
  def __mul__(self, other):
    return self.convolve(other, operator.mul)
  def __rmul__(self, other):
    return self.rconvolve(other, operator.mul)
  def __floordiv__(self, other):
    return self.convolve(other, operator.floordiv)
  def __rfloordiv__(self, other):
    return self.rconvolve(other, operator.floordiv)
  def __truediv__(self, other):
    return self.convolve(other, operator.truediv)
  def __rtruediv__(self, other):
    return self.rconvolve(other, operator.truediv)
  def __pow__(self, other):
    return self.convolve(other, operator.pow)
  def __rpow__(self, other):
    return self.rconvolve(other, operator.pow)
  def __mod__(self, other):
    return self.convolve(other, operator.mod)
  def __rmod__(self, other):
    return self.rconvolve(other, operator.mod)

  def __eq__(self, other):
    return self.convolve(other, lambda x, y: 1 if x == y else 0)
  def __ne__(self, other):
    return self.convolve(other, lambda x, y: 1 if x != y else 0)
  def __lt__(self, other):
    return self.convolve(other, lambda x, y: 1 if x < y else 0)
  def __le__(self, other):
    return self.convolve(other, lambda x, y: 1 if x <= y else 0)
  def __gt__(self, other):
    return self.convolve(other, lambda x, y: 1 if x > y else 0)
  def __ge__(self, other):
    return self.convolve(other, lambda x, y: 1 if x >= y else 0)

  def __bool__(self):
    assert all(v in (0, 1) for v in self.vals)
    return len(self.vals) == 1 and self.vals[0] == 1

  def __pos__(self):
    return self
  def __neg__(self):
    return 0 - self
  def __abs__(self):
    return RV(tuple(abs(v) for v in self.vals), self.probs)
  def __round__(self, n=0):
    return RV(tuple(round(v, n) for v in self.vals), self.probs)
  def __floor__(self):
    return RV(tuple(math.floor(v) for v in self.vals), self.probs)
  def __ceil__(self):
    return RV(tuple(math.ceil(v) for v in self.vals), self.probs)
  def __trunc__(self):
    return RV(tuple(math.trunc(v) for v in self.vals), self.probs)

  def __repr__(self):
    sum_p = sum(self.probs)
    mean = self.mean()
    mean = round(mean, 1) if mean is not None else None
    std = self.std()
    std = round(std, 1) if std is not None else None
    result = f'mean: {mean} std: {std}\n'
    result += '\n'.join(f"{v}: {round(100*p/sum_p, 1)}" for v, p in zip(self.vals, self.probs))
    return result

class Seq(Iterable):
  def __init__(self, *source):
    n = list(utils.flatten(source))
    n = [x for x in n if not isinstance(x, RV)] + [v for x in n if isinstance(x, RV) for v in x.vals]  # expand RVs
    self.seq = n
    self._one_indexed = 1  # 1 is True, 0 is False
    self._sum = None

  def sum(self):
    if self._sum is None:
      self._sum = sum(self.seq)
    return self._sum

  def __repr__(self):
    return str(self.seq)
  def __iter__(self):
    return iter(self.seq)
  def __len__(self):
    return len(self.seq)
  def __getitem__(self, i):
    return self.seq[i-self._one_indexed] if 0 <= i-self._one_indexed < len(self.seq) else 0
  def  __matmul__(self, other):
    # access at indices in other
    if not isinstance(other, Seq):
      other = Seq(other)
    return sum(other[i] for i in self.seq)

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
    return self.compare_to(other, operator.eq)
  def __ne__(self, other):
    return self.compare_to(other, operator.ne)
  def __lt__(self, other):
    return self.compare_to(other, operator.lt)
  def __le__(self, other):
    return self.compare_to(other, operator.le)
  def __gt__(self, other):
    return self.compare_to(other, operator.gt)
  def __ge__(self, other):
    return self.compare_to(other, operator.ge)

  def compare_to(self, other, operation):
    if isinstance(other, RV):
      return operation(self.sum(), other)
    if isinstance(other, Iterable):
      if not isinstance(other, Seq):  # convert to Seq if not already
        other = Seq(*other)
      if operation == operator.ne: # special case for NE, since it is ∃ as opposed to ∀ like the others
        return not self.compare_to(other, operator.eq)
      return all(operation(x, y) for x, y in zip_longest(self.seq, other, fillvalue=float('-inf')))
    # if other is a number
    return sum(1 for x in self.seq if operation(x, other))


def dice(n):
  if isinstance(n, int):
    if n == 0:  # special case
      return RV([0], [1])
    return RV(list(range(1, n+1)), [1]*n)
  if isinstance(n, Iterable):
    if not isinstance(n, Seq):
      n = Seq(*n)
    return RV(n.seq, [1]*len(n))
  raise ValueError(f'cant get dice from {type(n)}')

def roll(n: int, d):
  if not isinstance(d, RV):
    d = dice(d)
  assert n >= 0
  if n == 0:
    return dice(0)
  if n == 1:
    return d
  half = roll(n//2, d)
  full = half+half
  if n%2 == 1:
    full = full + d
  return full

def d(s):
  # s is "ndm", example: "4d6"
  n, m = s.split('d')
  return roll(int(n) if n!='' else 1, dice(int(m)))

def show_summary(name, rv):
  print(name, f'{rv.mean():.0f} ± {rv.std():.0f}')

