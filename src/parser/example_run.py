from parser import parsetest

trials = [

'''
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
]

# a = parsetest.do_lexer('2 * 3 + 4 * (5 - x)', reload_module=True)
# a = parsetest.do_lexer(trials[-1], reload_module=True)
# a = parsetest.do_parse(trials[-1], reload_module=True)
a = parsetest.do_lexer('\n'.join(trials), reload_module=True)


for x in a: 
    print(x)
    if isinstance(x, str):
        print(x)
