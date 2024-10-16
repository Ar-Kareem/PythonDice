import pytest

from src.randvar import RV, settings_set
from src.parser import parse_and_exec

import logging

logger = logging.getLogger(__name__)

def pipeline(to_parse, version, global_vars={}):
  if version == 1:  # regular
    flags = None
  elif version == 2:  # the very ugly local scope fix
    flags = {'COMPILER_FLAG_NON_LOCAL_SCOPE': True}
  else:
    assert False, f'Unknown version {version}'

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
  r = parse_and_exec.safe_exec(python_str, global_vars=global_vars)
  return r

settings_set('RV_IGNORE_ZERO_PROBS', True)

def check(x, expected):
    logger.debug(x)
    assert type(x) == type(expected), f'types expected {type(expected)} got {type(x)}'
    if not isinstance(x, tuple):
        x = [x]
        expected = [expected]
    for a, b in zip(x, expected):
        if isinstance(a, RV):
            assert a.vals == b.vals, f'expected vals {b.vals} got {a.vals}'
            assert a.probs == b.probs, f'expected probs {b.probs} got {a.probs}'
        else:
            assert a == b, f'expected {b} got {a}'





bv = (0, 1)
lst = [
('''
output ((1d4-1) | (1d2-1))
''', [RV(bv, (125, 875))]
),('''
output {2}&(1d2-1)
''', [RV(bv, (1, 1))]
),('''
output {2,-2}&(1d2-1)
''', [RV(bv, (1, 0))]
),('''
output {2}&{2,-1}
''', [1]
),('''
output {2,-2}&{2,-2}
''', [0]
),('''
output {1,2,3}&1
''', [1]
),('''
output 1d2&1d2
''', [RV(bv, (0, 1))]
),('''
output {1}&1d2
''', [RV(bv, (0, 1))]
),('''
output 1d2&{1}
''', [RV(bv, (0, 1))]
),('''
output d-1
output d+1
A: 3d6
output d#A
''', [RV([-1], [1]), RV([1], [1]), RV([1, 2, 3], [1, 1, 1])]
),('''
output 2 * 2 @ 2d2
''', [RV([2, 4], [3, 1])]
), 
]
@pytest.mark.parametrize("code,res", lst)
def test_ands_and_ors(code, res):
    i = 0
    def check_res(x):
        nonlocal i
        check(x, res[i])
        i += 1
    pipeline(code, version=1, global_vars={'output': lambda x: check_res(x)})
    assert i == len(res)

@pytest.mark.parametrize("code,res", lst)
def test_ands_and_orsv2(code, res):
    i = 0
    def check_res(x):
        nonlocal i
        check(x, res[i])
        i += 1
    pipeline(code, version=2, global_vars={'output': lambda x: check_res(x)})
    assert i == len(res)


lst = [
(r'''
loop P over {1..3} {
  loop PP over {5..6} {
    output PP
    output PP+10
  }
  output 3
  output 4
  if (P-1)/2 {
    output 1003
  } else if P-1 {
    output 1002
  } else {
    output 1001
  }
}

P: 1
if (P-1)/2 {
  output 1003
} else if P-1 {
  output 1002
} else if P {
  output 999
} else {
  output 1001
}
''', [5, 15, 6, 16, 3, 4, 1001, 5, 15, 6, 16, 3, 4, 1002, 5, 15, 6, 16, 3, 4, 1003, 999]
),]
@pytest.mark.parametrize("code,res", lst)
def test_conditionals(code, res):
    i = 0
    def check_res(x):
        nonlocal i
        check(x, res[i])
        i += 1
    pipeline(code, version=1, global_vars={'output': lambda x: check_res(x)})
    assert i == len(res)

@pytest.mark.parametrize("code,res", lst)
def test_conditionalsv2(code, res):
    i = 0
    def check_res(x):
        nonlocal i
        check(x, res[i])
        i += 1
    pipeline(code, version=2, global_vars={'output': lambda x: check_res(x)})
    assert i == len(res)


lst = [
r'''
function: balanced RANK:n from FIVE:s {
 SIXTH: 72 - FIVE
 if SIXTH < 3 | SIXTH > 18 {
  result: d{}
 }
 result: RANK @ [sort {FIVE, SIXTH}]
}

loop RANK over {1..6} {
 output [balanced RANK from 5d[highest 3 of 4d6]]
}
''',
r'''
ABIL: 5 d [highest 3 of 4d6]
loop P over {1..5} {
 output P @ ABIL named "Ability [P]"
}

output 72 - {1..5}@ABIL named "Ability 6"
''',
r'''
function: if X:n in RESTRICT:s {
  if X = RESTRICT { result: X }
  result: d{}
}
output [if 3d6 in {3,5,7,9,11,13,15,17}] named "3d6 if odd"
output [if 3d6 in {4,6,8,10,12,14,16,18}] named "3d6 if even"
''',
r'''
function: INDEX:s at DICE:s if lowest less than MIN:n {
  if (#DICE@DICE >= MIN) { result: d{} }
  result: INDEX@DICE
}

function: INDEX:s at DICE:s if lowest at least MIN:n {
  if (#DICE@DICE < MIN) { result: d{} }
  result: INDEX@DICE
}

MIN: 10

output [2 at 3d20 if lowest less than MIN] named "Middle die of 3d20 if lowest die less than [MIN]"
output [{2,3} at 3d20 if lowest at least MIN] named "Middle and lowest die of 3d20 if lowest die at least [MIN]"
''',
r'''
function: restrict ROLL:n to RANGE:s else REROLL:d {
  if ROLL = RANGE { result: ROLL }
  else { result: REROLL }
}
function: restrict ROLL:d to RANGE:s once {
  result: [restrict ROLL to RANGE else ROLL]
}
function: restrict ROLL:n to RANGE:s else REROLL:d {
  if ROLL = RANGE { result: ROLL }
  else { result: REROLL }
}
function: restrict ROLL:d to RANGE:s {
  loop I over {1..20} {
    ROLL: [restrict ROLL to RANGE else ROLL]
  }
  result: ROLL
}
output [restrict 3d6 to {3,5,7,9,11,13,15,17}] named "3d6 if odd"
output [restrict 3d6 to {4,6,8,10,12,14,16,18}] named "3d6 if even"

function: middle of ROLL:s if lowest in RANGE:s {
  if 3@ROLL = RANGE { result: 2@ROLL } \ assumes a three die pool! \
  else { result: -1 }
}

MAX: 10
DIST: [middle of 3d20 if lowest in {1..MAX}]

output DIST named "middle of 3d20 if lowest <= [MAX] (else -1)"
output [restrict DIST to {1..20}] named "middle of 3d20 if lowest <= [MAX] (conditional)"
''',
r'''
function: attack D:n plus BONUS:n vs AC:n  {
    if D = 20 { result: 1 } 
    else if D = 1 { result: 0}
    else if D + BONUS >= AC { result: 1 } 
    else { result:0}
}

loop AC over {5..25} {
    output [attack d20 plus 8 vs AC] named "[AC]"
}
''',
r'''
output 1d6 != 1d6
output 1d6 = 1d6
output 1d6 > 1d6
output 1d6 < 1d6
output 1d6 ^ 1d6
output 1d6 | 1d6
output 1d6 & 1d6
output (2d2-2)
''',
r'''
function: roll ROLL:s {
  \ we assume that ROLL always has exactly two dice; AnyDice sorts them in descending order \
  HI: 1@ROLL
  LO: 2@ROLL
  \ handle the special cases first \
  if LO = 10 & HI = 10 { result: -1 } \ double 10 = "crit success/fail" \
  if LO + HI = 20      { result: 20 } \ mirror pair = crit success \
  if LO = HI           { result:  0 } \ equal pair = crit failure \ 
  \ at this point, we know there's no equal or mirror pair \
  if [absolute LO - 10] < [absolute HI - 10] { result: LO } else { result: HI }
}

output [roll 2d20]
''',
r'''
function: count VALUES:s in lowest NUMBER:n of DICE:s {
  COUNT: 0
  loop P over {(#DICE - NUMBER + 1) .. #DICE} {
    COUNT: COUNT + (P@DICE = VALUES)
  }
  result: COUNT
}

output [count {8, 9, 10} in lowest 1 of 2d10] named "Domain or Skill"
output [count {8, 9, 10} in lowest 2 of 3d10] named "Domain and Skill"
output [count {8, 9, 10} in lowest 3 of 4d10] named "All and Mastery"

NORMAL: 1
RISKY: 2
DANGEROUS: 3

function: heart RISK:n ROLL:s {
 L: RISK@ROLL 
 if L > 7 {
  result: 2 + (L=10)
 }
 result: L >= 6
}

loop P over {2..4} {
 output [heart DANGEROUS Pd10] named "[P]d10"
}
''',
r'''
A: 2d6
output 1d6 + 1d6 named "hello[A][B ]" \ this is a comment function: test \ output 1d6 + 1d6
output 1d6 + 1d6 named "hello[A][B ]"
''',
r'''
A: 2d6
output 1
''',
r'''
A: 1 >= 2
function: da {
A:1d4
}
A: 2d6
if {1,2,A}>1>=1<=1!=2 {output A}

ORIGINAL: 6d(3d6)
NEW: 7d[highest 3 of 4d{3..6}]

loop N over {1} {
  output N@ORIGINAL named "[N]@3d6"
  output N@NEW named "[N]@7d(4d6r1,2)"
}
ARRAY: 7d[highest 3 of 4d{3..6}]
output 1@ARRAY
output 2@ARRAY
output 3@ARRAY
output 4@ARRAY
output 5@ARRAY
output 6@ARRAY
function: stat{
result: [highest 3 of 4d6]
}
output 1@24d([stat])
''',
r'''
\** GREAT WEAPON FIGHTING **\
\
  the first parameter is evaluated as a die roll, the second is evaluated as a die,
  a die cannot be rolled within a function and assigned to a variable (this sucks).
  the only way to evaluate a die roll is to pass it as an argument; DAMAGE_ROLL
  and DAMAGE_DIE must be the same, i.e. d6 & d6
\
function: gwf with DAMAGE_ROLL:n rolled on DAMAGE_DIE:d {
   if DAMAGE_ROLL < 3 { result: dDAMAGE_DIE }
   result: DAMAGE_ROLL
}
\ so, we define another function to call the first one \
function: gwf with die DIE:d { result: [gwf with DIE rolled on DIE] }

\** CRITICAL HIT (OR MISS) **\
\
  the only way to evaluate a die roll is to pass it as an argument, so ROLL must be 'd20'
  I can't see away around the tight coupling between function definition and function call.
\
function: is ROLL:n a crit or miss with damage DAMAGE:d {
   if ROLL = 20 { result: dDAMAGE+dDAMAGE }
   if ROLL = 1 { result: 0 }
   result: dDAMAGE
}
\ so, we define another function to call the first one \
function: return crit or miss with damage DAMAGE:d { result: [is d20 a crit or miss with damage DAMAGE] }

\ END DEFINITIONS \

function: figher damage roll { result: [return crit or miss with damage 2d[gwf with die d6]]+5 }
function: rogue damage roll { result: [return crit or miss with damage 4d6]+4 }
output 1d6+4 named "rogue, do something useful"
output [figher damage roll] named "figher (one hit)"
output [rogue damage roll] named "rogue (sneak attack)"
output [figher damage roll]+[figher damage roll] named "figher (two hits)"
output [figher damage roll]+[figher damage roll]+[rogue damage roll] named "Who's yer daddy?"
''',
r'''
\
 !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~
\
\ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~ \

output 1d1
''',
r'''
output {2*3..4}
Z__A_ : 2 + 3 * {2, {}} / 5
output Z__A_ 
output 2d2
output 1
if 1 {if 1 {A:1 A:1}}
output 1
if 1=1 {A:1} else {A:2}
if 1=1 {A:1} else if 1=1 {A:2} else {A:3}
function: rand B:s name a {A:2}
''',
r'''
set "position order" to "lowest first"

output 1@3d6 named "lowest die"
output 1@2d6 named "least significant digit"

set "position order" to "highest first" \ the default behavior \

output 1@3d6 named "highest die"
output 1@2d6 named "most significant digit"
function: anotheranother test D {
  result: 1
}
function: D anotheranother test B {
  result: 1
}
function: D {
  result: 1
}
function: D B {
  result: 1
}
''',
r'''
output [absolute 1]
output [{1..5} contains 1]
output [count 1 in {1..5}]
output [explode d3]
output [highest 1 of 2d3]
output [lowest 1 of 2d3]
output [middle 1 of 2d3]
output [highest of 1 and 1]
output [lowest of 1 and 1]
output [maximum of 2d3]
output [reverse {1..4}]
output [sort {1..4}]
''',
r'''
function: a {result: 1}

output [a]

function: call b {result: [b]+1}
function: b {result: 2}
output [call b]
''',
r'''
set "explode depth" to 1
AAA: 1
set "explode depth" to AAA
loop AAAA over {1..5} {
  set "explode depth" to AAAA
}
loop DEPTH over {1..5} {
  set "explode depth" to DEPTH
}
output 1
''',
r'''
loop P over {1..5} {
 output 1 named "INLOOP%[P]%"
}
'''
]
@pytest.mark.parametrize("code", lst)
def test_running(code):
    r = pipeline(code, version=1)
    assert r is not None


@pytest.mark.parametrize("code", lst)
def test_runningv2(code):
    r = pipeline(code, version=2)
    assert r is not None



lst = [
r'''
function: a {result: 1}

output [a]

function: call b {result: [b]+1}
output [call b]
''',
r'''
A: 1
'''  # no output should error
]
@pytest.mark.parametrize("code", lst)
def test_FAIL_code(code):
    with pytest.raises(Exception):
      pipeline(code, version=1)

@pytest.mark.parametrize("code", lst)
def test_FAIL_codev2(code):
    with pytest.raises(Exception):
      pipeline(code, version=2)


unbound_var_code = [
('''
function: rolla {
  B: B + 1
  result: B
}
B: 10
output [rolla]
output B
''', [11, 10]),

]

@pytest.mark.parametrize("code, res", unbound_var_code)
def test_scope_fail(code, res):
    with pytest.raises(Exception):
      pipeline(code, version=1)

@pytest.mark.parametrize("code, res", unbound_var_code)
def test_scope_success(code, res):
    i = 0
    def check_res(x):
        nonlocal i
        check(x, res[i])
        i += 1
    pipeline(code, version=2, global_vars={'output': lambda x: check_res(x)})
    assert i == len(res)
