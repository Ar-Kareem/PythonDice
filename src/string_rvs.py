
from typing import Union

from .typings import T_if, T_ifsr
from . import randvar
from . import blackrv
from .seq import Seq
from . import utils

T_ift = Union[T_if, str]


class VarString:
  def __init__(self, strings, values=None):
    if isinstance(strings, list):
      if values is None:
        values = [1]*len(strings)
      self.data: dict[str, int] = {strings[i]: values[i] for i in range(len(strings))}
    elif isinstance(strings, dict):
      self.data = strings
    else:
      raise ValueError('strings must be a list or dict')

  def __add__(self, other):
    if isinstance(other, VarString):
      newdict = self.data.copy()
      for key, val in other.data.items():
        newdict[key] = newdict.get(key, 0) + val
      return VarString(newdict)
    else:
      return NotImplemented

  def __repr__(self):
    return str(self.data)


class StringSeq(Seq):
  def __init__(self, source: tuple[T_ift, ...]):
    # do not call super().__init__ here
    self._seq: tuple[T_ift, ...] = source

  def to_varstring(self):
    return VarString(self._seq)
