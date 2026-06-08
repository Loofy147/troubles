## 2025-05-15 - Hot Path Dictionary Lookups
**Learning:** In high-frequency performance profiling, the overhead of `dict.get()` followed by a truthiness check is measurably higher than a `try-except` block when the key is expected to exist most of the time (the common path).
**Action:** Use `try-except` for dictionary lookups in hot paths where keys are repeatedly accessed after initial creation.
## 2025-05-15 - Closure-Based Statistics Caching
**Learning:** For utilities used as decorators or context managers, capturing stateful objects (like lists used for statistics) in a closure at initialization time is significantly faster than performing repeated dictionary lookups during the measured execution. Inlining the update logic further reduces call overhead.
**Action:** Prefer closure-captured references for hot-path state management in decorators and context managers.
## 2025-05-15 - Multi-Language Optimization
**Learning:** Performance bottlenecks are often language-specific yet logically similar. In Rust, avoiding `clone()` via conditional lookups (`get_mut` then `insert`) is critical. In C, bitwise operations for indexing are preferred over modulo. In Python, closure caching and inlining updates significantly reduce "Tax".
**Action:** Apply language-specific hot-path optimizations (avoiding clones, using bitwise masks, closure caching) to minimize tool overhead.
