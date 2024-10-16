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
'''

''',
'''

''',
'''

''',
'''

''',
'''

''',
'''

''',
'''

''',
'''

''',
'''

''',
'''

''',
'''

''',
'''

''',
'''

''',
'''

''',
]
