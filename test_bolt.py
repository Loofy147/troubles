import time
import io
import contextlib
from bolt import bolt

@bolt
def decorated_func(n):
    return sum(i*i for i in range(n))

def normal_func(n):
    return sum(i*i for i in range(n))

if __name__ == "__main__":
    f = io.StringIO()
    with contextlib.redirect_stderr(f):
        print("Testing @bolt decorator...")
        res = decorated_func(10**5)
        assert res == sum(i*i for i in range(10**5))

        print("Testing direct bolt call...")
        res = bolt(normal_func, 10**5)
        assert res == sum(i*i for i in range(10**5))

        print("Testing context manager...")
        with bolt("custom_block"):
            time.sleep(0.05)

    output = f.getvalue()
    print("\nCaptured stderr output:")
    print(output)

    assert "decorated_func" in output
    assert "normal_func" in output
    assert "custom_block" in output

    print("\nAll tests passed!")
