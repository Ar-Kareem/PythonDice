from typing import Iterable, Callable, Optional, Union
from itertools import zip_longest
import operator

from .typings import T_if, T_ifs, T_ifsr, MetaRV, MetaSeq
from . import utils
from . import factory


class Seq(Iterable, MetaSeq):
  def __init__(self, *source: T_ifsr, _INTERNAL_SEQ_VALUE: Optional[tuple[T_if, ...]] = None):
    self._sum = None
    self._one_indexed = 1
    if _INTERNAL_SEQ_VALUE is not None:  # used for internal optimization only
      self._seq: tuple[T_if, ...] = _INTERNAL_SEQ_VALUE
      return
    flat = tuple(utils.flatten(source))
    flat_rvs = [x for x in flat if factory.is_rv(x)]  # expand RVs
    flat_rv_vals = [v for rv in flat_rvs for v in rv.vals]
    flat_else: list[T_if] = [x for x in flat if not isinstance(x, MetaRV)]
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
    if isinstance(other, MetaRV):  # ( self:SEQ @ other:RV ) thus RV takes priority
      return other.__rmatmul__(self)
    # access at indices in other ( self @ other )
    if isinstance(other, (int, float)):
      other = Seq([int(d) for d in str(other)])  # SEQ @ int  thus convert int to sequence using base 10
    if not isinstance(other, Seq):
      other = Seq(other)
    assert all(isinstance(i, int) for i in self._seq), 'indices must be integers'
    return sum(other[int(i)] for i in self._seq)

  def __rmatmul__(self, other: T_ifs):
    if isinstance(other, MetaRV):  # ( other:RV @ self:SEQ ) thus not allowed,
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

  def _compare_to(self, other: T_ifsr, operation: Callable[[float, Union[T_if, MetaRV]], bool]):
    if isinstance(other, MetaRV):
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
    assert not isinstance(s1, MetaRV) and not isinstance(s2, MetaRV), 'cannot compare Seq with RV'
    if not isinstance(s1, Seq):
      s1 = Seq(s1)
    if not isinstance(s2, Seq):
      s2 = Seq(s2)
    return s1._seq == s2._seq
