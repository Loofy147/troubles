import time, sys, subprocess as sp, cProfile, pstats, io
from functools import wraps

_log = {} # name -> [n, sum_ns, min_ns, max_ns]
_T = time.perf_counter_ns

def _fmt(ns):
    if ns < 1000: return f"{ns}ns"
    if ns < 1000000: return f"{ns/1000:.1f}µs"
    if ns < 1000000000: return f"{ns/1000000:.1f}ms"
    return f"{ns/1000000000:.3f}s"

def _emit(name, ns):
    if name not in _log:
        _log[name] = [1, ns, ns, ns]
        print(f"⚡ {name}  {_fmt(ns)}", file=sys.stderr)
    else:
        s = _log[name]
        s[0] += 1; s[1] += ns
        if ns < s[2]: s[2] = ns
        if ns > s[3]: s[3] = ns
        n = s[0]
        if n in {2, 5, 10, 50, 100} or n % 100 == 0:
            print(f"⚡ {name}  ×{n}  μ={_fmt(s[1]//n)}  [{_fmt(s[2])}…{_fmt(s[3])}]", file=sys.stderr)

class bolt:
    """@bolt | @bolt('l') | with bolt('l'): | bolt(fn,*a,**k) | CLI shim"""
    __slots__ = ('_l', '_t')

    def __new__(cls, x=None, *a, **k):
        if callable(x) and not a and not k:
            @wraps(x)
            def w(*a,**k): t=_T(); r=x(*a,**k); _emit(x.__name__, _T()-t); return r
            return w
        if callable(x):
            t=_T(); r=x(*a,**k); _emit(getattr(x,'__name__','fn'), _T()-t); return r
        return super().__new__(cls)

    def __init__(self, x="block"): self._l = x

    def __call__(self, f):
        @wraps(f)
        def w(*a,**k): t=_T(); r=f(*a,**k); _emit(self._l, _T()-t); return r
        return w

    def __enter__(self): self._t = _T(); return self
    def __exit__(self, *_): _emit(self._l, _T()-self._t)

    @staticmethod
    def deep(f, *a, top=8, **k):
        pr = cProfile.Profile(); r = pr.runcall(f, *a, **k); s = io.StringIO()
        pstats.Stats(pr, stream=s).strip_dirs().sort_stats('cumtime').print_stats(top)
        print(s.getvalue(), file=sys.stderr); return r

    @staticmethod
    def stats(name=None):
        for n, s in ({name:_log[name]} if name else _log).items():
            print(f"{n:20s} n={s[0]:>5}  total={_fmt(s[1])}  μ={_fmt(s[1]//s[0])}  "
                  f"min={_fmt(s[2])}  max={_fmt(s[3])}")

    @staticmethod
    def reset(): _log.clear()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        t = _T(); r = sp.run(sys.argv[1:]); _emit("run", _T()-t)
