# Immutability and Finality

## The constraint

Values, attributes, and hierarchies cannot be modified after declaration. The type checker rejects reassignment to `Final` variables, mutation of frozen dataclass fields, overriding of `Final` methods, and subclassing of `@final` classes.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Dataclasses (frozen) | Immutable record types where field assignment is a type error | [-> catalog/06](../catalog/T06-derivation.md) |
| Final / ClassVar | Mark variables, methods, or classes as non-overridable / non-reassignable | [-> catalog/12](../catalog/T32-immutability-markers.md) |

## Patterns

### A — Frozen dataclass

Declare a dataclass with `frozen=True` so that field reassignment is flagged by the checker.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: float
    y: float

p = Point(1.0, 2.0)
print(p.x)              # OK
p.x = 3.0               # error: Property "x" defined in "Point" is read-only
```

Frozen dataclasses also get a `__hash__` implementation, making them usable as dict keys and set members.

```python
points = {Point(0, 0): "origin", Point(1, 1): "diagonal"}  # OK — hashable
```

### B — Final variables

Prevent reassignment of module-level constants and instance attributes.

```python
from typing import Final

MAX_RETRIES: Final = 3
MAX_RETRIES = 5          # error: Cannot assign to final name "MAX_RETRIES"

API_URL: Final[str] = "https://api.example.com"
API_URL = "http://localhost"  # error: Cannot assign to final name "API_URL"

class Config:
    timeout: Final[int]

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout    # OK — first assignment

    def update(self) -> None:
        self.timeout = 99         # error: Cannot assign to final attribute "timeout"
```

### C — Final methods preventing override

Mark a method as `Final` so subclasses cannot override it.

```python
from typing import final

class Base:
    @final
    def validate(self) -> bool:
        # Critical validation logic that must not be changed
        return self._check()

    def _check(self) -> bool:
        return True

class Derived(Base):
    def validate(self) -> bool:   # error: Cannot override final method "validate"
        return True               #        defined in "Base"

    def _check(self) -> bool:     # OK — _check is not final
        return False
```

### D — Final class preventing subclassing

Mark a class as `@final` so no subclass can be created.

```python
from typing import final

@final
class Singleton:
    _instance: "Singleton | None" = None

    def __new__(cls) -> "Singleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

class MySingleton(Singleton):     # error: Cannot inherit from final class "Singleton"
    pass
```

### Untyped Python comparison

Without `Final` and `frozen`, constants and records can be silently mutated.

```python
# No type annotations
MAX_RETRIES = 3

# Somewhere deep in the codebase...
MAX_RETRIES = -1    # silently breaks retry logic — no checker warning

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1.0, 2.0)
p.x = "not a number"   # silently corrupts the point — discovered later as TypeError
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **Frozen dataclass** | True immutability for records; enables hashing; checker and runtime both reject mutation | Cannot partially freeze; all fields are frozen or none; `__post_init__` workarounds needed for derived fields |
| **Final variable** | Prevents reassignment of constants and config values | Only checked statically; runtime can still reassign; no deep freeze of mutable contents (e.g., `Final[list[int]]` prevents rebinding but not `.append()`) |
| **Final method** | Protects critical logic from being overridden in subclasses | Cannot be used with `@abstractmethod`; limits extensibility |
| **Final class** | Prevents entire inheritance trees; simplifies reasoning about behavior | May be too restrictive for library code where users expect to subclass |

## When to use which feature

- **Frozen dataclass** for value objects and records that should never change after creation — coordinates, configuration snapshots, event payloads.
- **Final variables** for module-level constants and configuration values that must not be reassigned — API URLs, retry limits, feature flags.
- **Final methods** for critical methods where correctness depends on the exact implementation — validation logic, security checks, serialization protocols.
- **Final classes** sparingly, for types whose behavior must be exactly as defined — singletons, security-sensitive classes, or types where subclassing would violate invariants.

## Source anchors

- [PEP 591 — Adding a final qualifier to typing](https://peps.python.org/pep-0591/)
- [PEP 557 — Data Classes](https://peps.python.org/pep-0557/)
- [mypy — Final names, methods, and classes](https://mypy.readthedocs.io/en/stable/final_attrs.html)
- [Python dataclasses documentation](https://docs.python.org/3/library/dataclasses.html)
- [typing module — Final](https://docs.python.org/3/library/typing.html#typing.Final)
