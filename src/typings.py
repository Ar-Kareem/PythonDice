from typing import Iterable, Iterator, Union, TypeVar, TYPE_CHECKING
from abc import ABC


# TYPE DEFINITIONS
T_if = Union[int, float]
T_ifs = Union[T_if, Iterable['T_ifs']]  # recursive type
T_is = Union[int, Iterable['T_is']]  # recursive type

T_isr = Union[T_is, 'MetaRV']
T_ifr = Union[T_if, 'MetaRV']
T_ifsr = Union[T_ifs, 'MetaRV']

T_s = Iterable['T_ifs']  # same as T_ifs but excludes int and float (not iterable)

# define T_N, T_S, T_D to be unique types used in casting
if TYPE_CHECKING:
  from .randvar import RV
  from .seq import Seq
  T_N = int
  T_S = Seq
  T_D = RV
else:
  T_N = TypeVar('T_N')
  T_S = TypeVar('T_S')
  T_D = TypeVar('T_D')


class MetaRV(ABC):
  vals: tuple[float, ...]
  probs: tuple[int, ...]

  def _get_expanded_possible_rolls(self):
    raise NotImplementedError

  def __neg__(self):
      raise NotImplementedError

  def __lt__(self, other: T_ifsr):
    raise NotImplementedError

  def __le__(self, other: T_ifsr):
    raise NotImplementedError

  def __gt__(self, other: T_ifsr):
    raise NotImplementedError

  def __ge__(self, other: T_ifsr):
    raise NotImplementedError

  def __rmatmul__(self, other: T_is):
    raise NotImplementedError


class MetaSeq(ABC):
  _seq: tuple[T_if, ...]

  def sum(self):
    raise NotImplementedError

  def __len__(self):
    raise NotImplementedError

  def __getitem__(self, i: int) -> T_if:
    raise NotImplementedError

  def __iter__(self) -> Iterator[T_if]:
    raise NotImplementedError
