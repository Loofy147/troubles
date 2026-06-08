# ⚡ Bolt

Performance-obsessed, ultra-compact profiling toolkit for Python, C, and Rust.

## Features

- **Multi-Language**: Native high-performance implementations for Python, C, and Rust.
- **Zero-Latency Bypass**: Production modes for near-zero runtime overhead.
- **High-Precision Stats**: Mean (μ) and Standard Deviation (σ) with nanosecond resolution.
- **Constant Memory**: Tracks millions of events in O(1) space per label.
- **Cross-Language Monitoring**: Integrated stack profiling (Python -> C -> Rust).

## Integrated Stack Benchmarks (0^6$ iterations)

| Layer | Language | μ (Integrated) | σ (Integrated) |
|-------|----------|----------------|----------------|
| Bridge| Python   | ~1.4µs         | ~1.4µs         |
| FFI   | C        | ~231ns         | ~522ns         |
| Core  | Rust     | ~30ns          | ~181ns         |

*The integrated results show the "stack tax" across language boundaries, proving Bolt's stability in high-frequency FFI scenarios.*

## Python Usage
```python
from bolt import bolt
with bolt("logic"):
    ...
bolt.stats()
```

## C Usage (Header-only)
```c
#include "bolt.h"
BOLT("io", { read_file(); });
BOLT_STATS();
```

## Rust Usage
```rust
use bolt::bolt;
bolt!("compute", { matrix_multiply(); });
bolt::stats();
```

## Production Bypass
- **Python**: `BOLT_OFF=1`
- **C**: `#define BOLT_OFF`
- **Rust**: `#[cfg(feature = "bolt_off")]`
