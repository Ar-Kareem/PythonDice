from typing import Iterable, Union

from .typings import T_if, T_ifsr, MetaRV, MetaSeq
from . import utils
from . import seq
from . import string_rvs
from . import randvar
from . import blackrv

T_ifsrt_single = Union[T_ifsr, str]
T_ifsrt = Union[T_ifsrt_single, Iterable['T_ifsrt']]


def get_seq(*source: T_ifsrt, _INTERNAL_SEQ_VALUE=None) -> 'seq.Seq':
  if _INTERNAL_SEQ_VALUE is not None:  # used for internal optimization only
    return seq.Seq(_INTERNAL_SEQ_VALUE=_INTERNAL_SEQ_VALUE)
  # check if string in values, if so, return StringSeq
  flat = tuple(utils.flatten(source))
  flat_rvs = [x for x in flat if isinstance(x, MetaRV) and not isinstance(x, blackrv.BlankRV)]  # expand RVs
  flat_rv_vals = [v for rv in flat_rvs for v in rv.vals]
  flat_else: list[T_if] = [x for x in flat if not isinstance(x, MetaRV)]
  res = tuple(flat_else + flat_rv_vals)
  if any(isinstance(x, (str, string_rvs.StringVal)) for x in res):
    return string_rvs.StringSeq(res)
  assert all(isinstance(x, (int, float)) for x in res), 'Seq must be made of numbers and RVs. Seq:' + str(res)
  return seq.Seq(_INTERNAL_SEQ_VALUE=res)


def get_rv(source: T_ifsr) -> 'randvar.RV':
  if isinstance(source, (int, float, bool)):
    source = randvar.RV.from_const(source)
  elif isinstance(source, Iterable):
    source = randvar.RV.from_seq(source)
  assert isinstance(source, randvar.RV), f'source must be a RV {source}'
  return source


def merge_rvs(rvs: Iterable[Union['int', 'float', MetaRV, MetaSeq, None]], weights: Union[Iterable[int], None] = None) -> MetaRV:
  return randvar.RV.from_rvs(rvs=rvs, weights=weights)


def is_blank_rv(rv) -> bool:
  return isinstance(rv, blackrv.BlankRV)


def is_rv(rv) -> bool:
  return isinstance(rv, randvar.RV)
