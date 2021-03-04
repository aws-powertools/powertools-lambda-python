import time
from contextlib import contextmanager
from typing import Generator


@contextmanager
def timing() -> Generator:
    """ "Generator to quickly time operations. It can add 5ms so take that into account in elapsed time

    Examples
    --------

        with timing() as t:
            print("something")
        elapsed = t()
    """
    start = time.perf_counter()
    yield lambda: time.perf_counter() - start  # gen as lambda to calculate elapsed time
