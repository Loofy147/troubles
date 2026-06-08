import time, io, contextlib, sys
from bolt import bolt, _log

@bolt
def fast_fn(): pass

@bolt("custom")
def custom_fn(): pass

def normal_fn():
    time.sleep(0.01)

if __name__ == "__main__":
    err = io.StringIO()
    out = io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
        print("Testing rolling stats...")
        for _ in range(5):
            fast_fn()

        print("Testing custom label decorator...")
        custom_fn()

        print("Testing context manager...")
        with bolt("block"):
            normal_fn()

        print("Testing deep profiling...")
        bolt.deep(normal_fn)

        print("\nFinal Stats Report:")
        bolt.stats()

    stderr_out = err.getvalue()
    stdout_out = out.getvalue()

    print("\nCaptured Stderr:", file=sys.stderr)
    print(stderr_out, file=sys.stderr)

    print("\nCaptured Stdout:")
    print(stdout_out)

    # Assertions
    assert "fast_fn  ×2" in stderr_out
    assert "fast_fn  ×5" in stderr_out
    assert "custom" in stderr_out
    assert "block" in stderr_out
    assert "normal_fn" in stderr_out # from deep profiling

    # Verify stats output
    assert "fast_fn" in stdout_out
    assert "n=    5" in stdout_out

    # Verify memory efficiency: _log should have 3 entries (fast_fn, custom, block)
    assert len(_log) == 3
    for key in _log:
        assert len(_log[key]) == 4 # [n, sum, min, max]

    print("\nAll tests passed!")
