import logging
from . import myparser
from .python_resolver import PythonResolver


def setup_logging(filename):
    logging.basicConfig(filename=filename, level=logging.DEBUG, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger().addHandler(logging.StreamHandler())
setup_logging('./log/example_run.log')

def parse(to_parse, verbose_lex=False, verbose_yacc=False):
  myparser.lexer.input(to_parse)
  tokens = [x for x in myparser.lexer]

  for x in myparser.ILLEGAL_CHARS:
      logging.debug(f'Illegal character {x!r}')
  myparser.ILLEGAL_CHARS.clear()

  if verbose_lex:
    logging.debug('Tokens:')
    for x in tokens:
        logging.debug(x)

  yacc_ret = myparser.yacc_parser.parse(to_parse)
  if verbose_yacc and yacc_ret:
    for x in yacc_ret:
      logging.debug('yacc: ' + str(x))
  return yacc_ret

def pipeline(to_parse, do_exec=True, verbose_input_str=False, verbose_lex=False, verbose_yacc=False, verbose_parseed_python=False):
  if to_parse is None or to_parse.strip() == '':
    logging.debug('Empty string')
    return
  if verbose_input_str:
    logging.debug(f'Parsing:\n{to_parse}')
  parsed = parse(to_parse, verbose_lex=verbose_lex, verbose_yacc=verbose_yacc)
  if parsed is None:
    logging.debug('Parse failed')
    return
  r = PythonResolver(parsed).resolve()
  if verbose_parseed_python:
    logging.debug(f'Parsed python:\n{r}')

  _import_str = 'from randvar import RV, Seq, anydice_casting, output, roll, myrange, settings_set \n'
  _import_str += 'import funclib \n'
  helper_funcs = [('absolute', 'absolute_X'), 
                  ('contains', 'X_contains_X'), 
                  ('count_in', 'count_X_in_X'), 
                  ('explode', 'explode_X'), 
                  ('highest_N_of_D', 'highest_X_of_X'), 
                  ('lowest_N_of_D', 'lowest_X_of_X'), 
                  ('middle_N_of_D', 'middle_X_of_X'), 
                  ('highest_of_N_and_N', 'highest_of_X_and_X'), 
                  ('lowest_of_N_and_N', 'lowest_of_X_and_X'), 
                  ('maximum_of', 'maximum_of_X'), 
                  ('reverse', 'reverse_X'), 
                  ('sort', 'sort_X')]
  _import_str += '\n'.join(f'from funclib import {k} as {v}' for k,v in helper_funcs)
  if do_exec:
    g = {}
    exec(_import_str, g, g)
    logging.debug('Executing parsed python:')
    exec(r, g, g)


