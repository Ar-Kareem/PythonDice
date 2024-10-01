
from typing import Iterable

from randvar import Seq, RV, roll

class __D_BASE:
  def __mul__(self, other):
    return roll(other)
  def __rmul__(self, other):
    return self.D_WITH_LEFT(left=other)

  class D_WITH_LEFT:
    def __init__(self, left):
      self.left = left
    def __mul__(self, other):
      return roll(self.left, other)
D = __D_BASE()

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

def d(s):
  #    s is "ndm", example: "4d6"
  # or s is "dm", example: "d6"
  s = s.split('d')
  if s[0] == '':
    return roll(1, int(s[1]))
  return roll(int(s[0]), int(s[1]))
