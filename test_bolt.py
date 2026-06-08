import os, sys, time

def test_on():
    print("\n--- Testing BOLT_ON (Standard) ---")
    if "bolt" in sys.modules: del sys.modules["bolt"]
    os.environ.pop("BOLT_OFF", None)
    os.environ.pop("BOLT_OUT", None)
    import bolt
    @bolt.bolt
    def fast(): pass
    fast()
    bolt.bolt.stats()
    print("Test ON: Passed")

def test_sigma_and_top():
    print("\n--- Testing Sigma and Top ---")
    if "bolt" in sys.modules: del sys.modules["bolt"]
    os.environ.pop("BOLT_OFF", None)
    os.environ.pop("BOLT_OUT", None)
    import bolt
    @bolt.bolt
    def variable_fn(s):
        time.sleep(s)
    for s in [0.01, 0.02, 0.01]:
        variable_fn(s)
    bolt.bolt.top(n=1)
    print("Test Sigma/Top: Passed")

def test_off():
    print("\n--- Testing BOLT_OFF (Zero-Overhead) ---")
    if "bolt" in sys.modules: del sys.modules["bolt"]
    os.environ["BOLT_OFF"] = "1"
    import bolt
    def fn(): return 1
    assert bolt.bolt(fn) is fn
    print("Test OFF: Passed")

def test_bolt_out():
    print("\n--- Testing BOLT_OUT (File Sink) ---")
    if "bolt" in sys.modules: del sys.modules["bolt"]
    os.environ["BOLT_OUT"] = "bolt_metrics.log"
    os.environ.pop("BOLT_OFF", None)
    if os.path.exists("bolt_metrics.log"): os.remove("bolt_metrics.log")
    import bolt
    @bolt.bolt
    def logged(): pass
    logged()
    with open("bolt_metrics.log", "r") as f:
        content = f.read()
        assert "logged" in content
    os.remove("bolt_metrics.log")
    print("Test BOLT_OUT: Passed")

if __name__ == "__main__":
    test_on()
    test_sigma_and_top()
    test_off()
    test_bolt_out()
    print("\nAll Comprehensive Tests Passed!")
