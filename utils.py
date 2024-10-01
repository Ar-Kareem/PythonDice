from typing import Iterable 


def flatten(items):
    """Yield items from any nested iterable; see Reference.  https://stackoverflow.com/a/40857703/6173665"""
    for x in items:
        if isinstance(x, Iterable):
            assert not isinstance(x, str), "flatten() does not support strings"
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x

_memoized = {}
def factorial(n):
    if n not in _memoized:
        _memoized[n] = n * factorial(n-1) if n > 1 else 1
    return _memoized[n]