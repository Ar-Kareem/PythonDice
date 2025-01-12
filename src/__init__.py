__version__ = '0.3.6'

# core classes
from .randvar import RV
from .seq import Seq
from .factory import get_seq

# core functions
from .roller import myrange
from .settings import settings_set
from .output import output
from .blackrv import BlankRV

# core decorators
from .decorators import anydice_casting, anydice_type_casting, max_func_depth
from .typings import T_N, T_S, T_D

# helpful functions
from .settings import settings_reset
from .roller import roll, roller
from .string_rvs import StringSeq

# function library
from .funclib import absolute as absolute_X, contains as X_contains_X, count_in as count_X_in_X, explode as explode_X, highest_N_of_D as highest_X_of_X
from .funclib import lowest_N_of_D as lowest_X_of_X, middle_N_of_D as middle_X_of_X, highest_of_N_and_N as highest_of_X_and_X, lowest_of_N_and_N as lowest_of_X_and_X
from .funclib import maximum_of as maximum_of_X, reverse as reverse_X, sort as sort_X


from .utils import mymatmul as myMatmul, mylen as myLen, myinvert as myInvert, myand as myAnd, myor as myOr


__all__ = [
  'RV', 'Seq', 'anydice_casting', 'anydice_type_casting', 'BlankRV', 'max_func_depth', 'output', 'roll', 'settings_set', 'myrange',
  'T_N', 'T_S', 'T_D',
  'roller', 'settings_reset', 'StringSeq', 'get_seq',
  'absolute_X', 'X_contains_X', 'count_X_in_X', 'explode_X', 'highest_X_of_X', 'lowest_X_of_X', 'middle_X_of_X', 'highest_of_X_and_X', 'lowest_of_X_and_X', 'maximum_of_X', 'reverse_X', 'sort_X',
  'myMatmul', 'myLen', 'myInvert', 'myAnd', 'myOr'
]
