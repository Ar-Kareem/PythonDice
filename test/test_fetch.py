from typing import Sequence, Union
import pytest
import logging
import json
from pathlib import Path
import copy

import dice_calc.randvar
from dice_calc import RV, Seq, settings_reset, BlankRV
from dice_calc.parser import parse_and_exec


logger = logging.getLogger(__name__)

glob_json = json.loads((Path(__file__).parent / 'glob_test_skip.json').read_text())
remove_zero_probs_in_online_response = glob_json.get('global_flags', {}).get('remove_zero_probs_in_online_response', False)
SKIP_VERSION = glob_json['tests']
COMP_EPS = 1e-5

# specify test names below and run:    python -m pytest test/test_fetch.py -k test_cherrypick --log-cli-level=DEBUG --capture=tee-sys
CHERRYPICK = set([])

data = json.loads((Path(__file__).parent / 'autoouts' / 'fetch_out.json').read_text())['data']
code_resp_pairs = [(x['inp'], x['out'], x.get('name', None)) for x in data]


class cust_np_array:
  def __init__(self, x):
    self.x = x
    self.shape = []
    _s = x
    while isinstance(_s, Sequence):
      self.shape.append(len(_s))
      if len(_s) == 0:
        break
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

def pipeline(to_parse, version, global_vars={}):
  if version == 1:  # regular
    flags = None
  elif version == 2:  # the very ugly local scope fix
    flags = {'COMPILER_FLAG_NON_LOCAL_SCOPE': True, 'COMPILER_FLAG_OPERATOR_ON_INT': True}
  else:
    assert False, f'Unknown version {version}'
  # logger.warning(f'Parsing:\n{to_parse}')
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
  python_str = parse_and_exec.do_resolve(yacc_ret, flags=flags)
  logger.warning('\n'.join(f'{i+1}: {x}' for i, x in enumerate(python_str.split('\n'))))
  r = parse_and_exec.safe_exec(python_str, global_vars=global_vars)
  return r

def check(inp: Union[RV, Seq, int], expected, i):
  if remove_zero_probs_in_online_response:  # remove zero prob values from expected
    expected = [x for x in expected if x[1] != 0]
  if isinstance(inp, BlankRV) and expected == []:  # outputting blank gives nothing
    return
  # if inp is None and expected == []:  # outputting None gives nothing
  #   return
  if isinstance(inp, Seq) and len(inp) == 0 and expected == []:  # outputting emtpy seq gives nothing
    return
  logger.warning(f'Checking {inp} against {expected}')
  # clear (null, null) from expected
  expected = [x for x in expected if x != [None, None]]
  # assert not expected, expected
  if not isinstance(inp, RV):
    inp = RV.from_seq([inp])
  x = [[v, p*100] for v, p in inp.get_vals_probs()]
  cust_x = cust_np_array(x)
  cust_expected = cust_np_array(expected)
  assert cust_x.shape == cust_expected.shape, f'i:{i}|shape mismatch | shpaes A: {cust_x.shape}, B: {cust_expected.shape} | A: {x}, B: {expected}'
  assert not all_close(cust_x, cust_expected+0.01, atol=COMP_EPS), f'How is allcose true here???'
  assert all_close(cust_x, cust_expected, atol=COMP_EPS), f'i:{i}|diff: {sum_diff_iterable(x, expected)}|ME: {x}, ONLINE: {expected}'
  # for a, b in zip(x, expected):
    # assert all_close(a, b, atol=COMP_EPS), f'A and B: {a}, {b} np diff: {np.abs(np.array(a) - np.array(b))}'






@pytest.fixture(autouse=True)
def fixture_settings_reset():
    settings_reset()
    dice_calc.roller._MEMOIZED_ROLLS = {}


@pytest.mark.parametrize("i", range(len(code_resp_pairs)))
def test_all_fetch_v1(i):
  inp_code,anydice_resp,name = code_resp_pairs[i]
  logger.warning(f'Running test {name}: {inp_code} {anydice_resp}')
  v_to_skip = SKIP_VERSION.get(name, {}).get('flags', [])
  if 'v1' in v_to_skip or 'all' in v_to_skip:
    pytest.skip(f'Skipping {name} for v1')
  anydice_resp = json.loads(anydice_resp)
  i = 0
  def check_res(x, named):
    nonlocal i
    assert i < len(anydice_resp['distributions']['data']), f'i:{i}| ground truth shorter than expected. {len(anydice_resp["distributions"]["data"])}'
    assert named is None or named == anydice_resp['distributions']['labels'][i], f'i:{i}| named does not match expected. expected: {anydice_resp["distributions"]["labels"][i]}, got: {named}'
    check(x, anydice_resp['distributions']['data'][i], i)
    i += 1
  pipeline(inp_code, version=1, global_vars={'output': lambda x, named=None: check_res(x, named)})


@pytest.mark.parametrize("i", range(len(code_resp_pairs)))
def test_all_fetch_v2(i):
  inp_code,anydice_resp,name = code_resp_pairs[i]
  logger.warning(f'Running test {name}: {inp_code} {anydice_resp}')
  v_to_skip = SKIP_VERSION.get(name, {}).get('flags', [])
  if 'v2' in v_to_skip or 'all' in v_to_skip:
    pytest.skip(f'Skipping {name} for v2')
  anydice_resp = json.loads(anydice_resp)
  i = 0
  def check_res(x, named):
    nonlocal i
    assert i < len(anydice_resp['distributions']['data']), f'i:{i}| ground truth shorter than expected. {len(anydice_resp["distributions"]["data"])}'
    assert named is None or named == anydice_resp['distributions']['labels'][i], f'i:{i}| named does not match expected. expected: {anydice_resp["distributions"]["labels"][i]}, got: {named}'
    check(x, anydice_resp['distributions']['data'][i], i)
    i += 1
  pipeline(inp_code, version=2, global_vars={'output': lambda x, named=None: check_res(x, named)})
  # assert False, f'inp_code: {inp_code}, anydice_resp: {anydice_resp}'



code_resp_pairs_picked = [x for x in code_resp_pairs if x[2] in CHERRYPICK]
@pytest.mark.skipif(len(code_resp_pairs_picked) == 0, reason='No tests cherrypicked ; nothing needed to test.')
@pytest.mark.parametrize("i", range(len(code_resp_pairs_picked)))
def test_cherrypick(i):
  inp_code,anydice_resp,name = code_resp_pairs_picked[i]
  logger.warning(f'Running test {name}: {inp_code} {anydice_resp}')
  anydice_resp = json.loads(anydice_resp)
  i = 0
  def check_res(x, named):
    nonlocal i
    label = anydice_resp['distributions']['labels'][i]
    logger.warning(str(i) + ' ' + str(named))
    assert i < len(anydice_resp['distributions']['data']), f'i:{i}| ground truth shorter than expected. {len(anydice_resp["distributions"]["data"])}'
    assert named is None or str(named) == str(label), f'i:{i}| named does not match expected. expected: {label}, got: {named}'

    check(x, anydice_resp['distributions']['data'][i], i)
    i += 1
  pipeline(inp_code, version=2, global_vars={'output': lambda x, named=None: check_res(x, named)})
  # assert False, f'inp_code: {inp_code}, anydice_resp: {anydice_resp}'
