import time, sys, subprocess as sp
def bolt(f, *a, **k):
    t = time.perf_counter()
    r = f(*a, **k)
    print(f"{getattr(f, '__name__', 'task')} took {time.perf_counter()-t:.4f}s")
    return r
if __name__ == "__main__":
    if len(sys.argv) > 1: bolt(sp.run, sys.argv[1:])
