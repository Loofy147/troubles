# ⚡ Bolt

Performance-obsessed, ultra-compact profiling toolkit for Python, C, and Rust.

## Features

- **Multi-Language**: Native high-performance implementations for Python, C, and Rust.
- **Zero-Latency Bypass**: Production modes for near-zero runtime overhead.
- **High-Precision Stats**: Mean (μ) and Standard Deviation (σ) with nanosecond resolution.
- **Constant Memory**: Tracks millions of events in O(1) space per label.

## Python
```python
from bolt import bolt
with bolt("logic"):
    ...
bolt.stats()
```

## C (Header-only)
```c
#include "bolt.h"
BOLT("io", { read_file(); });
BOLT_STATS();
```

## Rust
```rust
use bolt::bolt;
bolt!("compute", { matrix_multiply(); });
bolt::stats();
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
