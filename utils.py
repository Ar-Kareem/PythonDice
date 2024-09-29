from typing import Iterable 


def flatten(items):
    """Yield items from any nested iterable; see Reference.  https://stackoverflow.com/a/40857703/6173665"""
    for x in items:
        if isinstance(x, Iterable):
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x
