# recreations of functions in https://anydice.com/docs/function-library/
from .randvar import RV
from .seq import Seq
from .settings import SETTINGS
from .roller import roll
from .decorators import anydice_casting

# BASE FUNCTIONS


@anydice_casting()
def absolute(NUMBER: int, *args, **kwargs):
    if NUMBER < 0:
        return -NUMBER
    return NUMBER


@anydice_casting()
def contains(SEQUENCE: Seq, NUMBER: int, *args, **kwargs):
    return (SEQUENCE == NUMBER) > 0


@anydice_casting()
def count_in(VALUES: Seq, SEQUENCE: Seq, *args, **kwargs):
    COUNT = 0
    for P in range(1, len(VALUES) + 1):
        COUNT = COUNT + (P @ VALUES == SEQUENCE)
    return COUNT


@anydice_casting()
def reverse_VANILLA_SLOW(SEQUENCE: Seq, *args, **kwargs):
    R = Seq()
    for P in range(1, len(SEQUENCE) + 1):
        R = Seq(P @ SEQUENCE, R)
    return R


@anydice_casting()
def reverse(SEQUENCE: Seq, *args, **kwargs):
    return Seq(SEQUENCE._seq[::-1])


@anydice_casting()
def maximum_of(DIE: RV, *args, **kwargs):
    return 1 @ reverse(Seq(DIE))


@anydice_casting()
def explode(DIE: RV, *args, depth=None, **kwargs):
    if depth is None:
        depth = SETTINGS['explode depth']
    MAX = maximum_of(DIE)
    return _explode_helper(DIE, MAX, ORIG_DIE=DIE, depth=depth)  # type: ignore


@anydice_casting()
def _explode_helper(N: int, MAX: int, ORIG_DIE: RV, depth):
    if N == MAX and depth > 0:
        return N + _explode_helper(ORIG_DIE, MAX, ORIG_DIE=ORIG_DIE, depth=depth - 1)  # type: ignore
    return N


@anydice_casting()
def highest_N_of_D(NUMBER: int, DICE: RV, *args, **kwargs):
    return Seq(range(1, NUMBER + 1)) @ DICE


@anydice_casting()
def lowest_N_of_D(NUMBER: int, DICE: RV, *args, **kwargs):
    return Seq(range((len(DICE) - NUMBER + 1), len(DICE) + 1)) @ DICE


@anydice_casting()
def middle_N_of_D(NUMBER: int, DICE: RV, *args, **kwargs):
    if NUMBER == len(DICE):
        return DICE

    if NUMBER == 1:
        return (1 + (len(DICE) - 1) // 2) @ DICE

    FROM = 1 + (len(DICE) - NUMBER) // 2
    TO = FROM + NUMBER - 1
    return Seq(range(FROM, TO + 1)) @ DICE


@anydice_casting()
def highest_of_N_and_N(A: int, B: int, *args, **kwargs):
    if A > B:
        return A
    return B


@anydice_casting()
def lowest_of_N_and_N(A: int, B: int, *args, **kwargs):
    if A < B:
        return A
    return B


@anydice_casting()
def sort_VANILLA_SLOW(SEQUENCE: Seq, *args, **kwargs):
    SORTED = Seq()
    for P in range(1, len(SEQUENCE) + 1):
        SORTED = _sort_helper_add_N_to_S(P @ SEQUENCE, SORTED)  # type: ignore
    return SORTED


@anydice_casting()
def _sort_helper_add_N_to_S(N: int, S: Seq, *args, **kwargs):
    if len(S) == 0:
        return Seq(N)
    if N >= 1 @ S:
        return Seq(N, S)
    if N <= (len(S)) @ S:
        return Seq(S, N)

    R = Seq()
    for P in range(1, len(S) + 1):
        if N >= P @ S:
            R = Seq(R, N, P @ S)
            N = Seq()  # type: ignore
        else:
            R = Seq(R, P @ S)
    if len(N):  # type: ignore
        R = Seq(R, N)
    return R


@anydice_casting()
def sort(SEQUENCE: Seq, *args, **kwargs):
    return Seq(sorted(SEQUENCE, reverse=True))

# MORE FUNCTIONS


@anydice_casting()
def gwf(num_die: int, dmg_die, min_to_reroll=2, *args, **kwargs):
    assert isinstance(num_die, int), 'great weapon fighting must get int as number of die and faces of dmg die'
    if isinstance(dmg_die, int):  # prevent making RV as constant int
        dmg_die = roll(1, dmg_die)
    single_gwf = _gwf_helper(roll_1=dmg_die, dmg_die=dmg_die, min_to_reroll=min_to_reroll)  # type: ignore
    return roll(num_die, single_gwf)


@anydice_casting()
def _gwf_helper(roll_1: int, dmg_die: RV, min_to_reroll: int, *args, **kwargs):
    if roll_1 <= min_to_reroll:
        return dmg_die
    return roll_1
