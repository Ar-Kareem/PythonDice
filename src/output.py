from typing import Union, Iterable

from .typings import T_isr
from .settings import SETTINGS
from . import randvar
from . import seq
from . import blackrv


def output(rv: Union[T_isr, None], named=None, show_pdf=True, blocks_width=None, print_=True, print_fn=None, cdf_cut=0):
  if isinstance(rv, seq.Seq) and len(rv) == 0:  # empty sequence plotted as empty
    rv = blackrv.BlankRV()
  if isinstance(rv, int) or isinstance(rv, Iterable) or isinstance(rv, bool):
    rv = randvar.RV.from_seq([rv])
  if blocks_width is None:
    blocks_width = SETTINGS['DEFAULT_OUTPUT_WIDTH']

  result = ''
  if named is not None:
    result += named + ' '

  if rv is None or isinstance(rv, blackrv.BlankRV):
    result += '\n' + '-' * (blocks_width + 8)
    if print_:
      if print_fn is None:
        SETTINGS['DEFAULT_PRINT_FN'](result)
      else:
        print_fn(result)
      return
    else:
      return result
  assert isinstance(rv, randvar.RV), f'rv must be a RV {rv}'

  try:
    mean = rv.mean()
    mean = round(mean, 2) if mean is not None else None
    std = rv.std()
    std = round(std, 2) if std is not None else None
    result += f'{mean} ± {std}'
  except Exception:
    result += 'NaN ± NaN'

  if show_pdf:
    vp = rv.get_vals_probs(cdf_cut / 100)
    max_val_len = max(len(str(v)) for v, _ in vp)
    blocks = max(0, blocks_width - max_val_len)
    for v, p in vp:
      result += '\n' + f"{v:>{max_val_len}}: {100 * p:>5.2f}  " + ('█' * round(p * blocks))
    result += '\n' + '-' * (blocks_width + 8)
  if print_:
    if print_fn is None:
      SETTINGS['DEFAULT_PRINT_FN'](result)
    else:
      print_fn(result)
    return
  else:
    return result
