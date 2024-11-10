# recreations of functions in https://anydice.com/docs/function-library/
from .typings import T_N, T_S, T_D
from .seq import Seq
from .settings import SETTINGS
from .roller import roll
from .decorators import anydice_type_casting

# BASE FUNCTIONS


@anydice_type_casting()
def absolute(NUMBER: T_N, *args, **kwargs):
    if NUMBER < 0:
        return -NUMBER
    return NUMBER


@anydice_type_casting()
def contains(SEQUENCE: T_S, NUMBER: T_N, *args, **kwargs):
    return (SEQUENCE == NUMBER) > 0


@anydice_type_casting()
def count_in(VALUES: T_S, SEQUENCE: T_S, *args, **kwargs):
    COUNT = 0
    for P in range(1, len(VALUES) + 1):
        COUNT = COUNT + (P @ VALUES == SEQUENCE)
    return COUNT


@anydice_type_casting()
def reverse_VANILLA_SLOW(SEQUENCE: T_S, *args, **kwargs):
    R = Seq()
    for P in range(1, len(SEQUENCE) + 1):
        R = Seq(P @ SEQUENCE, R)
    return R


@anydice_type_casting()
def reverse(SEQUENCE: T_S, *args, **kwargs):
    return Seq(SEQUENCE._seq[::-1])


@anydice_type_casting()
def maximum_of(DIE: T_D, *args, **kwargs):
    return 1 @ reverse(Seq(DIE))


@anydice_type_casting()
def explode(DIE: T_D, *args, depth=None, **kwargs):
    if depth is None:
        depth = SETTINGS['explode depth']
    MAX = maximum_of(DIE)
    return _explode_helper(DIE, MAX, ORIG_DIE=DIE, depth=depth)  # type: ignore


@anydice_type_casting()
def _explode_helper(N: T_N, MAX: T_N, ORIG_DIE: T_D, depth):
    if N == MAX and depth > 0:
        return N + _explode_helper(ORIG_DIE, MAX, ORIG_DIE=ORIG_DIE, depth=depth - 1)  # type: ignore
    return N


@anydice_type_casting()
def highest_N_of_D(NUMBER: T_N, DICE: T_D, *args, **kwargs):
    return Seq(range(1, NUMBER + 1)) @ DICE


@anydice_type_casting()
def lowest_N_of_D(NUMBER: T_N, DICE: T_D, *args, **kwargs):
    return Seq(range((len(DICE) - NUMBER + 1), len(DICE) + 1)) @ DICE


@anydice_type_casting()
def middle_N_of_D(NUMBER: T_N, DICE: T_D, *args, **kwargs):
    if NUMBER == len(DICE):
        return DICE

    if NUMBER == 1:
        return (1 + (len(DICE) - 1) // 2) @ DICE

    FROM = 1 + (len(DICE) - NUMBER) // 2
    TO = FROM + NUMBER - 1
    return Seq(range(FROM, TO + 1)) @ DICE


@anydice_type_casting()
def highest_of_N_and_N(A: T_N, B: T_N, *args, **kwargs):
    if A > B:
        return A
    return B


@anydice_type_casting()
def lowest_of_N_and_N(A: T_N, B: T_N, *args, **kwargs):
    if A < B:
        return A
    return B


@anydice_type_casting()
def sort_VANILLA_SLOW(SEQUENCE: T_S, *args, **kwargs):
    SORTED = Seq()
    for P in range(1, len(SEQUENCE) + 1):
        SORTED = _sort_helper_add_N_to_S(P @ SEQUENCE, SORTED)  # type: ignore
    return SORTED


@anydice_type_casting()
def _sort_helper_add_N_to_S(N: T_N, S: T_S, *args, **kwargs):
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


@anydice_type_casting()
def sort(SEQUENCE: T_S, *args, **kwargs):
    return Seq(sorted(SEQUENCE, reverse=True))

# MORE FUNCTIONS


@anydice_type_casting()
def gwf(num_die: T_N, dmg_die, min_to_reroll=2, *args, **kwargs):
    assert isinstance(num_die, int), 'great weapon fighting must get int as number of die and faces of dmg die'
    if isinstance(dmg_die, int):  # prevent making RV as constant int
        dmg_die = roll(1, dmg_die)
    single_gwf = _gwf_helper(roll_1=dmg_die, dmg_die=dmg_die, min_to_reroll=min_to_reroll)  # type: ignore
    return roll(num_die, single_gwf)


@anydice_type_casting()
def _gwf_helper(roll_1: T_N, dmg_die: T_D, min_to_reroll: T_N, *args, **kwargs):
    if roll_1 <= min_to_reroll:
        return dmg_die
    return roll_1
