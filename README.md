# ⚡ Bolt

Performance-obsessed, ultra-compact profiling toolkit for Python, C, and Rust.

## Features

- **Multi-Language**: Native high-performance implementations for Python, C, and Rust.
- **Zero-Latency Bypass**: Production modes for near-zero runtime overhead.
- **High-Precision Stats**: Mean (μ) and Standard Deviation (σ) with nanosecond resolution.
- **O(1) C Lookup**: Hash-based label lookup in C for scalable performance.
- **Zero-Allocation Rust**: Uses `Cow<'static, str>` for zero-heap static labels.
- **Self-Diagnostics**: Integrated `check()` methods to measure profiling tax.

## Python
```python
from bolt import bolt
bolt.check() # measures profiling overhead
with bolt[0]: ...
```

## C (Header-only)
```c
#include "bolt.h"
BOLT_CHECK(); // measures overhead
BOLT("io", { ... });
```

## Rust
```rust
use bolt::bolt;
bolt::check(); // measures overhead
bolt!("compute", { ... });
```

## Performance Validation (Next-Level Benchmarks)

| Language | Profiling Tax | Architecture | Precision |
|----------|---------------|--------------|-----------|
| Python   | ~4.8µs        | Streamlined  | ns        |
| C        | ~66ns         | O(1) Hash    | ns        |
| Rust     | ~106ns        | Zero-Alloc   | ns        |

### Production Bypass
- **Python**: `BOLT_OFF=1`
- **C**: `#define BOLT_OFF`
- **Rust**: `#[cfg(feature = "bolt_off")]`
