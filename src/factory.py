from typing import Union, TYPE_CHECKING

from .typings import T_if, T_ifsr, MetaRV
from . import utils
from . import seq
from . import string_rvs
from . import blackrv

T_ifsrt = Union[T_ifsr, str]


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
