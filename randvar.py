import operator
import math
from typing import Sequence, Iterable
import utils

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
    return sum(v*p for v, p in zip(self.vals, self.probs)) / sum_p
  def std(self):
    mean = self.mean()
    mean_X2 = RV(tuple(v**2 for v in self.vals), self.probs).mean()
    var = mean_X2 - mean**2
    return math.sqrt(var)
  def convolve(self, other, operation):
    if not isinstance(other, RV):
      return RV([operation(v, other) for v in self.vals], self.probs)
    new_vals = tuple(operation(v1, v2) for v1 in self.vals for v2 in other.vals)
    new_probs = tuple(p1*p2 for p1 in self.probs for p2 in other.probs)
    return RV(new_vals, new_probs)
  def rconvolve(self, other, operation):
    assert not isinstance(other, RV)
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
    result = f'mean: {self.mean():.2f} std: {self.std():.2f} \n'
    result += '\n'.join(f"{v}: {round(100*p/sum_p, 2)}" for v, p in zip(self.vals, self.probs))
    return result


def dice(n):
  if isinstance(n, int):
    if n == 0:  # special case
      return RV([0], [1])
    return RV(list(range(1, n+1)), [1]*n)
  if isinstance(n, Iterable):
    n = list(utils.flatten(n))
    n = [x for x in n if not isinstance(x, RV)] + [v for x in n if isinstance(x, RV) for v in x.vals]
    return RV(n, [1]*len(n))
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

