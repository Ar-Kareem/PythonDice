from typing import Iterable, Union, TYPE_CHECKING

if TYPE_CHECKING:  # https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
  from .randvar import RV
  from .blackrv import BlankRV


# TYPE DEFINITIONS
T_if = Union[int, float]
T_ifs = Union[T_if, Iterable['T_ifs']]  # recursive type
T_is = Union[int, Iterable['T_is']]  # recursive type

T_isr = Union[T_is, 'RV', 'BlankRV']
T_ifr = Union[T_if, 'RV', 'BlankRV']
T_ifsr = Union[T_ifs, 'RV', 'BlankRV']

T_s = Iterable['T_ifs']  # same as T_ifs but excludes int and float (not iterable)
