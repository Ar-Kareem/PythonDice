from typing import Iterable, TypeVar, Union


T = TypeVar('T')
T_flat = Iterable[T]
T_ifs = Union[T, Iterable['T_ifs']]  # recursive type
T_s = Iterable['T_ifs']  # same as T_ifs but excludes int and float (not iterable)


def flatten(items: T_s) -> T_flat:
    """Yield items from any nested iterable; see Reference.  https://stackoverflow.com/a/40857703/6173665"""
    for x in items:
        if isinstance(x, Iterable):
            if isinstance(x, str):
                yield x
                continue
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x


_memoized = {}


def factorial(n: int):
    if n not in _memoized:
        _memoized[n] = n * factorial(n - 1) if n > 1 else 1
    return _memoized[n]


# to handle special cases of operators on int
def mymatmul(a, b):
    if isinstance(a, int) and isinstance(b, int):  # special case for int @ int
        return int(str(b)[a - 1]) if (0 <= a - 1 < len(str(b))) else 0
    return a @ b


def mylen(a):
    if isinstance(a, int):
        return len(str(abs(a)))
    return len(a)


def myinvert(a):
    if isinstance(a, int):
        return 1 if a == 0 else 0
    return ~a


def myand(a, b):
    if isinstance(a, int) and isinstance(b, int):
        return 1 if (a and b) else 0
    return a & b


def myor(a, b):
    if isinstance(a, int) and isinstance(b, int):
        return 1 if (a or b) else 0
    return a | b


def true_div(a, b):
    return a / b
