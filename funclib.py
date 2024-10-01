# recreations of functions in https://anydice.com/docs/function-library/
import randvar as rv
from randvar import Seq, RV

@rv.anydice_casting()
def absolute (NUMBER:int):
    if NUMBER < 0: 
        return -NUMBER
    return NUMBER

@rv.anydice_casting()
def contains(SEQUENCE:Seq, NUMBER:int):
    return (SEQUENCE == NUMBER) > 0

@rv.anydice_casting()
def count_in(VALUES:Seq, SEQUENCE:Seq):
    COUNT = 0
    for P in range(1, len(VALUES)+1):
        COUNT = COUNT + (P@VALUES == SEQUENCE)
    return COUNT

@rv.anydice_casting()
def reverse_VANILLA_SLOW(SEQUENCE:Seq):
    R = Seq()
    for P in range(1, len(SEQUENCE)+1):
        R = Seq(P@SEQUENCE, R)  
    return R
@rv.anydice_casting()
def reverse(SEQUENCE:Seq):
    return Seq(SEQUENCE.seq[::-1])

@rv.anydice_casting()
def maximum_of(DIE:RV):
    return 1@reverse(Seq(DIE))

@rv.anydice_casting()
def explode(DIE:RV, depth=2):
    MAX = maximum_of(DIE)
    return _explode_helper(DIE, MAX, ORIG_DIE=DIE, depth=depth)  # type: ignore

@rv.anydice_casting()
def _explode_helper(N:int, MAX:int, ORIG_DIE:RV, depth):
    if N == MAX and depth > 0:
        return N + _explode_helper(ORIG_DIE, MAX, ORIG_DIE=ORIG_DIE, depth=depth-1)  # type: ignore
    return N

@rv.anydice_casting()
def highest_N_of_D(NUMBER:int, DICE:RV):
    return Seq(range(1, NUMBER+1))@DICE

@rv.anydice_casting()
def lowest_N_of_D(NUMBER:int, DICE:RV):
    return Seq(range((len(DICE) - NUMBER + 1), len(DICE)+1))@DICE

@rv.anydice_casting()
def middle_N_of_D(NUMBER:int, DICE:RV):
    if NUMBER == len(DICE): 
        return DICE

    if NUMBER == 1: 
        return (1 + (len(DICE) - 1) // 2) @ DICE

    FROM = 1 + (len(DICE) - NUMBER) // 2
    TO = FROM + NUMBER - 1
    return Seq(range(FROM, TO+1))@DICE

@rv.anydice_casting()
def highest_of_N_and_N(A:int, B:int):
    if A > B:
        return A
    return B

@rv.anydice_casting()
def lowest_of_N_and_N(A:int, B:int):
    if A < B:
        return A
    return B

@rv.anydice_casting()
def sort_VANILLA_SLOW(SEQUENCE:Seq):
    SORTED = Seq()
    for P in range(1, len(SEQUENCE)+1):
        SORTED = _sort_helper_add_N_to_S(P@SEQUENCE, SORTED)
    return SORTED

@rv.anydice_casting()
def _sort_helper_add_N_to_S(N:int, S:Seq):
    if len(S) == 0:
        return Seq(N)
    if N >= 1@S: 
        return Seq(N, S)
    if N <= (len(S))@S:
        return Seq(S, N)

    R = Seq()
    for P in range(1, len(S)+1):
        if N >= P@S:
            R = Seq(R, N, P@S)
            N = Seq()
        else: 
            R = Seq(R, P@S)
    if len(N): 
        R = Seq(R, N)
    return R

@rv.anydice_casting()
def sort(SEQUENCE:Seq):
    return Seq(sorted(SEQUENCE, reverse=True))
