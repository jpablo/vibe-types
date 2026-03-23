# Conversions (via Dunder Methods)

## The constraint

Type conversions are explicit in Python. There is no implicit coercion between types. Conversion is performed through dunder methods (`__int__`, `__str__`, `__float__`, `__bool__`) and built-in functions (`int()`, `str()`, `float()`). The type checker verifies that conversion methods exist and return the correct type.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Conversions / coercions | Dunder methods define explicit conversion paths | [-> catalog/18](../catalog/T18-conversions-coercions.md) |
| Protocol | Structural contracts for types that support specific conversions | [-> catalog/07](../catalog/T07-structural-typing.md) |
| Derivation / dataclass | Auto-generated `__repr__` and `__str__` from fields | [-> catalog/06](../catalog/T06-derivation.md) |

## Patterns

### A — __int__ and __float__ for numeric conversion

Define explicit numeric conversions via dunder methods.

```python
from dataclasses import dataclass

@dataclass
class Celsius:
    degrees: float

    def __float__(self) -> float:
        return self.degrees

    def __int__(self) -> int:
        return int(self.degrees)

temp = Celsius(36.6)
float(temp)   # 36.6 — calls __float__
int(temp)     # 36   — calls __int__

# No implicit coercion:
# temp + 1.0  # error: unsupported operand type(s) for +
float(temp) + 1.0  # OK — explicit conversion first
```

### B — __str__ and __repr__ for text conversion

`__str__` defines user-facing string conversion; `__repr__` defines developer-facing representation.

```python
from dataclasses import dataclass

@dataclass
class UserId:
    value: int

    def __str__(self) -> str:
        return f"user-{self.value}"

    def __repr__(self) -> str:
        return f"UserId({self.value})"

uid = UserId(42)
str(uid)     # "user-42"
repr(uid)    # "UserId(42)"
f"{uid}"     # "user-42" — f-strings call __str__
```

### C — __bool__ for truthiness

Control how a type behaves in boolean contexts.

```python
from dataclasses import dataclass

@dataclass
class NonEmptyList[T]:
    items: list[T]

    def __bool__(self) -> bool:
        return len(self.items) > 0

tasks = NonEmptyList([1, 2, 3])
if tasks:           # OK — calls __bool__
    print("has tasks")

empty = NonEmptyList([])
if not empty:       # OK — __bool__ returns False
    print("no tasks")
```

### D — Protocol for convertible types

Define a structural contract for types that support a specific conversion.

```python
from typing import Protocol

class SupportsFloat(Protocol):
    def __float__(self) -> float: ...

def to_fahrenheit(value: SupportsFloat) -> float:
    return float(value) * 9 / 5 + 32

to_fahrenheit(Celsius(100.0))   # OK — Celsius has __float__
to_fahrenheit(36.6)             # OK — float has __float__
# to_fahrenheit("hot")          # error: str has no __float__
```

### Untyped Python comparison

Without types, conversion errors surface as runtime exceptions.

```python
# No types
class Celsius:
    def __init__(self, degrees):
        self.degrees = degrees

temp = Celsius(36.6)
float(temp)    # TypeError: float() argument must be a string or a real number, not 'Celsius'
temp + 1.0     # TypeError: unsupported operand type(s) for +
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| **Dunder methods** | Idiomatic; integrates with built-in functions and f-strings | Must define each conversion separately; no bulk derivation |
| **Protocol (SupportsFloat, etc.)** | Structural: accepts any type with the right method | Only checks method existence statically, not conversion correctness |
| **Explicit function calls** | Clear intent at the call site; no hidden behavior | Verbose compared to implicit coercion in other languages |

## When to use which feature

- **Implement `__str__`** on every domain type for user-facing output — log messages, display, f-strings.
- **Implement `__int__` / `__float__`** when a type has a natural numeric interpretation — temperatures, distances, percentages.
- **Implement `__bool__`** when a type has a natural emptiness or truthiness concept — collections, optional wrappers, result types.
- **Use `SupportsFloat` / `SupportsInt` protocols** in generic functions that need to convert their arguments.

## Source anchors

- [Python data model — Emulating numeric types](https://docs.python.org/3/reference/datamodel.html#emulating-numeric-types)
- [Python data model — __str__ and __repr__](https://docs.python.org/3/reference/datamodel.html#object.__str__)
- [Python data model — __bool__](https://docs.python.org/3/reference/datamodel.html#object.__bool__)
- [typing module — SupportsFloat, SupportsInt](https://docs.python.org/3/library/typing.html#typing.SupportsFloat)
