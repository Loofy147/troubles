## 2025-05-15 - Hot Path Dictionary Lookups
**Learning:** In high-frequency performance profiling, the overhead of `dict.get()` followed by a truthiness check is measurably higher than a `try-except` block when the key is expected to exist most of the time (the common path).
**Action:** Use `try-except` for dictionary lookups in hot paths where keys are repeatedly accessed after initial creation.
