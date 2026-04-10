# Equality Safety (via __eq__ and dataclass)

> **Since:** `__eq__` — Python 1.x; `@dataclass(eq=True)` — Python 3.7 (PEP 557); `Protocol` — Python 3.8 (PEP 544)

## What it is

In Python, equality comparison (`==`) is controlled by the `__eq__` dunder method. For custom classes, the default `__eq__` inherited from `object` performs **identity comparison** (`is`), meaning two distinct instances with identical fields are not equal unless you explicitly implement `__eq__`. The `@dataclass` decorator generates `__eq__` (and optionally `__hash__`) based on the declared fields, providing **structural equality** out of the box.

Unlike Rust (where `==` requires implementing `PartialEq`) or Haskell (where `==` requires the `Eq` typeclass), Python allows `==` between *any* two objects — the type checker does not prevent comparing unrelated types. The comparison simply returns `NotImplemented` or `False` at runtime if the types are incompatible. Some checkers (pyright with strict mode) can flag suspicious comparisons between obviously unrelated types.

## What constraint it enforces

**`@dataclass(eq=True)` generates field-by-field equality, ensuring structural comparison without manual boilerplate. The type checker verifies `__eq__` signatures but does not prevent cross-type comparisons. `__hash__` consistency with `__eq__` is the developer's responsibility.**

## Minimal snippet

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

a = Point(1.0, 2.0)
b = Point(1.0, 2.0)
c = Point(3.0, 4.0)

a == b    # True  — structural equality from generated __eq__
a == c    # False
a is b    # False — different objects

# Without @dataclass:
class RawPoint:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

RawPoint(1.0, 2.0) == RawPoint(1.0, 2.0)    # False — identity comparison!
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dataclasses / derivation** [-> catalog/T06](T06-derivation.md) | `@dataclass(eq=True)` is the default — it generates `__eq__` and `__hash__` (if `frozen=True`). `@dataclass(eq=False)` preserves identity semantics. |
| **Protocol** [-> catalog/T07](T07-structural-typing.md) | Define `class SupportsEq(Protocol): def __eq__(self, other: object) -> bool: ...` to require equality support structurally. All objects satisfy this by default, so a more specific protocol may be needed. |
| **Immutability / Final** [-> catalog/T32](T32-immutability-markers.md) | `@dataclass(frozen=True)` makes instances immutable *and* hashable (generates `__hash__`), enabling use in sets and dict keys. |
| **Enum** [-> catalog/T01](T01-algebraic-data-types.md) | Enum members use identity for equality (`Color.RED == Color.RED`). Comparing an enum member with a non-member string/int is flagged by some checkers as a non-overlapping comparison. |
| **NewType** [-> catalog/T03](T03-newtypes-opaque.md) | NewType values compare as their underlying type at runtime, but the checker can flag comparisons between different NewTypes if they are structurally distinct. |

## Gotchas and limitations

1. **`__eq__` and `__hash__` must be consistent.** If two objects are equal (`a == b`), they must have the same hash. `@dataclass` with mutable fields sets `__hash__ = None` (unhashable) to prevent inconsistency. Use `frozen=True` or `unsafe_hash=True` to get hashability.

   ```python
   @dataclass
   class Mutable:
       x: int

   {Mutable(1)}   # TypeError: unhashable type: 'Mutable'

   @dataclass(frozen=True)
   class Immutable:
       x: int

   {Immutable(1)}  # OK — frozen dataclass is hashable
   ```

2. **Cross-type `==` always succeeds at runtime.** `Point(1, 2) == "hello"` returns `False` (not an error). The type checker does not flag this in standard mode. pyright's `reportUnnecessaryComparison` can catch some cases.

3. **`__eq__` should accept `object`, not a specific type.** The correct signature is `def __eq__(self, other: object) -> bool`. Narrowing to a specific type breaks Liskov substitution and causes checker warnings.

   ```python
   class Good:
       def __eq__(self, other: object) -> bool:
           if not isinstance(other, Good):
               return NotImplemented
           return self.x == other.x

   class Bad:
       def __eq__(self, other: "Bad") -> bool:    # Too narrow!
           return self.x == other.x
   # Checker warning: signature incompatible with "object.__eq__"
   ```

4. **NamedTuple equality compares by position, not by name.** Two different `NamedTuple` types with the same field types compare equal if the values match, since they are tuple subclasses.

   ```python
   from typing import NamedTuple

   class Point(NamedTuple):
       x: int
       y: int

   class Size(NamedTuple):
       width: int
       height: int

   Point(1, 2) == Size(1, 2)    # True! — both are (1, 2) tuples
   ```

5. **`@dataclass(order=True)` generates `__lt__`, `__le__`, etc.** but raises `TypeError` at runtime if you compare instances of different dataclass types (even with the same fields). The type checker does not prevent this.

## Beginner mental model

Think of `==` as asking "are these the same?" By default, Python objects answer "only if we are literally the same object" (identity). `@dataclass` teaches them to answer "if all our fields match" (structural equality). The type checker trusts you when you write `==` — it will not stop you from comparing apples to oranges, but `@dataclass` ensures that comparing two apples checks every bite.

## Example A — Dataclass equality with frozen hashability

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

red = Color(255, 0, 0)
also_red = Color(255, 0, 0)
blue = Color(0, 0, 255)

assert red == also_red           # True — structural equality
assert red != blue               # True
assert red is not also_red       # True — different objects

# Usable as dict keys and in sets because frozen=True generates __hash__
palette: set[Color] = {red, blue, also_red}
assert len(palette) == 2         # red and also_red collapse to one entry

color_names: dict[Color, str] = {
    Color(255, 0, 0): "red",
    Color(0, 0, 255): "blue",
}
assert color_names[also_red] == "red"   # lookup works via __hash__ + __eq__
```

## Example B — Custom __eq__ with type narrowing

```python
from __future__ import annotations

class Money:
    def __init__(self, amount: int, currency: str) -> None:
        self.amount = amount
        self.currency = currency

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __hash__(self) -> int:
        return hash((self.amount, self.currency))

    def __repr__(self) -> str:
        return f"Money({self.amount}, {self.currency!r})"

usd_10 = Money(10, "USD")
usd_10b = Money(10, "USD")
eur_10 = Money(10, "EUR")

assert usd_10 == usd_10b       # True — same amount and currency
assert usd_10 != eur_10        # True — different currency
assert usd_10 != "10 USD"      # True — returns NotImplemented, then False

# Hashable — usable in sets
prices = {usd_10, eur_10, usd_10b}
assert len(prices) == 2
```

## Use-case cross-references

- [-> UC-02](../usecases/UC02-domain-modeling.md) — Domain value objects use structural equality to compare by content, not identity.
- [-> UC-06](../usecases/UC06-immutability.md) — Frozen dataclasses combine immutability with safe hashability for use as dict keys.

## When to use it

- **Domain value objects**: When equality should be based on field values, not identity (e.g., `Money(10, "USD") == Money(10, "USD")`).
- **Cache keys and set membership**: When objects must be hashable and comparison-based (use `frozen=True`).
- **Test assertions**: When verifying that constructed objects have expected field values.
- **Deduplication**: When removing duplicate entries from lists or collections.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
@dataclass(eq=True)
class Product:
    sku: str
    name: str

products = [Product("A", "Apple"), Product("A", "Apple"), Product("B", "Banana")]
unique = list(dict.fromkeys(products))  # Deduplicates via __eq__ + __hash__
```

## When NOT to use it

- **Identity semantics needed**: When two distinct instances should never be equal (e.g., database session objects, user connections).
- **Partial equality**: When only some fields should determine equality (requires custom `__eq__`, not `@dataclass`).
- **Mutable objects as dict keys**: Mutable dataclasses are unhashable by default — do not use as keys in `dict` or members of `set`.
- **Performance-critical hot paths**: Field-by-field equality can be slower than simple identity checks; use `is` when identity is what matters.

```python
# Don't use dataclass equality here:
class Session:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.created_at = time.now()

s1 = Session(1)
s2 = Session(1)
assert s1 != s2  # OK, but dataclass(eq=True) would make them equal!
```

## Antipatterns when using it

1. **Forgetting to handle `NotImplemented`**: Returning `False` instead of `NotImplemented` for incompatible types breaks symmetric equality.

```python
class Bad:
    x: int
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Bad):
            return False  # Wrong! Should return NotImplemented
        return self.x == other.x

class Good:
    x: int
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Good):
            return NotImplemented  # Correct
        return self.x == other.x
```

2. **Implementing `__hash__` without `__eq__`** (or vice versa): Inconsistent hashing breaks `set` and `dict` behavior.

```python
@dataclass
class Broken:
    x: int
    def __hash__(self) -> int:
        return hash(self.x)  # Wrong! @dataclass sets __hash__ = None because it's mutable

@dataclass(frozen=True)
class Working:
    x: int
    # __hash__ auto-generated from fields — consistent with __eq__
```

3. **Comparing incomparable types explicitly**: Writing tests that assume cross-type comparisons work.

```python
# Testing this is an antipattern:
@dataclass
class Point:
    x: float
    y: float

assert Point(1, 2) == [1, 2]  # Don't test this — it's False by accident
```

## Antipatterns with other techniques

1. **Using `is` instead of `==` for value types**: Identity checks fail for distinct instances with same content.

```python
# Antipattern:
@dataclass
class Config:
    debug: bool

cfg1 = Config(debug=True)
cfg2 = Config(debug=True)
if cfg1 is cfg2:  # False! Use == for value comparison
    ...

# Better:
if cfg1 == cfg2:  # True — structural equality
    ...
```

2. **Using raw classes with dict keys**: Without `__hash__`, runtime errors occur.

```python
# Antipattern:
class Point:
    def __init__(self, x: int, y: int):
        self.x, self.y = x, y

points = {Point(1, 2): "origin"}  # TypeError: unhashable type: 'Point'

# Better with @dataclass:
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: int
    y: int

points = {Point(1, 2): "origin"}  # Works
```

3. **Mixing equality types in collections**: Having some objects with structural equality and others with identity equality leads to subtle bugs.

```python
# Antipattern:
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

class RawPoint:
    def __init__(self, x: int, y: int):
        self.x, self.y = x, y

mixed = {Point(1, 2), RawPoint(1, 2)}  # Two entries: Point != RawPoint
# You probably expected one entry, since both have (x=1, y=2)
```

## Use-case cross-references

- [-> UC-02](../usecases/UC02-domain-modeling.md) — Domain value objects use structural equality to compare by content, not identity.
- [-> UC-06](../usecases/UC06-immutability.md) — Frozen dataclasses combine immutability with safe hashability for use as dict keys.

## Source anchors

- [PEP 557 — Data Classes](https://peps.python.org/pep-0557/)
- [Python Data Model — object.__eq__](https://docs.python.org/3/reference/datamodel.html#object.__eq__)
- [dataclasses module — eq and hash](https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass)
- [mypy — Comparison operators](https://mypy.readthedocs.io/en/stable/common_issues.html#comparison)
