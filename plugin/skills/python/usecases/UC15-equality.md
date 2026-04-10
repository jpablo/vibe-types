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

## When to Use

- **Value objects with full-field equality**: Use `dataclass(eq=True)` when all fields determine equality — coordinates, configuration records, DTOs
- **Semantic equality**: Use custom `__eq__` when comparison logic differs from field-by-field equality — case-insensitive strings, approximate floats, semantic versioning
- **Hashable value types**: Use `frozen=True` when instances must be hashable (dict keys, set members) and immutable
- **Partial field comparison**: Use `field(compare=False)` to exclude specific fields from the generated `__eq__` — timestamps, caches, internal counters
- **Structural typing**: Use `Protocol` when defining a contract for comparable types across different implementations

## When Not to Use

- **Reference identity checks**: Don't use `==` when you need to test if two variables point to the same object — use `is` instead
- **Mutable objects in collections**: Don't add mutable dataclasses to `set` or use as `dict` keys without `frozen=True` — unhashable runtime error
- **Performance-critical inner loops**: Don't define complex `__eq__` in hot paths — inline comparisons or use primitive types
- **Deep structural equality on arbitrary objects**: Don't implement recursive deep equality — it's slow, error-prone on circular structures, and loses specificity

## Antipatterns When Using This Technique

### Antipattern 1 — Forgetting `__hash__` consistency with `__eq__`

```python
from dataclasses import dataclass, field

@dataclass
class User:
    id: int
    name: str
    session_id: str = field(compare=False)

# ❌ User is now unhashable because __eq__ is defined but __hash__ is not
users = {User(1, "Alice", "sess1")}  # TypeError: unhashable type: 'User'

# ✅ Use frozen=True or define __hash__ explicitly
@dataclass(frozen=True)
class User:
    id: int
    name: str
```

### Antipattern 2 — Returning `False` instead of `NotImplemented`

```python
class Point:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return False  # ❌ Breaks reverse comparison
        return self.x == other.x and self.y == other.y

class Vector(Point):
    pass

p = Point(1, 2)
v = Vector(1, 2)

p == v  # False (Point.__eq__ says no)
v == p  # True (object.__eq__ falls back to identity, but may behave unexpectedly)

# ✅ Return NotImplemented to allow reverse comparison
def __eq__(self, other: object) -> bool:
    if not isinstance(other, Point):
        return NotImplemented  # Lets Python try other.__eq__
    return self.x == other.x and self.y == other.y
```

### Antipattern 3 — Comparing all fields when some should be excluded

```python
from dataclasses import dataclass

@dataclass
class CacheEntry:
    key: str
    value: str
    access_count: int

entry1 = CacheEntry("k", "v", 100)
entry2 = CacheEntry("k", "v", 200)

entry1 == entry2  # ❌ False — access_count differs but logically same entry

# ✅ Exclude non-semantic fields
from dataclasses import field

@dataclass
class CacheEntry:
    key: str
    value: str
    access_count: int = field(compare=False)

entry1 == entry2  # True — access_count ignored
```

### Antipattern 4 — Identity comparison for value types

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

p1 = Point(1.0, 2.0)
p2 = Point(1.0, 2.0)

p1 is p2  # ❌ False — identity comparison for value types
p1 == p2  # ✅ True — value comparison

# Use `is` only for None checks or singleton identity
if user is None:
    ...
```

### Antipattern 5 — Hashable dataclass with mutable fields

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Container:
    items: list  # ❌ List is mutable even though dataclass is frozen

c = Container([1, 2])
c.items.append(3)  # Works! The list content changed

# ✅ Use immutable types or make defensive copies
@dataclass(frozen=True)
class Container:
    items: tuple

# Or with explicit __post_init__ conversion
@dataclass(frozen=True)
class Container:
    items: list

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))
```

## Antipatterns Solved by This Technique

### Problem A — Accidental identity comparison for value types

```python
# ❌ Plain class — equality is by identity
class Point:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

p1 = Point(1.0, 2.0)
p2 = Point(1.0, 2.0)

p1 == p2  # False — silently wrong for value types

# ✅ dataclass generates proper __eq__
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

p1 = Point(1.0, 2.0)
p2 = Point(1.0, 2.0)

p1 == p2  # True — field-by-field comparison
```

### Problem B — Cross-type comparison with no compile-time feedback

```python
# ❌ Plain classes — no type guidance
class UserId:
    def __init__(self, value: str) -> None:
        self.value = value

class OrderId:
    def __init__(self, value: str) -> None:
        self.value = value

user_id = UserId("u123")
order_id = OrderId("o456")

user_id == order_id  # ❌ Returns False — no error, just wrong

# ✅ With types, mypy flags the incompatible comparison
from dataclasses import dataclass

@dataclass
class UserId:
    value: str

@dataclass
class OrderId:
    value: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OrderId):
            return NotImplemented
        return self.value == other.value

user_id = UserId("u123")
order_id = OrderId("o456")

user_id == order_id  # mypy: Unsupported operand types for ==
```

### Problem C — Inconsistent equality semantics across codebase

```python
# ❌ Scattered ad-hoc equality implementations
class User:
    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name

def users_equal(a: User, b: User) -> bool:
    return a.id == b.id  # By ID only

def users_deep_equal(a: User, b: User) -> bool:
    return a.id == b.id and a.name == b.name  # By all fields

# ✅ dataclass enforces field-by-field equality consistently
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str

a = User(1, "Alice")
b = User(1, "Bob")

a == b  # False — consistent semantics, no confusion
```

### Problem D — Using mutable objects as dict keys or set members

```python
# ❌ Plain class — no __hash__, cannot be used as key
class Point:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

points = {Point(1, 2): "first"}  # TypeError: unhashable type: 'Point'

# ✅ Frozen dataclass provides both __eq__ and __hash__
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: float
    y: float

points = {Point(1, 2): "first", Point(3, 4): "second"}
points[Point(1, 2)]  # "first" — works correctly
```

### Problem E — Field inclusion confusion for partial equality

```python
# ❌ Need to exclude fields but have no clean way
class Event:
    def __init__(self, type: str, timestamp: float) -> None:
        self.type = type
        self.timestamp = timestamp

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Event):
            return NotImplemented
        # Timestamp should NOT affect equality but there's no marker
        return self.type == other.type and self.timestamp == other.timestamp

event1 = Event("click", 1000.0)
event2 = Event("click", 2000.0)

event1 == event2  # False — but semantically they're the same event type

# ✅ field(compare=False) makes exclusion explicit
from dataclasses import dataclass, field

@dataclass
class Event:
    type: str
    timestamp: float = field(compare=False)

event1 = Event("click", 1000.0)
event2 = Event("click", 2000.0)

event1 == event2  # True — timestamp correctly excluded
```

## Source anchors

- [PEP 557 — Data Classes](https://peps.python.org/pep-0557/)
- [Python data model — `__eq__`](https://docs.python.org/3/reference/datamodel.html#object.__eq__)
- [mypy — Equality and comparison checks](https://mypy.readthedocs.io/en/stable/error_code_list.html#check-that-comparison-is-not-overlapping-comparison-overlap)
- [dataclasses — field options](https://docs.python.org/3/library/dataclasses.html#dataclasses.field)
