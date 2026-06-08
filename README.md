# ⚡ Bolt

A performance-obsessed, compact, and adaptive profiling utility.

## Features

- **Decorator**: Easy profiling of functions.
- **Context Manager**: Profile specific blocks of code.
- **Direct Call**: Profile any callable on the fly.
- **CLI Shim**: Profile shell commands directly from your terminal.

## Usage

### As a decorator
```python
from bolt import bolt

@bolt
def my_function():
    ...
```

### As a context manager
```python
from bolt import bolt

with bolt("heavy_lifting"):
    # Code to profile
    ...
```

### As a direct call
```python
from bolt import bolt

result = bolt(my_function, *args, **kwargs)
```

### From CLI
```bash
python3 bolt.py sleep 1
```
