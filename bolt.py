import time, sys, subprocess as sp
from functools import wraps

class bolt:
    """@bolt | with bolt('x'): | bolt(fn,*a,**k) | CLI shim"""
    __slots__ = ('_l', '_t')

    def __new__(cls, f=None, *a, **k):
        if callable(f) and not a and not k:           # @bolt → transparent wrap
            @wraps(f)
            def w(*a, **k): return cls._tick(f, *a, **k)
            return w
        if callable(f): return cls._tick(f, *a, **k)  # bolt(fn,...) → timed call
        return super().__new__(cls)                    # with bolt('x'): → ctx

    def __init__(self, label="block"):
        if isinstance(label, str): self._l, self._t = label, 0

    def __enter__(self): self._t = time.perf_counter(); return self
    def __exit__(self, *_):
        print(f"{self._l} {time.perf_counter()-self._t:.4f}s", file=sys.stderr)

    @staticmethod
    def _tick(f, *a, **k):
        s = time.perf_counter(); r = f(*a, **k)
        print(f"{getattr(f,'__name__','fn')} {time.perf_counter()-s:.4f}s", file=sys.stderr)
        return r

if __name__ == "__main__":
    sys.argv[1:] and bolt(sp.run, sys.argv[1:])
