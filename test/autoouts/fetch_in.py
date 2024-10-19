code_library = [
'''
output 1
''',
'''
output 1d6
''',
'''
output 1 + 2 * 3 ^ 4 @ 5 d 6
''',
'''
output 1d6
output 1d2
output 1d4 named "1d4 now"
output 1d2 named "1d2 now"
output 1d3
''',
'''
output (! 2)>3
output ! (2>3)
output 2 > !3
output ! 2>3
''',
'''
output ! 5
output ! 0
output ! -5
output ! (1 > 2)
output ! (1 < 2)
''',
#   https://www.reddit.com/r/3d6/comments/9skfiz/anydice_tutorial_part_1_basics_and_damage/
'''
output d6
output 1d6 + 4
output 2d6 named "2d6 vary independently of each other"
output 2*d6 named "2*d6 depends on only one dice roll"
X:d6
output X + X named "Variables capture entire distributions"
output [highest 1 of 2d20]
output [lowest 1 of 2d20]
output [highest 1 of 2d20]
output [highest of d20 and d20]
output 1d4 + 5 named "1d4 dagger + 5 dex"
output 2d6 + 5 named "2d6 greatsword + 5 str"
output 1d8 + 4 + 3d6 named "1d8 longbow + 4 dex + 3d6 sneak attack"
output d20 + 3 + 4 named "+3 proficiency +4 strength"
output d20 + 3 + 4 + d4 named "+3 proficiency +4 strength with bless"
output [highest 1 of 2d20] + 3 + 4 named "+3 proficiency +4 strength with advantage"
output d20 + 3 + 4 + 2 named "+3 proficiency +4 dexterity +2 archery fighting style"
output [lowest 1 of 2d20] + 3 + 4 named "+3 proficiency +4 strength with disadvantage"
output [highest of [lowest of d20 + 3 + 4 - 15 + 1 and 1] and 0] named "+3 proficiency +4 strength"
output [highest of [lowest of d20 + 3 + 4 + d4 - 15 + 1 and 1] and 0] named "+3 proficiency +4 strength with bless"
output [highest of [lowest of [highest 1 of 2d20] + 3 + 4 - 15 + 1 and 1] and 0] named "+3 proficiency +4 strength with advantage"
output [highest of [lowest of d20 + 3 + 4 + 2 - 15 + 1 and 1] and 0] named "+3 proficiency +4 strength +2 archery fighting style"
output [highest of [lowest of [lowest 1 of 2d20] + 3 + 4 - 15 + 1 and 1] and 0] named "+3 proficiency +4 strength with disadvantage"
output
[highest of [lowest of d20 + 2 + 3 - 13 + 1 and 1] and 0] * (1d6 + 3) +
[highest of [lowest of d20 + 2 + 3 - 13 + 1 and 1] and 0] * (1d6 + 3)
named "Two-weapon fighting"

output
[highest of [lowest of d20 + 2 + 3 - 13 + 1 and 1] and 0] * (1d8 + 3 + 2) 
named "Dueling"

output
[highest of [lowest of d20 + 2 + 3 + 2 - 13 + 1 and 1] and 0] * (1d10 + 3) 
named "Archery"

output
[highest of [lowest of d20 + 2 + 3 - 13 + 1 and 1] and 0] * (2d6 + 3) 
named "Defense (Greatsword)"

output [highest 1 of 2d20 + 100]
output [highest 1 of 2d20] + 100
output 1d{0, 0, 0, 1d4}
output 1d{0, 0, 0, 1, 2, 3, 4}
output 1d{0, 1} * 1d6 + 4
output 1d{0, 1} * (1d6 + 4) 
''',  
# https://www.reddit.com/r/3d6/comments/9sv548/anydice_tutorial_part_2_functions_rerolls_crits/
'''
function: double X:n when even {
    if X = 2*(X/2) {
        result: 2*X
    }
    result: X
}
function: reroll REROLL:s on ROLL:n to REPLACEMENT:d {
    if [REROLL contains ROLL] {
        result: REPLACEMENT
    }
    result: ROLL
}
output [reroll {1,2} on d8 to d8]
function: reroll REROLL:s on DICE:d {
    result: [reroll REROLL on DICE to DICE]
}
function: attack ROLL:n plus BONUS:n vs AC:n for DMG:d crit CRIT_DMG:d on CRIT_RANGE:n {
    if ROLL = 1 {
        result: 0
    }
    if ROLL >= CRIT_RANGE {
        result: DMG + CRIT_DMG
    }
    if ROLL + BONUS >= AC {
        result: DMG
    }
    result: 0
}
output [attack [highest 1 of 2d20] plus 2 + 3 vs 13 for 1d6 + 3 + 2d6 crit 1d6 + 2d6 on 20]
function: attack ROLL:n plus BONUS:n vs AC:n hit HIT:d miss MISS:d crit CRIT:d on CRIT_RANGE:n {
    if ROLL = 1 {
        result: MISS
    }
    if ROLL >= CRIT_RANGE {
        result: CRIT
    }
    if ROLL + BONUS >= AC {
        result: HIT
    }
    result: MISS
}
output
[attack d20 plus 4 + 5 vs 16
    hit  1d6 + 5 + 5d6  + [attack d20 plus 4 + 5 vs 16 for 1d6       crit 1d6       on 20]
    miss                  [attack d20 plus 4 + 5 vs 16 for 1d6 + 5d6 crit 1d6 + 5d6 on 20]
    crit 2d6 + 5 + 10d6 + [attack d20 plus 4 + 5 vs 16 for 1d6       crit 1d6       on 20] on 20
] named "[9] Two-weapon rogue"
output
[attack d20 plus 4 + 3 + 2 vs 16
    hit  [attack [highest 1 of 2d20] plus 4 + 3 + 2 - 5 vs 16 for 1d6 + 3 + 10 + 4d6 crit 1d6 + 4d6 on 20]
    miss [attack d20                 plus 4 + 3 + 2     vs 16 for 1d6 + 3      + 4d6 crit 1d6 + 4d6 on 20]
    crit [attack [highest 1 of 2d20] plus 4 + 3 + 2 - 5 vs 16 for 1d6 + 3 + 10 + 4d6 crit 1d6 + 4d6 on 20] on 20
] named "[9] Crossbow expert throwing nets and sharpshooting"
output
[attack d20 plus 4 + 3 + 2 vs 16
    hit  1d6 + 3 + 4d6 + [attack d20 plus 4 + 3 + 2 - 5 vs 16 for 1d6 + 3 + 10       crit 1d6       on 20]
    miss                 [attack d20 plus 4 + 3 + 2     vs 16 for 1d6 + 3      + 4d6 crit 1d6 + 4d6 on 20]
    crit 2d6 + 3 + 8d6 + [attack d20 plus 4 + 3 + 2 - 5 vs 16 for 1d6 + 3 + 10       crit 1d6       on 20] on 20
] named "[9] Crossbow expert attacking twice and sharpshooting if the first attack hit"

function: attack ROLL:n plus BONUS:n vs AC:n hit HIT:d miss MISS:d crit CRIT:d on CRIT_RANGE:n {
    if ROLL = 1 {
        result: MISS
    }
    if ROLL >= CRIT_RANGE {
        result: CRIT
    }
    if ROLL + BONUS >= AC {
        result: HIT
    }
    result: MISS
}

function: attack ROLL:n plus BONUS:n vs AC:n for DMG:d crit CRIT_DMG:d on CRIT_RANGE:n {
    result: [attack ROLL plus BONUS vs AC hit DMG miss 0 crit DMG + CRIT_DMG on CRIT_RANGE]
}


function: reroll REROLL:s on ROLL:n to REPLACEMENT:d {
    if [REROLL contains ROLL] {
        result: REPLACEMENT
    }
    result: ROLL
}

function: reroll REROLL:s on DICE:d {
    result: [reroll REROLL on DICE to DICE]
}

function: gwf DICE:d {
    result: [reroll {1,2} on DICE]
}

ADVANTAGE: [highest 1 of 2d20]

DISADVANTAGE: [lowest 1 of 2d20]

output
[attack d20 plus 2 + 3 vs 13 for 1d6 + 3 crit 1d6 on 20] +
[attack d20 plus 2 + 3 vs 13 for 1d6 + 3 crit 1d6 on 20]
named "Two-weapon fighting"

output
[attack d20 plus 2 + 3 vs 13 for 1d8 + 3 + 2 crit 1d8 on 20]
named "Dueling"

output
[attack d20 plus 2 + 3 + 2 vs 13 for 1d10 + 3 crit 1d10 on 20]
named "Archery"

output
[attack d20 plus 2 + 3 vs 13 for 2d[gwf d6] + 3 crit 2d[gwf d6] on 20]
named "Great-weapon fighting"

''',
# https://anydice.com/program/2d89a
r'''
\ 
ANYDICE Code for the Virtually Real RPG.  
Released under CC-SA by Virtually Real Games 2023
As examples of custom exploding dice systems.
\
 
\ Initializers \

CRIT: 0                    \ A crit is rolling a 0 \
MAXDICE: 5                 \ 5 is the max dice we ever add \
INSPILEVEL: 1              \ How many inspiration levels to output \
SHORTLEVEL: 1              \ How many penalty levels to output \

set "maximum function depth" to MAXDICE

\ 
Virtually Real skill system separates training from experience.
The number in the square brackets is your training, the number of
dice to roll.  Your experience in the skill determine's the modifier.

The number of dice to roll is as follows :
        [1]     Secondary skill, untrained
        [2]     Primary Skill, trained
        [3]     Advanced (master craftsman, olympic atheletes)
        [4]     Supernatural (non-human; need [3] in the attribute)
        [5]     Deific (divine; need [4] or [5] in the attribute)

Brilliant results will roll an extra d6 on the following natural rolls,
the last column shows the normal critical failure results.

        [1]     6               1
        [2]     12              2
        [3]     17,18           3
        [4]     22-24           4
        [5]     27-30           5,6

If the extra/exploded die is a 6, add +2 to the total and roll another die.
If you keep rolling 6's, keep adding 2 and roll another die.
If it wasn't a 6, on rolls of
        [1]     Don't add anything more
        [2+]    Add the result on the die and stop

Most positional / tactical modifiers are presented in the book and
are fixed-value modifiers.  The curve and chances of brilliant or
critical results do not change.  The min, max, and average values
change by the modifier.  In practice, this will be a skill level
and possibly 1 other modifier.

Ardor is used for special interests such as skill aspects or "home"
geography & history, your own culture, favorite weapon, etc.  Ardor
is long-term, specific, non-situational source of "inspiration".
Situational modifiers may add other sources of inspiration.  

Inspiration is a somewhat random bonus that adds just under 2, but 
additional sources of inspiration give steadily lower benefits. Any
source of inspiration will slowly decrease critical failure rates
and increase your chances of a brilliant.  

A shortcoming is the reverse of inspiration.  Shortcomings mainly
come from the condition chart, applied to most combat rolls. Use 
shortcomings and inspiration for random situational modifiers where 
precision is unavailable or undesirable.  

Add +1 die per source of inspiration and drop the lowest die rolled.  Add
+1 to the critical range (total, not per source).

Shortcomings come from conditions on the condition chart and also
from some backgrounds and situational penalties.  It's the reverse of
inspiration.  Note that positional and other combat modifiers give
flat bonuses and penalties to the roll itself.  While skill level
bonuses are not applied to critical failures, other flat bonuses are.
Add +1 die per shortcoming and subtract the highest die.

You can have Inspirations and Shortcomings on the same roll.
See the very end of the table for examples where heavy condition
code modifiers might apply large numbers of shortcomings, and
note how applying inspiration affects the roll.

NOTE: The results shown are die roll results.  Your skill LEVEL
and any fixed modifiers are added if the result is not critical.
This is then compared to the target number.  Degrees of success
matter!
\

\ What rolls are brilliant for this many dice \ 
function: brilliant of DICE:d {
  MAX: [maximum of DICE] +2
  if MAX = 8 { result: { 6 } } 
  BR: {}
  loop N over {1..#DICE} {
    if N = 1 {
      BR: BR
    }
    else {
      BR: {BR, MAX-N}
    }
  }
  result: {BR}
}

\ returns the set of critical rolls for this many dice \
function: critical plus LEVEL:n of DICE:d {
  if #DICE > 4 { 
    LEVEL: LEVEL+1 
  }
  else { 
    CRIT: {#DICE} 
  }
  N: #DICE
  loop S over {1 .. LEVEL} {
    N: N+1
    CRIT: {CRIT,N}
  }
  result: CRIT  
}

\ explode helper for [2]+ dice rolls \
function: explodeb ROLLEDVALUE:n {
 if ROLLEDVALUE = 6 { 
   result: 2 + [explodeb d6] 
 }
  else {
    result: ROLLEDVALUE
  }
}

\ explode helper for [1] die rolls \
function: explodec ROLLEDVALUE:n {
  if ROLLEDVALUE = 6 { result: 2 + [explodec d6] }
  result: 0
}

\ The new explode function with crit and brilliant ranges \
function: explode ROLLEDVALUE:n crit CRITR:s bril BRIL:s {
if ROLLEDVALUE = CRITR { result: CRIT }
 if BRIL = 6 &  ROLLEDVALUE = 6 { result: ROLLEDVALUE + [ explodec d6 ] }
 if ROLLEDVALUE = BRIL { result: ROLLEDVALUE + [explodeb d6] }
 result: ROLLEDVALUE
}

\ My replacement explode function, wrapping the above \
function: explode DICE:d {
  if #DICE = 1 {
    result: [explode DICE crit 1 bril 6]
  }
  result: [explode DICE crit [critical plus 0 of DICE] bril [brilliant of DICE]]
}

\ Middle x values of a roll with start and end \
function: mid NUM:n start PENALTY:n of SET:s {
 S: [sort SET]
 R: {}
 START: PENALTY+1
 END: NUM+PENALTY
 loop P over {START..END} {
  R: {P@S, R}
 }
 result: R
}

\ Shortcoming + Inspiration \
function: complex DICE:d bonus BONUS:n penalty SHORT:n {
  TOTALDICE: #(DICE) + BONUS + SHORT
  NEWCRIT: BONUS
  \if NEWCRIT > (SHORT+1) {
    NEWCRIT: (SHORT+1)
  }\
  if BONUS > 0 {
    NEWCRIT: 1
  }
  result: [explode [mid #(DICE) start SHORT of TOTALDICEd6] crit [critical plus NEWCRIT of DICE] bril [brilliant of DICE]]
}

\ Main Program \

loop N over {1..MAXDICE} {
  TEST: Nd6

  \ List shortcomings in reverse order \
  loop S over {1..SHORTLEVEL} {
    REVERSE: SHORTLEVEL-S+1
    output [complex TEST bonus 0 penalty REVERSE] named "[TEST] [REVERSE]s 0i"
  }
  output [complex TEST bonus 0 penalty 0] named "Exploding [TEST]"
  loop S over {1..INSPILEVEL} {
    output [complex TEST bonus S penalty 0] named "[TEST] 0s [S]i"
  }
}

\ Special stuff 2d6 with various bonuses/inspiration and shortcomings/penalties\

loop P over {0..4} {
  loop B over {0..4} {
    output [complex 2d6 bonus B penalty P] named "2d6 [P]s [B]i"
  }
}
''',
r'''
function: rec {
  result: [rec]+1
}
output [rec]

set "maximum function depth" to 42
function: rec {
  result: [rec]+1
}
output [rec]
''',
r'''
A: 1d6
output 0 named "[A]"
A: 2d1
output 0 named "[A]"
A: 2d{1}
output 0 named "[A]"
A: 2d(2d2)
output 0 named "[A]"
A: 2d(1d2)
output 0 named "[A]"
''',
# # __STR__ (INT, INT)
r'''
loop PA over {-3,-1,0,1,3} {
  loop PB over {-3,-1,0,1,3} {
    A: PA d PB
    output 0 named "[PA]d[PB]=[A]"
  }
}
''',
# __STR__ (SEQ, INT)
r'''
PA: {}
loop PB over {-3,-1,0,1,3} {
  A: PA d PB
  output 0 named "[PA]d[PB]=[A]"
}
PA: {-2}
loop PB over {-3,-1,0,1,3} {
  A: PA d PB
  output 0 named "[PA]d[PB]=[A]"
}
PA: {-1}
loop PB over {-3,-1,0,1,3} {
  A: PA d PB
  output 0 named "[PA]d[PB]=[A]"
}
PA: {0}
loop PB over {-3,-1,0,1,3} {
  A: PA d PB
  output 0 named "[PA]d[PB]=[A]"
}
PA: {1}
loop PB over {-3,-1,0,1,3} {
  A: PA d PB
  output 0 named "[PA]d[PB]=[A]"
}
PA: {2}
loop PB over {-3,-1,0,1,3} {
  A: PA d PB
  output 0 named "[PA]d[PB]=[A]"
}
PA: {-2,2}
loop PB over {-3,-1,0,1,3} {
  A: PA d PB
  output 0 named "[PA]d[PB]=[A]"
}
PA: {-2,-2}
loop PB over {-3,-1,0,1,3} {
  A: PA d PB
  output 0 named "[PA]d[PB]=[A]"
}
PA: {2,2}
loop PB over {-3,-1,0,1,3} {
  A: PA d PB
  output 0 named "[PA]d[PB]=[A]"
}
''',
# __STR__ (INT, SEQ)
r'''
PA: {}
loop PB over {-3,-1,0,1,3} {
  A: PB d PA
  output 0 named "[PB]d[PA]=[A]"
}
PA: {-2}
loop PB over {-3,-1,0,1,3} {
  A: PB d PA
  output 0 named "[PB]d[PA]=[A]"
}
PA: {-1}
loop PB over {-3,-1,0,1,3} {
  A: PB d PA
  output 0 named "[PB]d[PA]=[A]"
}
PA: {0}
loop PB over {-3,-1,0,1,3} {
  A: PB d PA
  output 0 named "[PB]d[PA]=[A]"
}
PA: {1}
loop PB over {-3,-1,0,1,3} {
  A: PB d PA
  output 0 named "[PB]d[PA]=[A]"
}
PA: {2}
loop PB over {-3,-1,0,1,3} {
  A: PB d PA
  output 0 named "[PB]d[PA]=[A]"
}
PA: {-2,2}
loop PB over {-3,-1,0,1,3} {
  A: PB d PA
  output 0 named "[PB]d[PA]=[A]"
}
PA: {-2,-2}
loop PB over {-3,-1,0,1,3} {
  A: PB d PA
  output 0 named "[PB]d[PA]=[A]"
}
PA: {2,2}
loop PB over {-3,-1,0,1,3} {
  A: PB d PA
  output 0 named "[PB]d[PA]=[A]"
}
''',
# __STR__ (SEQ, SEQ)
r'''
function: a I:n {
  result: {I}
}
loop PA over {-3,-1,0,1,3} {
  loop PB over {-3,-1,0,1,3} {
    A: [a PA] d [a PB]
    output 0 named "a [PA]d[PB]=[A]"
  }
}

function: aa I:n {
  result: {-1, I}
}
loop PA over {-3,-1,0,1,3} {
  loop PB over {-3,-1,0,1,3} {
    A: [aa PA] d [aa PB]
    output 0 named "a [PA]d[PB]=[A]"
  }
}
''',
# __STR__ RV (too bored to write more)
r'''
A: 2 d ({1} d ({1} d 2))
output 0 named "[A]"

A: 2 d (1 d (1 d 2))
output 0 named "[A]"

function: g I:n {
  if I <= 2 {result: 0}
  result: 1
}
A: [g 1d4]
output 0 named "[A]"
A: 2 d A
output 0 named "[A]"

''',
r'''
function: myrange {
result: 2
}
output [myrange]
output {1..4}
''',
r'''
A: 1 d (1 d (1 d 2))
output 1@A named "[A]"
''',
r'''
function: a {
result: [sort 5d6]
}
output 1 @ 5d6
output 1 @ [sort 5d6]
function: sort D:d {
result: D
}
output 1 @ [sort 5d6]
output 1 @ [a]
''',
r'''
output #-100
output #-10
output #-9
output #-1
output #0
output #7
output #78
output #789
''',
r'''
output -2 @ 789
output -1 @ 789
output 0 @ 789
output 1 @ 789
output 2 @ 789
output 3 @ 789
output 4 @ 789
output 5 @ 789
''',
r'''
output !10
output !1
output !0
output !-1
output !-5
output !-10
''',
r'''
_A: 2
output _A
''',
r'''
output !(2d4)
output !(2d0)
output !(0d4)
output !(2d(2d(0d3)))
''',
r'''
output !({})
output !({0})
output !({0,0})
output !({-1,1})
output !({0,-1,1})
output !({0,-1})
output !({-2,2})
''',
r'''
function: d {result: 1} \impossible to call\
function: d A {result: 1} \impossible to call\
function: A:d {result: 1}  \can call, is just 1 param called A\
output [ d 1 ]
''',
# SHOWING THAT MAX INT IS WRONG
r'''
output 922340 - 9999999999999999999/10000000000000  
''',
r'''
output {1..3}@4d6 named "4d6 drop lowest"
''',
r'''

function: evaluate S:s {
 
}
X: [evaluate 1d1] 

output X
''',
r'''

function: evaluate S:s {
 
}
X: [evaluate 1] 

output X
''',
r'''
function: e N:n {
 result: [e N]+1
}
set "maximum function depth" to 2
output [e 2d4]

''',
r'''

''',
r'''

''',
r'''

''',
]














# so that you can simply run this code using vanilla vscode's code runner
if __name__ == '__main__':
  from fetch import main
  main()
