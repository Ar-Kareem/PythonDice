
# core classes
from .randvar import RV, Seq

# core decorators
from .randvar import anydice_casting, max_func_depth

# core functions
from .randvar import output, roll, settings_set, myrange

# helpful functions
from.randvar import roller, settings_reset

# function library
from .funclib import absolute as absolute_X, contains as X_contains_X, count_in as count_X_in_X, explode as explode_X, highest_N_of_D as highest_X_of_X, lowest_N_of_D as lowest_X_of_X, middle_N_of_D as middle_X_of_X, highest_of_N_and_N as highest_of_X_and_X, lowest_of_N_and_N as lowest_of_X_and_X, maximum_of as maximum_of_X, reverse as reverse_X, sort as sort_X


from .utils import mymatmul as myMatmul, mylen as myLen, myinvert as myInvert, myand as myAnd, myor as myOr
