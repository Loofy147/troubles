import os, sys, time, io, contextlib
from bolt import bolt

def test_pipeline():
    print("\n--- Testing Pipeline and Indexing ---")
    if "bolt" in sys.modules: del sys.modules["bolt"]
    os.environ.pop("BOLT_OFF", None)
    import bolt

    # Registration
    bolt.bolt.register("input", "transform", "output")

    # Use index-based context managers
    with bolt.bolt[0]: # input
        time.sleep(0.01)

    with bolt.bolt[1]: # transform
        time.sleep(0.02)

    with bolt.bolt[2]: # output
        time.sleep(0.01)

    # Use index-based decorator
    @bolt.bolt[1]
    def extra_transform():
        time.sleep(0.01)

    extra_transform()

    print("\nPipeline report:")
    bolt.bolt.pipeline()
    print("Test Pipeline: Passed")

def test_off_pipeline():
    print("\n--- Testing BOLT_OFF with Pipeline ---")
    if "bolt" in sys.modules: del sys.modules["bolt"]
    os.environ["BOLT_OFF"] = "1"
    import bolt

    bolt.bolt.register("input")

    # Context manager should not crash
    with bolt.bolt[0]:
        pass

    # Decorator should return original function
    def fn(): return 1
    assert bolt.bolt[0](fn) is fn

    print("Test OFF Pipeline: Passed")

if __name__ == "__main__":
    test_pipeline()
    test_off_pipeline()
    print("\nAll Advanced Pipeline Tests Passed!")
