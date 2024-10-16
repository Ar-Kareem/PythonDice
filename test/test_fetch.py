from typing import Sequence
import pytest
import logging
import json
from pathlib import Path
import copy

from src.randvar import RV, Seq
from src.parser import parse_and_exec


logger = logging.getLogger(__name__)

TO_EXCLUDE = set(['testing_not_on_int'])  # TODO: remove this when implemented
COMP_EPS = 1e-5

data = json.loads((Path(__file__).parent / 'autoouts' / 'fetch_out.json').read_text())['data']
code_resp_pairs = [(x['inp'], x['out']) for x in data if x.get('name', None) not in TO_EXCLUDE]


class cust_np_array:
  def __init__(self, x):
    self.x = x
    self.shape = []
    _s = x
    while isinstance(_s, Sequence):
      self.shape.append(len(_s))
      _s = _s[0]
  def __add__(self, other: float):  # dummy add just to fudge single element
    x = copy.deepcopy(self.x)
    _s = x
    for i in range(len(self.shape)-1):
      _s = _s[0]
    _s[0] += other
    return cust_np_array(x)

def all_close(a: cust_np_array, b: cust_np_array, atol):
  assert len(a.shape) == len(b.shape), f'{a.shape}, {b.shape}'
  assert a.shape == b.shape, f'{a.shape}, {b.shape}'
  return sum_diff_iterable(a.x, b.x) < atol
def sum_diff_iterable(a: Sequence, b: Sequence):
  tot = 0
  for x, y in zip(a, b):
    if isinstance(x, Sequence) and isinstance(y, Sequence):
      tot += sum_diff_iterable(x, y)
    elif isinstance(x, (int, float)) and isinstance(y, (int, float)):
      tot += abs(x - y)
    else:
      assert False, f'UNKNOWN PARAMS! x: {x}, y: {y}'
  return tot

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
  cust_x = cust_np_array(x)
  cust_expected = cust_np_array(expected)
  assert cust_x.shape == cust_expected.shape, f'A: {x}, B: {expected}'
  assert not all_close(cust_x, cust_expected+0.01, atol=COMP_EPS), f'How is allcose true here???'
  assert all_close(cust_x, cust_expected, atol=COMP_EPS), f'A: {x}, B: {expected} diff: {sum_diff_iterable(x, expected)}'
  # for a, b in zip(x, expected):
    # assert all_close(a, b, atol=COMP_EPS), f'A and B: {a}, {b} np diff: {np.abs(np.array(a) - np.array(b))}'


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