# ⚡ Bolt

A performance-obsessed, compact profiling utility with pipeline architectural mapping and zero-latency bypass.

## Features

- **Pipeline Mapping**: Register architectural layers with `bolt.register()` and visualize bottlenecks with `bolt.pipeline()`.
- **Index Access**: Access registered layers via `bolt[idx]` syntax.
- **Precision Stats**: Tracks mean (μ) and standard deviation (σ) for all tasks.
- **Hotspot Ranking**: Identify slow functions with `bolt.top()`.
- **Zero-Overhead Bypass**: Toggle with `BOLT_OFF=1` for production safety.
- **Custom Sinks**: Redirect metrics to a file with `BOLT_OUT=path`.

## Usage

### Layer Registration & Pipelines
```python
from bolt import bolt

# Register architectural layers
bolt.register("db_fetch", "logic", "serialize")

# Use index-based profiling
with bolt[0]:  # Profiles as "db_fetch"
    ...

@bolt[1]  # Profiles as "logic"
def process_data():
    ...

# Visualize the pipeline flow
bolt.pipeline()
```

### Output
```text
── pipeline ──
  [ 0] db_fetch             μ=45.2ms  σ=2.1ms  40%  cum=45.2ms
  [ 1] logic                μ=56.8ms  σ=5.4ms  50%  cum=102.0ms
  [ 2] serialize            μ=11.3ms  σ=0.5ms  10%  cum=113.3ms
```

### Global Stats & Deep Profiling
```python
bolt.stats()
bolt.top(n=5)
bolt.deep(heavy_fn)
```
