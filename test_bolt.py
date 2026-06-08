import time
from bolt import bolt

def test_cpu_bound(n):
    return sum(i*i for i in range(n))

def test_io_bound(s):
    time.sleep(s)
    return "done"

if __name__ == "__main__":
    print("Testing CPU bound...")
    res_cpu = bolt(test_cpu_bound, 10**6)
    assert res_cpu == sum(i*i for i in range(10**6))

    print("\nTesting IO bound...")
    res_io = bolt(test_io_bound, 0.1)
    assert res_io == "done"

    print("\nAll tests passed!")
