import pytest
import logging
import json
from pathlib import Path
import numpy as np

from src.randvar import RV, Seq
from src.parser import parse_and_exec


logger = logging.getLogger(__name__)

COMP_EPS = 1e-10

data = json.loads((Path(__file__).parent / 'fetch_out.json').read_text())['data']
code_resp_pairs = [(x['inp'], x['out']) for x in data]


def pipeline(to_parse, global_vars={}):
  if to_parse is None or to_parse.strip() == '':
    logger.debug('Empty string')
    return
  lexer, yaccer = parse_and_exec.build_lex_yacc()
  parse_and_exec.do_lex(to_parse, lexer)
  if lexer.LEX_ILLEGAL_CHARS:
    logger.debug('Lex Illegal characters found: ' + str(lexer.LEX_ILLEGAL_CHARS))
    return
  yacc_ret = parse_and_exec.do_yacc(to_parse, lexer, yaccer)
  if lexer.YACC_ILLEGALs:
    logger.debug('Yacc Illegal tokens found: ' + str(lexer.YACC_ILLEGALs))
    return
  python_str = parse_and_exec.do_resolve(yacc_ret)
  r = parse_and_exec.safe_exec(python_str, global_vars=global_vars)
  return r

def check(inp: RV|Seq|int, expected):
  # clear (null, null) from expected
  expected = [x for x in expected if x != [None, None]]
  # assert not expected, expected
  if not isinstance(inp, RV):
    inp = RV.from_seq([inp])
  x = [[v, p*100] for v, p in inp.get_vals_probs()]
  x = np.array(x)
  expected = np.array(expected)
  assert len(x) == len(expected), f'A: {x}, B: {expected}'
  assert x.shape == expected.shape, f'A: {x}, B: {expected}'
  assert not np.allclose(x, expected+0.001, atol=COMP_EPS), f'How is allcose true here???'
  assert np.allclose(x, expected, atol=COMP_EPS), f'A: {x}, B: {expected} np diff: {np.abs(x - expected)}'
  # for a, b in zip(x, expected):
    # assert np.allclose(a, b, atol=COMP_EPS), f'A and B: {a}, {b} np diff: {np.abs(np.array(a) - np.array(b))}'


@pytest.mark.parametrize("inp_code,anydice_resp", code_resp_pairs)
def test_all_fetch(inp_code,anydice_resp):
  anydice_resp = json.loads(anydice_resp)
  i = 0
  def check_res(x, named):
    nonlocal i
    assert named is None or named == anydice_resp['distributions']['labels'][i]
    check(x, anydice_resp['distributions']['data'][i])
    i += 1

  pipeline(inp_code, global_vars={'output': lambda x, named=None: check_res(x, named)})
  # assert False, f'inp_code: {inp_code}, anydice_resp: {anydice_resp}'
