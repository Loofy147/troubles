# ⚡ Bolt

A performance-obsessed, robust profiling utility with advanced precision statistics and zero-latency bypass.

## Features

- **Precision Stats**: Tracks mean (μ) and standard deviation (σ) for repeated tasks.
- **Hotspot Ranking**: Rank slow functions by mean execution time with `bolt.top()`.
- **Zero-Overhead Bypass**: Toggle with `BOLT_OFF=1` for production safety.
- **Custom Sinks**: Redirect metrics to a file with `BOLT_OUT=path/to/log`.
- **Deep Profiling**: Full `cProfile` integration via `bolt.deep(fn)`.
- **Compact API**: Supports decorators, context managers, and direct calls.

## Usage

### High-Precision Tracking
```python
from bolt import bolt

@bolt
def repeat_task():
    ...

# After many runs, metrics will show μ and σ
bolt.stats()
```

### Hotspot Identification
```python
# Shows top 5 slowest tasks by mean time
bolt.top(n=5)
```

### Custom Output Sink
```bash
BOLT_OUT=performance.log python3 my_app.py
```

### Production Bypass
```bash
BOLT_OFF=1 python3 my_app.py  # Utility disappears from runtime
```
