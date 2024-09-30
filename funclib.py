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
def count_in (VALUES:Seq, SEQUENCE:Seq):
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
def maximum_of (DIE:RV):
    return 1@reverse(Seq(DIE))

@rv.anydice_casting()
def explode(DIE:RV, depth=8):
    MAX = maximum_of(DIE)
    return _explode_helper(DIE, MAX, ORIG_DIE=DIE, depth=depth)

@rv.anydice_casting()
def _explode_helper(N:int, MAX:int, ORIG_DIE:RV, depth):
    if N == MAX and depth > 0:
        return N + _explode_helper(ORIG_DIE, MAX, ORIG_DIE=ORIG_DIE, depth=depth-1)
    return N
