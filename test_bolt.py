import os, sys, time

def test_on():
    print("\n--- Testing BOLT_ON ---")
    if "bolt" in sys.modules: del sys.modules["bolt"]
    os.environ.pop("BOLT_OFF", None)
    import bolt

    # Decorator
    @bolt.bolt
    def fast(): return 1
    assert fast() == 1

    # Context Manager
    with bolt.bolt("ctx"):
        time.sleep(0.01)

    # Direct Call
    res = bolt.bolt(sum, [1, 2])
    assert res == 3

    # Deep
    res = bolt.bolt.deep(sum, [1, 2])
    assert res == 3

    bolt.bolt.stats()
    print("Test ON: Passed")

def test_off():
    print("\n--- Testing BOLT_OFF ---")
    if "bolt" in sys.modules: del sys.modules["bolt"]
    os.environ["BOLT_OFF"] = "1"
    import bolt

    # Decorator
    def fn(): return 1
    wrapped = bolt.bolt(fn)
    assert wrapped is fn
    assert wrapped() == 1

    # Parameterized Decorator
    wrapped2 = bolt.bolt("label")(fn)
    assert wrapped2 is fn

    # Context Manager
    with bolt.bolt("ctx"):
        pass # Should not crash

    # Direct Call
    res = bolt.bolt(sum, [1, 2])
    assert res == 3

    # Deep
    res = bolt.bolt.deep(sum, [1, 2])
    assert res == 3

    bolt.bolt.stats() # Should be empty but not crash
    print("Test OFF: Passed")

if __name__ == "__main__":
    test_on()
    test_off()
    print("\nAll Robust Negative Space tests passed!")
