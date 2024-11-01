import inspect
import logging
import math
from itertools import product
from typing import Iterable, Union

from .typings import T_ifsr
from . import randvar as rv
from . import blackrv


logger = logging.getLogger(__name__)


def anydice_casting(verbose=False):  # noqa: C901
  # verbose = True
  # in the documenation of the anydice language https://anydice.com/docs/functions
  # it states that "The behavior of a function depends on what type of value it expects and what type of value it actually receives."
  # Thus there are 9 scenarios for each parameters
  # expect: int, actual: int  =  no change
  # expect: int, actual: seq  =  seq.sum()
  # expect: int, actual: rv   =  MUST CALL FUNCTION WITH EACH VALUE OF RV ("If a die is provided, then the function will be invoked for all numbers on the die – or the sums of a collection of dice – and the result will be a new die.")
  # expect: seq, actual: int  =  [int]
  # expect: seq, actual: seq  =  no change
  # expect: seq, actual: rv   =  MUST CALL FUNCTION WITH SEQUENCE OF EVERY ROLL OF THE RV ("If Expecting a sequence and dice are provided, then the function will be invoked for all possible sequences that can be made by rolling those dice. In that case the result will be a new die.")  # noqa: E501
  # expect: rv, actual: int   =  dice([int])
  # expect: rv, actual: seq   =  dice(seq)
  # expect: rv, actual: rv    =  no change
  def decorator(func):
    def wrapper(*args, **kwargs):
      args, kwargs = list(args), dict(kwargs)
      fullspec = inspect.getfullargspec(func)
      arg_names = fullspec.args  # list of arg names  for args (not kwargs)
      param_annotations = fullspec.annotations  # (arg_names): (arg_type)  that have been annotated

      hard_params = {}  # update parameters that are easy to update, keep the hard ones for later
      combined_args = list(enumerate(args)) + list(kwargs.items())
      if verbose:
        logger.debug(f'#args {len(combined_args)}')
      for k, arg_val in combined_args:
        arg_name = k if isinstance(k, str) else (arg_names[k] if k < len(arg_names) else None)  # get the name of the parameter (args or kwargs)
        if arg_name not in param_annotations:  # only look for annotated parameters
          if verbose:
            logger.debug(f'no anot {k}')
          continue
        expected_type = param_annotations[arg_name]
        actual_type = type(arg_val)
        new_val = None
        if expected_type not in (int, rv.Seq, rv.RV):
          if verbose:
            logger.debug(f'not int seq rv {k}')
          continue
        if isinstance(arg_val, blackrv.BlankRV):  # EDGE CASE abort calling if casting int/Seq to BlankRV  (https://github.com/Ar-Kareem/PythonDice/issues/11)
          if expected_type in (int, rv.Seq):
            if verbose:
              logger.debug(f'abort calling func due to BlankRV! {k}')
            return blackrv.BlankRV(_special_null=True)
          continue  # casting BlankRV to RV means the function IS called and nothing changes
        casted_iter_to_seq = False
        if isinstance(arg_val, Iterable) and not isinstance(arg_val, rv.Seq):  # if val is iter then need to convert to Seq
          arg_val = rv.Seq(*arg_val)
          new_val = arg_val
          actual_type = rv.Seq
          casted_iter_to_seq = True
        if (expected_type, actual_type) == (int, rv.Seq):
          new_val = arg_val.sum()
        elif (expected_type, actual_type) == (int, rv.RV):
          hard_params[k] = (arg_val, expected_type)
          continue
        elif (expected_type, actual_type) == (rv.Seq, int):
          new_val = rv.Seq([arg_val])
        elif (expected_type, actual_type) == (rv.Seq, rv.RV):
          hard_params[k] = (arg_val, expected_type)
          if verbose:
            logger.debug(f'EXPL {k}')
          continue
        elif (expected_type, actual_type) == (rv.RV, int):
          new_val = rv.RV.from_const(arg_val)  # type: ignore
        elif (expected_type, actual_type) == (rv.RV, rv.Seq):
          new_val = rv.RV.from_seq(arg_val)
        elif not casted_iter_to_seq:  # no cast made and one of the two types is not known, no casting needed
          if verbose:
            logger.debug(f'no cast, {k}, {expected_type}, {actual_type}')
          continue
        if isinstance(k, str):
          kwargs[k] = new_val
        else:
          args[k] = new_val
        if verbose:
          logger.debug('cast {k}')
      if verbose:
        logger.debug(f'hard {[(k, v[1]) for k, v in hard_params.items()]}')
      if not hard_params:
        return func(*args, **kwargs)

      var_name = tuple(hard_params.keys())
      all_rolls_and_probs = []
      for k in var_name:
        v, expected_type = hard_params[k]
        assert isinstance(v, rv.RV), 'expected type RV'
        if expected_type == rv.Seq:
          r, p = v._get_expanded_possible_rolls()
        elif expected_type == int:
          r, p = v.vals, v.probs
        else:
          raise ValueError(f'casting RV to {expected_type} not supported')
        all_rolls_and_probs.append(zip(r, p))
      # FINALLY take product of all possible rolls
      all_rolls_and_probs = product(*all_rolls_and_probs)

      res_vals: list[Union[rv.RV, blackrv.BlankRV, rv.Seq, int, float, None]] = []
      res_probs: list[int] = []
      for rolls_and_prob in all_rolls_and_probs:
        rolls = tuple(r for r, _ in rolls_and_prob)
        prob = math.prod(p for _, p in rolls_and_prob)
        # will update args and kwargs with each possible roll using var_name
        for k, v in zip(var_name, rolls):
          if isinstance(k, str):
            kwargs[k] = v
          else:
            args[k] = v
        val: T_ifsr = func(*args, **kwargs)  # single result of the function call
        if isinstance(val, Iterable):
          if not isinstance(val, rv.Seq):
            val = rv.Seq(*val)
          val = val.sum()
        if verbose:
          logger.debug(f'val {val} prob {prob}')
        res_vals.append(val)
        res_probs.append(prob)
      return rv.RV.from_rvs(rvs=res_vals, weights=res_probs)
    return wrapper
  return decorator


def max_func_depth():
  # decorator to limit the depth of the function calls
  def decorator(func):
    def wrapper(*args, **kwargs):
      if rv.SETTINGS['INTERNAL_CURR_DEPTH'] >= rv.SETTINGS['maximum function depth']:
        msg = 'The maximum function depth was exceeded, results are truncated.'
        if not rv.SETTINGS['INTERNAL_CURR_DEPTH_WARNING_PRINTED']:
          logger.warning(msg)
          print(msg)
          rv.SETTINGS['INTERNAL_CURR_DEPTH_WARNING_PRINTED'] = True
        return blackrv.BlankRV()
      rv.SETTINGS['INTERNAL_CURR_DEPTH'] += 1
      res = func(*args, **kwargs)
      rv.SETTINGS['INTERNAL_CURR_DEPTH'] -= 1
      return res if res is not None else blackrv.BlankRV()
    return wrapper
  return decorator