# ⚡ Bolt

A performance-obsessed, compact, and adaptive profiling utility with rolling statistics and deep diagnostics.

## Features

- **Decorator**: Profile functions with `@bolt` or `@bolt("label")`.
- **Context Manager**: Profile specific blocks with `with bolt("label"):`.
- **Rolling Statistics**: Automatically tracks min, max, and average execution times for repeated tasks without unbounded memory growth.
- **Deep Profiling**: Use `bolt.deep(fn)` for full `cProfile` integration.
- **Precision**: Uses `time.perf_counter_ns` for high-resolution timing.
- **CLI Shim**: Profile shell commands directly.

## Usage

### Decorators
```python
from bolt import bolt

@bolt
def fast_task():
    ...

@bolt("custom_label")
def another_task():
    ...
```

### Deep Profiling & Stats
```python
from bolt import bolt

# Detailed cProfile report
bolt.deep(my_function, arg1, kwarg=1)

# Summary report of all timed tasks
bolt.stats()
```

### CLI
```bash
python3 bolt.py sleep 1
```
