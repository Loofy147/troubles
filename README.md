# ⚡ Bolt

Performance-obsessed, ultra-compact profiling toolkit for Python, C, and Rust.

## Features

- **Multi-Language**: Native high-performance implementations for Python, C, and Rust.
- **Zero-Latency Bypass**: Production modes for near-zero runtime overhead.
- **Architectural Mapping**: Maps bottlenecks to system layers via `bolt.register()`.
- **Cloned Isolation**: Independent state management for cloned or nested utility usage.
- **High-Precision Stats**: Mean (μ) and Standard Deviation (σ) with nanosecond resolution.

## Python
```python
from bolt import bolt
bolt.register("db", "logic")

with bolt[0]: # architectural layer
    ...

@bolt("custom") # labeled decorator
def fn(): ...

bolt.pipeline() # bottleneck report
bolt.stats()     # global summary
```

## Nested & Cloned Usage
Bolt ⚡ supports independent isolation if the module is cloned. This allows nested profiling without state collision:
```python
import bolt, bolt_copy
@bolt.bolt("outer")
@bolt_copy.bolt("inner")
def task(): ...
```

## Design & Benchmarks

| Language | Overhead/Call | Footprint | Memory |
|----------|---------------|-----------|--------|
| Python   | ~1.6µs        | ~3KB      | O(1)   |
| C        | ~26ns         | Header    | O(1)   |
| Rust     | ~30ns         | Module    | O(1)   |

### Production Bypass
- **Python**: `BOLT_OFF=1`
- **C**: `#define BOLT_OFF`
- **Rust**: `#[cfg(feature = "bolt_off")]`
