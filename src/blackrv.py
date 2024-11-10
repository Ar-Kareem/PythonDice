# TODO rename file to blankrv.py
from typing import Iterable

from .typings import T_ifs, T_ifsr, MetaRV
from . import factory
from . import output


class BlankRV(MetaRV):
  def __init__(self, _special_null=False):
    self._special_null = _special_null  # makes it such that it's _special_null,  in operations like (X**2 + 1) still is blank (X). see https://anydice.com/program/395da

  def mean(self):
    return 0

  def std(self):
    return 0

  def output(self, *args, **kwargs):
    return output.output(self, *args, **kwargs)

  def __matmul__(self, other: T_ifs):
    # ( self:RV @ other ) thus not allowed,
    raise TypeError(f'A position selector must be either a number or a sequence, but you provided "{other}"')

  def __rmatmul__(self, other):
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
      other = factory.get_seq(*other).sum()
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
    return output.output(self, print_=False)
