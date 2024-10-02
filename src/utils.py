from typing import Iterable, TypeVar


T = TypeVar('T')
T_flat = Iterable[T]
T_ifs = T|Iterable['T_ifs']  # recursive type
T_s = Iterable['T_ifs']  # same as T_ifs but excludes int and float (not iterable)

def flatten(items: T_s) -> T_flat:
    """Yield items from any nested iterable; see Reference.  https://stackoverflow.com/a/40857703/6173665"""
    for x in items:
        if isinstance(x, Iterable):
            assert not isinstance(x, str), "flatten() does not support strings"
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x

_memoized = {}
def factorial(n: int):
    if n not in _memoized:
        _memoized[n] = n * factorial(n-1) if n > 1 else 1
    return _memoized[n]