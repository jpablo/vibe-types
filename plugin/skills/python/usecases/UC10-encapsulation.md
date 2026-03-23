# Encapsulation in Python

## The constraint

Internal implementation details must be hidden behind a public interface so that
external code cannot depend on or mutate private state. The type checker should
flag violations of encapsulation boundaries at check time.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| `_private` convention | Signal internal members; pyright reports external access | [-> T21](../catalog/T21-encapsulation.md) |
| `__name_mangling` | Avoid attribute collisions in subclass hierarchies | [-> T21](../catalog/T21-encapsulation.md) |
| `__all__` | Control star-import visibility at the module level | [-> T21](../catalog/T21-encapsulation.md) |
| `@property` | Expose controlled read/write access to private state | [-> T21](../catalog/T21-encapsulation.md) |
| `Protocol` | Define the public surface structurally | [-> T07](../catalog/T07-structural-typing.md) |
| `Final` | Prevent reassignment and subclass override | [-> T32](../catalog/T32-immutability-markers.md) |

## Patterns

### A — Single-underscore convention with pyright enforcement

A leading `_` marks a member as internal. pyright's `reportPrivateUsage` flags
external access as an error.

```python
class ConnectionPool:
    def __init__(self, max_size: int) -> None:
        self._connections: list[object] = []
        self._max_size = max_size

    def acquire(self) -> object:
        if self._connections:
            return self._connections.pop()
        return object()  # create new

    def release(self, conn: object) -> None:
        if len(self._connections) < self._max_size:
            self._connections.append(conn)

pool = ConnectionPool(10)
pool.acquire()              # OK — public API
pool._connections           # pyright: error — access to private member
```

### B — `@property` for controlled access

Expose derived or validated values without leaking internal representation.

```python
class Temperature:
    def __init__(self, celsius: float) -> None:
        self._celsius = celsius

    @property
    def celsius(self) -> float:
        return self._celsius

    @property
    def fahrenheit(self) -> float:
        return self._celsius * 9 / 5 + 32

    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < -273.15:
            raise ValueError("Below absolute zero")
        self._celsius = value

t = Temperature(100.0)
t.celsius                  # OK — 100.0
t.fahrenheit               # OK — 212.0 (read-only)
t.fahrenheit = 0           # error: property has no setter
```

### C — Module boundaries with `__all__`

`__all__` controls what `from module import *` exports. Combine with `_`-prefixed
helpers to create a clear public/private boundary at the module level.

```python
# payments.py
__all__ = ["charge", "PaymentResult"]

from dataclasses import dataclass

@dataclass
class PaymentResult:
    success: bool
    transaction_id: str

def charge(amount: int) -> PaymentResult:
    return _process(amount)

def _process(amount: int) -> PaymentResult:
    # internal — not in __all__
    return PaymentResult(success=True, transaction_id="txn-123")

# from payments import *     -> imports charge, PaymentResult
# from payments import _process  -> works but pyright warns
```

### D — Protocol to define the public surface

A `Protocol` declares the public contract. Consumers depend on the protocol,
not the concrete class, making internal details invisible.

```python
from typing import Protocol

class Logger(Protocol):
    def log(self, message: str) -> None: ...
    def flush(self) -> None: ...

class FileLogger:
    def __init__(self, path: str) -> None:
        self._buffer: list[str] = []   # private
        self._path = path              # private

    def log(self, message: str) -> None:
        self._buffer.append(message)

    def flush(self) -> None:
        self._buffer.clear()

def run(logger: Logger) -> None:
    logger.log("started")
    logger.flush()
    # logger._buffer  -> not part of Protocol, invisible to consumer
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **`_` convention** | Simple; idiomatic; pyright enforces | Not enforced at runtime; mypy does not flag by default |
| **`__` mangling** | Prevents subclass attribute collisions | Deterministic — can still be accessed via `_Class__name` |
| **`__all__`** | Controls star-import surface | Only affects `import *`; direct imports still work |
| **`@property`** | Read-only or validated access; Pythonic | Does not prevent deep mutation of mutable fields |
| **Protocol** | Structural public contract; decouples consumers | Extra type; no runtime enforcement without `@runtime_checkable` |

## When to use which feature

- **Start with `_` convention** for class-level encapsulation. pyright catches violations.
- **Use `@property`** when you need read-only access, validation, or computed attributes.
- **Use `__all__`** to define the public API of a module or package `__init__.py`.
- **Use `__` mangling** sparingly, only to avoid name collisions in deep inheritance.
- **Use `Protocol`** when consumers should depend on an interface, not a concrete class.

## Source anchors

- [PEP 8 — Naming Conventions](https://peps.python.org/pep-0008/#naming-conventions)
- [Python Tutorial — Private Variables](https://docs.python.org/3/tutorial/classes.html#private-variables)
- [Built-in Functions — property()](https://docs.python.org/3/library/functions.html#property)
- [pyright — reportPrivateUsage](https://microsoft.github.io/pyright/#/configuration?id=reportprivateusage)
- [PEP 544 — Protocols](https://peps.python.org/pep-0544/)
