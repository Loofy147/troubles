# ⚡ Bolt

Performance-obsessed, ultra-compact profiling toolkit for Python, C, and Rust.

## Technical Architecture

```mermaid
graph TD
    User([User Code]) --> B{Bolt Interface}
    B -- Decorator/Macro --> T[Timing Logic]
    B -- Context Manager --> T
    B -- Direct Call --> T

    T --> P{Bypass Active?}
    P -- Yes (BOLT_OFF) --> O[Return Original]
    P -- No --> M[Measure Latency]

    M --> S[(Constant Space Stats)]
    S --> D{Diagnostics}
    D --> Deep[cProfile/Deep]
    D --> Stats[μ, σ Aggregation]
    D --> Pipe[Pipeline Mapping]

## Logic & Dispatcher Flow

Bolt uses a multi-pattern dispatcher to adapt to various usage scenarios with minimal friction.

```mermaid
flowchart LR
    A[bolt class/macro] --> B{Input Type}
    B -- Callable --> C{Args Present?}
    C -- No --> D[Decorator/Wrapper]
    C -- Yes --> E[Immediate Execution]
    B -- Str/Int --> F[Context Manager/Indexed Layer]

    subgraph "Internal State (O(1))"
    G[Count n]
    H[Total Time Σ]
    I[Sum of Squares Σ²]
    J[Min/Max]
    end

    D & E & F --> M[Timing Start]
    M --> Task[Run Task]
    Task --> Z[Timing End]
    Z --> G & H & I & J
```

## Multi-Language Reference

| Feature | Python (`bolt.py`) | C (`bolt.h`) | Rust (`bolt.rs`) |
|---------|--------------------|---------------|-------------------|
| **Core**| Class-based | Macro-based | RAII-based |
| **Precision** | `perf_counter_ns` | `clock_gettime` | `Instant::now()` |
| **Lookup** | Dict (Hybrid State) | O(1) Additive Hash | OnceLock/Mutex HashMap |
| **Labels** | Dynamic Str/Int | Static Char[32] | Cow<'static, str> |
| **Bypass** | `BOLT_OFF` Env | `#define BOLT_OFF` | `cfg(bolt_off)` |

## Formulas

- **Mean (μ)**: $\Sigma / n$
- **Standard Deviation (σ)**: $\sqrt{\Sigma^2/n - (\Sigma/n)^2}$

## Benchmarks (10^7$ iterations)

- **C**: ~66ns overhead
- **Rust**: ~106ns overhead
- **Python**: ~4.8µs overhead (1.6µs per raw call wrapper)

---

### Usage Examples

#### Pipeline Mapping (Python)
```python
bolt.register("input", "logic", "output")
with bolt[1]: # Profile as "logic"
    process()
bolt.pipeline()
```

#### Header-only (C)
```c
BOLT("task", { heavy_compute(); });
BOLT_STATS();
```

#### Zero-Allocation (Rust)
```rust
bolt!("core", { compute(); });
bolt::stats();
```

## Production Safety (The "Tripwire" & "Epoch")

Bolt includes built-in safeties to prevent telemetry from becoming a bottleneck under production-level traffic.

### ⚡ Automated Tripwire
If the internal "Bolt Tax" (overhead) exceeds a configurable percentage of the task execution time, Bolt will automatically pull the rip-cord and globally bypass all profiling logic. This ensures that a degraded node never crashes or overflows buffers due to telemetry overhead.

### 🔄 Sliding Epoch Window
To prevent historical metrics from stagnating, Bolt can be configured with an Epoch limit. After reaching $N$ samples, the metrics are reset (or soft-reset depending on implementation), providing a sliding window view of performance.

### Usage

**Python**
```python
bolt.arm(e=10000, r=0.05) # 10k samples epoch, 5% max overhead tripwire
```

**C**
```c
BOLT_ARM(10000, 0.05, 60); // Epoch, Ratio, Estimated Tax (ns)
```

**Rust**
```rust
bolt::arm(10000, 0.05, 100); // Epoch, Ratio, Estimated Tax (ns)
```

## 🛡️ Forward Security/Coding (FSC) Engine

The FSC engine (`fsc.py`) is a high-performance Reed-Solomon coding implementation designed for both **Error Correction** (recovering corrupted data at known/unknown positions) and **Erasure Coding** (reconstructing missing shards in a himBHsof-$ swarm).

### Architecture
- **Geometric Projection**: Replaces (C(m, e) \cdot e^3)$ combinatorial brute-force with (m \cdot e^2)$ overdetermined RREF projections in GF(p).
- **Deterministic Latency**: Achieves sub-millisecond recovery times suitable for real-time media streaming and high-throughput networking.
- **Unified Manifold**: Both Error Correction and Erasure Coding share optimized linear algebra kernels.

---

## ⚖️ Design Arguments & Trade-offs

### 1. Zero-Latency Bypass vs. Code Readability
**Bypass**: `BOLT_OFF` environment checks are performed at the entry point of every call. While this adds a few nanoseconds of branch-prediction "tax" to the hot path, it allows the library to return original objects directly, effectively removing the profiling logic from the stack entirely when disabled.
**Trade-off**: The implementation uses dense, compacted logic to minimize the footprint of this bypass check.

### 2. Constant-Space Statistics vs. Precise History
**Constant-Space**: Bolt tracks only $, $\Sigma t$, $\Sigma t^2$, $, and $. This ensures (1)$ memory overhead regardless of sample count.
**Trade-off**: Full latency distributions (e.g., p99 percentiles) cannot be calculated from these metrics. However, the inclusion of Standard Deviation ($\sigma$) provides a sufficient proxy for performance jitter analysis without the memory tax of a sliding buffer or histogram.

### 3. FFI Stability vs. Language Idioms
Bolt prioritizes a unified telemetry output format (`⚡ Label μ=... σ=...`) across Python, C, and Rust. This ensures that architectural pipelines spanning multiple FFI boundaries can be analyzed as a single, coherent stream of execution.
