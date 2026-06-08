# ⚡ Bolt

Performance-obsessed, compact profiling utility with pipeline architectural mapping and zero-latency bypass.

## Design Arguments

- **Zero-Latency Bypass**: Robust `BOLT_OFF` mode returns original functions directly, avoiding any wrapper overhead in production.
- **Constant Memory Stats**: Tracks min, max, mean (μ), and standard deviation (σ) using fixed-space accumulators.
- **Architectural Mapping**: Maps performance bottlenecks to system layers via `bolt.register()` and `bolt[idx]`.
- **Extreme Compaction**: Integrated diagnostics (deep profiling, statistics, ranking) in a minimal physical footprint (~3KB).

## Stress Test Benchmarks

- **Throughput**: Verified at 10^6+ iterations.
- **Memory Overhead**: Constant O(1) space complexity per tracked label.
- **Profiling Tax**: Approximately 1.6µs per decorated call (Python 3.12).
- **Accuracy**: Reliable μ and σ calculation for high-jitter workloads.

## Usage

### Pipeline Mapping
```python
from bolt import bolt
bolt.register("input", "logic", "output")

with bolt[0]:  # Profiles as "input"
    ...

bolt.pipeline() # Bottleneck visualization
```

### Precision Statistics
```python
@bolt("heavy_task")
def task(): ...

# Shows μ, σ, min, max, total
bolt.stats()
```

### CLI & Environment
```bash
BOLT_OUT=perf.log python3 app.py  # Redirect to file
BOLT_OFF=1 python3 app.py        # Complete bypass
python3 bolt.py sleep 1          # CLI shim
```
