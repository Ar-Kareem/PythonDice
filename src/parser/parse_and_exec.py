
trials = [
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
output {2*3..4@4}
__A_ : 2 + 3 * {2, {}} / 5
output __A_ 
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
'''
]
import logging
from parser import myparser
from .myparser import lexer, ILLEGAL_CHARS, yacc_parser
from .python_resolver import PythonResolver

def setup_logging(filename):
    logging.basicConfig(filename=filename, level=logging.DEBUG, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger().addHandler(logging.StreamHandler())
setup_logging('./log/example_run.log')

def parse(to_parse, verbose_lex=False, verbose_yacc=False):
  if to_parse is None or to_parse.strip() == '':
    logging.debug('Empty string')
    return

  lexer.input(to_parse)
  tokens = [x for x in lexer]

  for x in ILLEGAL_CHARS:
      logging.debug(f'Illegal character {x!r}')

  if verbose_lex:
    logging.debug('Tokens:')
    for x in tokens:
        logging.debug(x)

  yacc_ret = yacc_parser.parse(to_parse)
  if verbose_yacc and yacc_ret:
    for x in yacc_ret:
      logging.debug('yacc: ' + str(x))
  return yacc_ret

def parse_and_exec(to_parse, do_exec=True, verbose_input_str=False, verbose_lex=False, verbose_yacc=False, verbose_parseed_python=False):
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
    print('g', g)
    logging.debug('Executing parsed python:')
    exec(r, g, g)


for to_parse in trials:
  try:
    parse_and_exec(to_parse, 
                  do_exec=True, 
                  verbose_input_str=False, 
                  verbose_lex=False, 
                  verbose_yacc=False, 
                  verbose_parseed_python=True)
  except Exception as e:
    logging.warning(f'Error in parsing: {to_parse}')
    logging.exception(e)
    raise
    # parse_and_exec(to_parse, do_exec=False, verbose_input_str=True, verbose_lex=True, verbose_yacc=True, verbose_parseed_python=False)
    pass
print('done')