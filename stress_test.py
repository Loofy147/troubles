import time, os, random, sys
from bolt import bolt, _L

def no_op(): pass

@bolt
def profiled_no_op(): pass

def run_bench(n=10**7):
    print(f"--- Stress Test: {n} iterations ---")

    # 1. Measure Raw Latency
    t0 = time.perf_counter_ns()
    for _ in range(n): no_op()
    raw_ns = (time.perf_counter_ns() - t0) / n
    print(f"Raw no-op: {raw_ns:.1f}ns/call")

    # 2. Measure Bolt Latency (Stress)
    t0 = time.perf_counter_ns()
    for _ in range(n): profiled_no_op()
    bolt_ns = (time.perf_counter_ns() - t0) / n
    tax = bolt_ns - raw_ns
    print(f"Bolt no-op: {bolt_ns:.1f}ns/call")
    print(f"Profiling Tax: {tax:.1f}ns/call")

    # 3. Verify Memory Stability
    print(f"Internal Log Size: {len(_L)} entries (O(1) Check)")
    assert len(_L) == 1

    # 4. Verify Accuracy with Jitter
    print("\n--- Jitter Accuracy Test ---")
    @bolt("jitter")
    def jitter_fn():
        # Random sleep between 1ms and 5ms
        time.sleep(random.uniform(0.001, 0.005))

    for _ in range(100): jitter_fn()
    bolt.stats("jitter")

    # 5. Pipeline Stress
    print("\n--- Pipeline Stress Test ---")
    bolt.register("A", "B", "C")
    for _ in range(1000):
        with bolt[0]: pass
        with bolt[1]: time.sleep(0.001)
        with bolt[2]: pass
    bolt.pipeline()

if __name__ == "__main__":
    run_bench()
