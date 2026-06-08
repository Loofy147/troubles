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
