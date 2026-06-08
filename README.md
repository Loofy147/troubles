# ⚡ Bolt

Performance-obsessed utility for compact and adaptive profiling.

## Usage

### As a decorator/wrapper
```python
from bolt import bolt
result = bolt(my_function, *args, **kwargs)
```

### From CLI
```bash
python3 bolt.py sleep 1
```
