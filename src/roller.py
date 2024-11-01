from typing import Union, Iterable
import random

from .randvar import RV
from .typings import T_isr


def roller(rv: T_isr, count: Union[int, None] = None):
  if isinstance(rv, int) or isinstance(rv, Iterable) or isinstance(rv, bool):
    rv = RV.from_seq([rv])
  assert isinstance(rv, RV), 'rv must be a RV'
  # roll using random.choices
  if count is None:
    return random.choices(rv.vals, rv.probs)[0]
  return tuple(random.choices(rv.vals, rv.probs)[0] for _ in range(count))
