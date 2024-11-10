import logging
from . import myparser
from .myparser import Node
from .python_resolver import PythonResolver


logger = logging.getLogger(__name__)


def build_lex_yacc(debug=False):
  lexer, yaccer = myparser.build_lex_yacc(debug=debug)
  lexer.LEX_ILLEGAL_CHARS = []
  lexer.YACC_ILLEGALs = []
  return lexer, yaccer


def do_lex(to_parse, lexer, verbose_lex=False):
  lexer.input(to_parse)  # feed the lexer
  tokens = [x for x in lexer]
  if verbose_lex:
    logger.debug('Tokens:')
    for x in tokens:
        logger.debug(x)


def do_yacc(to_parse, lexer, yaccer, verbose_yacc=False):
  yacc_ret: Node = yaccer.parse(to_parse, lexer=lexer)  # generate the AST
  if verbose_yacc and yacc_ret:
    for x in yacc_ret:
      logger.debug('yacc: ' + str(x))
  return yacc_ret


def do_resolve(yacc_ret, verbose_parseed_python=False, flags=None):
  r = PythonResolver(yacc_ret, flags=flags)
  r.resolve()
  r = r.get_text()
  if verbose_parseed_python:
    logger.debug(f'Parsed python:\n{r}')
  return r


def _get_lib():
  import math
  import itertools
  import random
  import functools
  from ..typings import T_N, T_S, T_D
  from ..randvar import RV
  from ..seq import Seq
  from ..factory import get_seq
  from ..settings import settings_set
  from ..decorators import anydice_casting
  from ..output import output
  from ..roller import roll, myrange
  from ..utils import mymatmul as myMatmul, mylen as myLen, myinvert as myInvert, myand as myAnd, myor as myOr, true_div as true_div_X_X
  from ..funclib import absolute as absolute_X, contains as X_contains_X, count_in as count_X_in_X, explode as explode_X, highest_N_of_D as highest_X_of_X
  from ..funclib import lowest_N_of_D as lowest_X_of_X, middle_N_of_D as middle_X_of_X, highest_of_N_and_N as highest_of_X_and_X, lowest_of_N_and_N as lowest_of_X_and_X
  from ..funclib import maximum_of as maximum_of_X, reverse as reverse_X, sort as sort_X
  rv_lib_dict = {
    # useful modules
    'math': math, 'itertools': itertools, 'random': random, 'functools': functools,
    # core
    'RV': RV, 'Seq': Seq, 'get_seq': get_seq, 'anydice_casting': anydice_casting, 'roll': roll, 'myrange': myrange, 'settings_set': settings_set, 'output': output,
    # typings
    'T_N': T_N, 'T_S': T_S, 'T_D': T_D,
    # funclib
    'absolute_X': absolute_X, 'X_contains_X': X_contains_X, 'count_X_in_X': count_X_in_X, 'explode_X': explode_X, 'highest_X_of_X': highest_X_of_X,
    'lowest_X_of_X': lowest_X_of_X, 'middle_X_of_X': middle_X_of_X, 'highest_of_X_and_X': highest_of_X_and_X, 'lowest_of_X_and_X': lowest_of_X_and_X,
    'maximum_of_X': maximum_of_X, 'reverse_X': reverse_X, 'sort_X': sort_X,
    # utils
    'myMatmul': myMatmul, 'myLen': myLen, 'myInvert': myInvert, 'myAnd': myAnd, 'myOr': myOr, 'true_div_X_X': true_div_X_X
  }
  return rv_lib_dict


def compile_anydice(to_parse, flags=None):
  assert to_parse is not None and to_parse.strip() != '', 'Empty input'
  lexer, yaccer = build_lex_yacc()
  do_lex(to_parse, lexer)
  assert not lexer.LEX_ILLEGAL_CHARS, 'Lex Illegal characters found: ' + str(lexer.LEX_ILLEGAL_CHARS)
  yacc_ret = do_yacc(to_parse, lexer, yaccer)
  assert not lexer.YACC_ILLEGALs and yacc_ret is not None, 'Yacc Illegal tokens found: ' + str(lexer.YACC_ILLEGALs)
  python_str = do_resolve(yacc_ret, flags=flags)
  return python_str


def safe_exec(r, global_vars=None):
  try:
    import RestrictedPython
  except ModuleNotFoundError:
      logger.error('RestrictedPython not installer. Run `pip install RestrictedPython`')
      logger.exception('code did not execute')
      return []
  import RestrictedPython as ResPy
  import RestrictedPython.Guards as Guards
  import RestrictedPython.Eval as Eval
  all_outputs = []
  g = {
    '__builtins__': ResPy.safe_builtins,
    '_getiter_': Eval.default_guarded_getiter,
    '_iter_unpack_sequence_': Guards.guarded_iter_unpack_sequence,
    # '_getattr_': getattr,
    'getattr': Guards.safer_getattr,

    # To use classes in Python 3
    #     __metaclass__ must be set. Set it to type to use no custom metaclass.
    #     __name__ must be set. As classes need a namespace to be defined in. It is the name of the module the class is defined in. You might set it to an arbitrary string.
    '__metaclass__': type,
    '__name__': 'restricted namespace',
    # needed to assign to lists and dicts
    '_write_': Guards.full_write_guard,

    '_getiter_ ': Eval.default_guarded_getiter,
    '_getitem_': Eval.default_guarded_getitem,


    **_get_lib(),
    'output': lambda *args, **kwargs: all_outputs.append((args, kwargs)),
    **(global_vars or {})
  }
  byte_code = ResPy.compile_restricted(
    source=r,
    filename='<inline code>',
    mode='exec'
  )
  exec(byte_code, g)
  return all_outputs


def unsafe_exec(r, global_vars=None):
  # logger.warning('Unsafe exec\n'*25)
  all_outputs = []
  g = {
    **_get_lib(),
    'output': lambda *args, **kwargs: all_outputs.append((args, kwargs)),
    **(global_vars or {})}
  exec(r, g)
  return all_outputs
