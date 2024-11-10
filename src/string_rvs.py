
from typing import Union
import operator as op

from .typings import MetaStr, T_if
from . import seq

T_ift = Union[T_if, str, 'StringVal']


_CONST_COEF = '_UNIQUE_STRING'


class StringVal(MetaStr):
  def __init__(self, keys: tuple[str, ...], pairs: dict[str, T_if]):
    self.keys = tuple(sorted(keys))
    self.data = pairs

  @staticmethod
  def from_const(const: T_if):
    return StringVal((_CONST_COEF, ), {_CONST_COEF: const})

  @staticmethod
  def from_str(s: str):
    return StringVal((s, ), {s: 1})

  @staticmethod
  def from_paris(pairs: dict[str, T_if]):  # TODO rename to from_pairs
    return StringVal(tuple(pairs.keys()), pairs)

  def is_number(self):
    import re  # noqa
    return len(self.keys) == 1 and re.match(r'^-?\d+(\.\d+)?$', self.keys[0])

  def __add__(self, other):
    if not isinstance(other, StringVal):
      other = StringVal.from_const(other)
    newdict = self.data.copy()
    for key, val in other.data.items():
      newdict[key] = newdict.get(key, 0) + val
    return StringVal.from_paris(newdict)

  def __radd__(self, other):
    return self.__add__(other)

  def __repr__(self):
    r = []
    last_coeff = ''
    for key in self.keys:
      if key == _CONST_COEF:  # empty string represents a number
        last_coeff = ' + ' + str(self.data[key])
        continue
      elif self.data[key] == 1:  # coefficient 1 is not shown
        n = key
      else:
        n = f'{self.data[key]}*{key}'
      r.append(n)
    return ' + '.join(r) + last_coeff

  def __format__(self, format_spec):
    return f'{repr(self):{format_spec}}'

  def __le__(self, other):
    return self._compare_to(other, op.le)

  def __lt__(self, other):
    return self._compare_to(other, op.lt)

  def __ge__(self, other):
    return self._compare_to(other, op.ge)

  def __gt__(self, other):
    return self._compare_to(other, op.gt)

  def __eq__(self, other):
    if isinstance(other, StringVal):
      return self.keys == other.keys and self.data == other.data
    else:
      return False

  def __ne__(self, other):
    if isinstance(other, StringVal):
      return self.keys != other.keys or self.data != other.data
    else:
      return True

  def _compare_to(self, other, operator):
    if isinstance(other, StringVal):
      i = 0
      while True:
        if i >= len(self.keys) or i >= len(other.keys):
          return operator(len(self.keys), len(other.keys))
        if self.keys[i] != other.keys[i]:
          return operator(self.keys[i], other.keys[i])
        if self.data[self.keys[i]] != other.data[other.keys[i]]:
          return operator(self.data[self.keys[i]], other.data[other.keys[i]])
        i += 1
    else:
      return operator(float('inf'), other)

  def __hash__(self):
    return hash((self.keys, tuple(self.data)))


class StringSeq(seq.Seq):
  def __init__(self, source: tuple[T_ift, ...]):
    # do not call super().__init__ here
    source_lst: list[T_ift] = list(source)
    for i, x in enumerate(source_lst):
      if isinstance(x, str):
        source_lst[i] = StringVal.from_str(x)
    self._seq: tuple[T_ift, ...] = tuple(source_lst)

  def __iter__(self):
    return iter(self._seq)
