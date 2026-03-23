# Equality (via __eq__ and dataclass)

## The constraint

Equality comparison is opt-in through `__eq__`. By default, objects compare by identity (`is`), not by value. The type checker enforces that `==` is only used between compatible types, and `dataclass(eq=True)` generates structural equality automatically.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Derivation / dataclass | Auto-generate `__eq__` based on fields | [-> catalog/06](../catalog/T06-derivation.md) |
| Equality safety | Checker rejects cross-type `==` unless `__eq__` accepts the operand | [-> catalog/20](../catalog/T20-equality-safety.md) |
| Protocol | Define structural contracts for comparable types | [-> catalog/07](../catalog/T07-structural-typing.md) |

## Patterns

### A — dataclass with generated equality

`dataclass(eq=True)` (the default) generates `__eq__` that compares all fields structurally.

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

Point(1.0, 2.0) == Point(1.0, 2.0)   # True — field-by-field comparison
Point(1.0, 2.0) == Point(3.0, 4.0)   # False
```

Without `dataclass`, two instances of a plain class with the same fields would compare as not equal (identity comparison).

### B — Custom __eq__ for domain logic

Override `__eq__` for case-insensitive or tolerance-based comparison.

```python
class CaseInsensitiveStr:
    def __init__(self, value: str) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CaseInsensitiveStr):
            return NotImplemented
        return self.value.lower() == other.value.lower()

    def __hash__(self) -> int:
        return hash(self.value.lower())

CaseInsensitiveStr("Hello") == CaseInsensitiveStr("hello")  # True
```

### C — Frozen dataclass for hashable equality

Frozen dataclasses get both `__eq__` and `__hash__`, making them usable as dict keys and set members.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

palette = {Color(255, 0, 0): "red", Color(0, 0, 255): "blue"}
palette[Color(255, 0, 0)]   # "red"
```

### D — Protocol for comparable types

Define a structural contract for types that support comparison.

```python
from typing import Protocol

class SupportsEq(Protocol):
    def __eq__(self, other: object) -> bool: ...

def are_equal(a: SupportsEq, b: SupportsEq) -> bool:
    return a == b

are_equal(Point(1, 2), Point(1, 2))   # OK
are_equal(42, 42)                       # OK — int has __eq__
```

### Untyped Python comparison

Without types, cross-type comparisons silently return `False` instead of being flagged.

```python
# No type annotations
class User:
    def __init__(self, name):
        self.name = name

User("alice") == User("alice")   # False — identity comparison, not value
User("alice") == "alice"         # False — no error, just wrong
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| **dataclass(eq=True)** | Zero boilerplate; structural equality from fields | Compares all fields — cannot exclude computed or internal fields without `field(compare=False)` |
| **Custom __eq__** | Full control over comparison semantics | Must maintain `__hash__` consistency manually; easy to forget `NotImplemented` return |
| **Frozen dataclass** | Equality + hashability in one declaration | All fields immutable; no partial freezing |
| **Protocol** | Structural requirement for comparability | Only checked statically; no runtime enforcement of comparison semantics |

## When to use which feature

- **Use `dataclass(eq=True)`** (the default) for value types where all fields determine equality — coordinates, configuration records, DTOs.
- **Use custom `__eq__`** when comparison logic differs from field-by-field equality — case-insensitive strings, approximate floats, semantic versioning.
- **Use `frozen=True`** when instances must be hashable (dict keys, set members) and immutable.
- **Use `field(compare=False)`** to exclude specific fields from the generated `__eq__` — timestamps, caches, internal counters.

## Source anchors

- [PEP 557 — Data Classes](https://peps.python.org/pep-0557/)
- [Python data model — `__eq__`](https://docs.python.org/3/reference/datamodel.html#object.__eq__)
- [mypy — Equality and comparison checks](https://mypy.readthedocs.io/en/stable/error_code_list.html#check-that-comparison-is-not-overlapping-comparison-overlap)
- [dataclasses — field options](https://docs.python.org/3/library/dataclasses.html#dataclasses.field)
