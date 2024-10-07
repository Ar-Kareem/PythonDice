import logging
from . import myparser
from .python_resolver import PythonResolver

# logger = logging.getLogger(__name__)
def setup_logging(filename):
    logging.basicConfig(filename=filename, level=logging.DEBUG, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger().addHandler(logging.StreamHandler())
setup_logging('./log/parse_and_exec.log')

def parse(to_parse, verbose_lex=False, verbose_yacc=False):
  if to_parse is None or to_parse.strip() == '':
    logging.debug('Empty string')
    return

  myparser.lexer.input(to_parse)  # feed the lexer
  tokens = [x for x in myparser.lexer]

  for x in myparser.ILLEGAL_CHARS:
      logging.debug(f'Illegal character {x!r}')
  myparser.ILLEGAL_CHARS.clear()

  if verbose_lex:
    logging.debug('Tokens:')
    for x in tokens:
        logging.debug(x)

  yacc_ret = myparser.yacc_parser.parse(to_parse)  # generate the AST

  if yacc_ret is None:
    logging.debug('Parse failed')
    return
  if verbose_yacc:
    for x in yacc_ret:
      logging.debug('yacc: ' + str(x))
  return yacc_ret

def get_lib():
  import math, itertools, random, functools
  from randvar import RV, Seq, anydice_casting, output, roll, settings_set
  from utils import myrange
  from funclib import absolute as absolute_X, contains as X_contains_X, count_in as count_X_in_X, explode as explode_X, highest_N_of_D as highest_X_of_X, lowest_N_of_D as lowest_X_of_X, middle_N_of_D as middle_X_of_X, highest_of_N_and_N as highest_of_X_and_X, lowest_of_N_and_N as lowest_of_X_and_X, maximum_of as maximum_of_X, reverse as reverse_X, sort as sort_X
  rv_lib_dict = {
    'math': math, 'itertools': itertools, 'random': random, 'functools': functools,
    'RV': RV, 'Seq': Seq, 'anydice_casting': anydice_casting, 'roll': roll, 'myrange': myrange, 'settings_set': settings_set, 'output': output,
    'absolute_X': absolute_X, 'X_contains_X': X_contains_X, 'count_X_in_X': count_X_in_X, 'explode_X': explode_X, 'highest_X_of_X': highest_X_of_X, 'lowest_X_of_X': lowest_X_of_X, 'middle_X_of_X': middle_X_of_X, 'highest_of_X_and_X': highest_of_X_and_X, 'lowest_of_X_and_X': lowest_of_X_and_X, 'maximum_of_X': maximum_of_X, 'reverse_X': reverse_X, 'sort_X': sort_X,
  }
  return rv_lib_dict

def safe_exec(r, global_vars=None):
  import RestrictedPython as ResPy
  import RestrictedPython.Guards as Guards
  import RestrictedPython.Eval as Eval
  all_outputs = []
  g = {
    '__builtins__': ResPy.safe_builtins,
    '_getiter_': Eval.default_guarded_getiter, 
    '_iter_unpack_sequence_': Guards.guarded_iter_unpack_sequence,
    '_getattr_': getattr,

    **get_lib(),
    'output': lambda *args, **kwargs: all_outputs.append((args, kwargs)),
    **(global_vars or {})
  }
  logging.debug('Executing parsed python:')
  byte_code = ResPy.compile_restricted(
      source=r,
      filename='<inline code>',
      mode='exec'
  )
  exec(byte_code, g)
  return all_outputs

def unsafe_exec(r, global_vars=None):
  logging.warning('Unsafe exec\n'*25)
  all_outputs = []
  g = {
    **get_lib(), 
    'output': lambda *args, **kwargs: all_outputs.append((args, kwargs)),
    **(global_vars or {})}
  exec(r, g)
  return all_outputs

def pipeline(to_parse, do_exec=True, verbose_input_str=False, verbose_lex=False, verbose_yacc=False, verbose_parseed_python=False, global_vars=None, _do_unsafe_exec=False):
  if verbose_input_str:
    logging.debug(f'Parsing:\n{to_parse}')
  parsed = parse(to_parse, verbose_lex=verbose_lex, verbose_yacc=verbose_yacc)
  r = PythonResolver(parsed).resolve()
  if verbose_parseed_python:
    logging.debug(f'Parsed python:\n{r}')
  if do_exec:
    return safe_exec(r, global_vars=global_vars)
  elif _do_unsafe_exec:
    return unsafe_exec(r, global_vars=global_vars)
