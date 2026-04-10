# Dataclasses and Typed Data Modeling

> **Since:** Python 3.7 (PEP 557) | **`dataclass_transform`:** Python 3.12 (PEP 681) | **Backport:** `typing_extensions.dataclass_transform`

## What it is

The `@dataclass` decorator generates boilerplate methods (`__init__`, `__repr__`, `__eq__`, etc.) from annotated class fields, turning a class body into a declarative schema. Because every field carries a type annotation, static type checkers treat the generated `__init__` as a fully typed constructor — verifying that callers supply correct types, that field access uses the declared type, and that immutability constraints (via `frozen=True`) are respected.

Python 3.12 added `@dataclass_transform` (PEP 681), which tells type checkers to apply dataclass-style field analysis to *any* decorator or metaclass — enabling first-class checker support for third-party libraries like attrs, Pydantic, and SQLModel without special plugins.

## What constraint it enforces

**Field types declared in a dataclass are enforced at construction and attribute access by the type checker, and `frozen=True` prevents reassignment after construction.**

Specifically:

- The generated `__init__` signature mirrors field annotations: passing the wrong type is flagged.
- Accessing a field returns the annotated type — no `Any` leakage.
- `frozen=True` makes all field assignments after `__init__` a type error.
- `ClassVar` fields are excluded from `__init__`; `InitVar` fields appear in `__init__` but are not stored as attributes.
- `@dataclass_transform` extends all of the above to third-party decorators.

## Minimal snippet

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: float
    y: float

p = Point(1.0, 2.0)       # OK
p = Point("a", 2.0)       # error: Argument 1 has incompatible type "str"; expected "float"
p.x = 3.0                 # error: Property "x" is read-only (frozen dataclass)
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Basic annotations** [-> catalog/01](T13-null-safety.md) | Field annotations drive the generated `__init__` signature and attribute types. |
| **Final / ClassVar** [-> catalog/12](T32-immutability-markers.md) | `ClassVar[T]` fields are excluded from `__init__`. `Final` fields cannot be reassigned even in non-frozen classes. |
| **Annotated metadata** [-> catalog/15](T26-refinement-types.md) | `Annotated[int, Gt(0)]` carries validator metadata; Pydantic and beartype use this at runtime while checkers see the base type. |
| **Generics** [-> catalog/07](T04-generics-bounds.md) | Dataclasses can be generic: `@dataclass class Box(Generic[T]): value: T`. |
| **Protocol** [-> catalog/09](T07-structural-typing.md) | A dataclass can satisfy a Protocol if it has the required attributes/methods — no inheritance needed. |

## Gotchas and limitations

1. **Mutable default trap.** A bare mutable default like `tags: list[str] = []` is rejected by the dataclass machinery at runtime (`ValueError`). Use `field(default_factory=list)` instead. Type checkers may or may not catch this before runtime.

   ```python
   from dataclasses import dataclass, field

   @dataclass
   class Bad:
       tags: list[str] = []                      # runtime error: mutable default

   @dataclass
   class Good:
       tags: list[str] = field(default_factory=list)  # OK
   ```

2. **`frozen` does not prevent deep mutation.** A frozen dataclass prevents reassigning fields, but if a field holds a mutable container, the container's contents can still change.

   ```python
   @dataclass(frozen=True)
   class Config:
       items: list[str]

   c = Config(items=["a"])
   c.items.append("b")     # OK at type-check time — list itself is mutable
   c.items = ["x"]          # error: read-only property
   ```

3. **Inheritance order matters.** A non-frozen dataclass cannot inherit from a frozen one (or vice versa) — this raises `TypeError` at runtime. When mixing frozen and non-frozen, keep the hierarchy consistent.

4. **`__post_init__` and `InitVar` typing.** `InitVar[T]` fields appear in `__init__` but are not instance attributes. They are passed to `__post_init__`, which must declare matching parameters. Forgetting to add the parameter in `__post_init__` silently drops the value.

5. **`slots=True` (3.10+) breaks multiple inheritance.** When `slots=True` is used, each class in an inheritance chain generates its own `__slots__`, and conflicts can cause `TypeError` if two parent classes define overlapping slot names.

6. **Field ordering with defaults.** Fields without defaults must come before fields with defaults. In inheritance hierarchies this can force awkward ordering — use `KW_ONLY` (3.10+) to make all subsequent fields keyword-only and sidestep the ordering constraint.

## Beginner mental model

Think of `@dataclass` as a form template: you list the field names and their types, and Python generates the constructor that enforces those types at check time. Adding `frozen=True` is like laminating the form after it is filled in — no one can change what was written. `@dataclass_transform` is like telling the type checker "this other decorator also produces laminated forms" — so attrs, Pydantic, and similar libraries get the same checking guarantees.

## Example A — Domain entity with typed fields and frozen immutability

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    amount_cents: int
    line_items: tuple[str, ...]               # immutable container for deep safety
    created_at: datetime = field(default_factory=datetime.utcnow)

inv = Invoice(
    invoice_id="INV-001",
    amount_cents=5000,
    line_items=("Widget A", "Widget B"),
)

total: int = inv.amount_cents                  # OK — checker knows this is int
inv.amount_cents = 9999                        # error: read-only property

# Using KW_ONLY (Python 3.10+)
from dataclasses import KW_ONLY

@dataclass
class Order:
    order_id: str
    _: KW_ONLY
    priority: int = 0
    notes: str = ""

Order("ORD-1", priority=1)                     # OK
Order("ORD-1", 1)                              # error: too many positional arguments
```

## Example B — Third-party decorator with @dataclass_transform

```python
from typing import dataclass_transform, TypeVar

T = TypeVar("T")

# Library code: tell checkers this decorator produces dataclass-like classes
@dataclass_transform()
def my_model(cls: type[T]) -> type[T]:
    # In reality: generate __init__, __eq__, etc. (like attrs does)
    return cls

# User code: checker treats MyUser fields as typed __init__ params
@my_model
class MyUser:
    name: str
    age: int

u = MyUser(name="Alice", age=30)               # OK
u = MyUser(name="Alice", age="thirty")          # error: expected int, got str
u.name                                          # OK — str
u.unknown                                       # error: has no attribute "unknown"

# Real-world: Pydantic v2 uses @dataclass_transform internally
# from pydantic import BaseModel
# class User(BaseModel):
#     name: str
#     age: int
# Type checkers understand User(name=..., age=...) without a mypy plugin.
```

## Common type-checker errors and how to read them

### mypy: `Argument N has incompatible type "X"; expected "Y"`

Wrong type passed to the generated `__init__`.

```
error: Argument 1 to "Point" has incompatible type "str"; expected "float"
```

**Fix:** Pass the correct type, or widen the field annotation if the field truly accepts multiple types.

### mypy: `Property "x" defined in "Point" is read-only`

Assigning to a field on a `frozen=True` dataclass.

```
error: Property "x" defined in "Point" is read-only
```

**Fix:** Frozen dataclasses are immutable by design. Create a new instance with `dataclasses.replace(point, x=new_value)`.

### pyright: `"Point" has no attribute "z"`

Accessing a field that was not declared.

```
error: Cannot access attribute "z" for class "Point"
  Attribute "z" is unknown
```

**Fix:** Add the field to the class definition, or check for a typo.

### mypy: `Attributes without a default cannot follow attributes with one`

Field ordering violation in dataclass inheritance.

```
error: Attributes without a default cannot follow attributes with one
```

**Fix:** Reorder fields so all non-default fields come first, or use `KW_ONLY` to make defaulted fields keyword-only.

## Use-case cross-references

- [-> UC-02](../usecases/UC02-domain-modeling.md) — Dataclasses model domain entities with enforced field types.
- [-> UC-06](../usecases/UC06-immutability.md) — Frozen dataclasses guarantee immutability of value objects.
- [-> UC-09](../usecases/UC09-builder-config.md) — `@dataclass_transform` enables typed data modeling across ORM and validation libraries.

## Recommended libraries

| Library | Description |
|---|---|
| [pydantic](https://pypi.org/project/pydantic/) | `BaseModel` with runtime validation, JSON serialization, and `dataclass_transform` support for full checker integration |
| [attrs](https://pypi.org/project/attrs/) | Alternative to dataclasses with validators, converters, and `dataclass_transform` — more features, same checker support |
| [cattrs](https://pypi.org/project/cattrs/) | Structure (dict-to-class) and unstructure (class-to-dict) for attrs and dataclass objects with type-safe converters |

## When to use it

- **Domain entities with enforced invariants** — User, Invoice, Order: the constructor signature enforces required fields and types at check time.
- **Value objects with immutability requirements** — `frozen=True` models that must not change after construction.
- **Config objects with defaults** — `field(default_factory=...)` or `field(default=...)` provides typed defaults.
- **Single source of truth for field definitions** — Adding a field to the dataclass immediately updates the constructor and attribute types everywhere.
- **Structural protocol compliance** — Dataclasses automatically satisfy Protocols with matching attributes, no explicit `implements`.
- **Third-party decorators that look like dataclasses** — Using `@dataclass_transform` to give attrs, custom decorators, or validation libraries the same checker support.

## When not to use it

- **Transient, internal-only structures** — Plain dictionaries or namedtuples are lighter for short-lived values that don't cross boundaries.
- **Mutable state containers that evolve** — Event-driven systems or entities that change shape over time are better modeled with explicit methods and state machines.
- **Performance-critical hot paths** — Dataclass generation adds some overhead; in tight loops, plain classes or dictionaries may outperform.
- **Complex inheritance hierarchies** — Mixing frozen/non-frozen, or deep MRO chains with `slots=True`, can cause runtime `TypeError`.
- **When runtime validation is insufficient** — Dataclasses provide type safety but no runtime validation beyond the generated `__init__`. Use Pydantic or Beartype for constraint checking (e.g., positive integers, email format).

## Antipatterns when using dataclasses

### ❌ Mutable default without `field(default_factory=...)`

```python
from dataclasses import dataclass

@dataclass
class Bad:
    tags: list[str] = []  # runtime ValueError: mutable default

@dataclass
class Good:
    from dataclasses import field
    tags: list[str] = field(default_factory=list)
```

### ❌ Frozen class with mutable container fields

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    items: list[str]

c = Config(items=["a"])
c.items.append("b")  # type OK, mutable list contents
```

**Fix:** Use immutable containers: `tuple[str, ...]`, `frozenset[str]`, or frozen `list` via `field(default_factory=lambda: ...)` + copying on change.

### ❌ Reassigning fields in `__post_init__`

```python
from dataclasses import dataclass, InitVar

@dataclass
class Bad:
    x: InitVar[int]
    y: int

    def __post_init__(self, x: int):
        y = x * 2  # creates local variable `y`, does not set attribute

@dataclass
class Good:
    x: InitVar[int]
    y: int

    def __post_init__(self, x: int):
        object.__setattr__(self, "y", x * 2)  # or self.y = ... in non-frozen
```

### ❌ Field ordering errors with defaults

```python
from dataclasses import dataclass

@dataclass
class Bad:
    name: str
    age: int = 0        # OK
    email: str          # error: non-default after default

@dataclass
class Good:
    from dataclasses import KW_ONLY
    name: str
    _: KW_ONLY
    age: int = 0
    email: str = ""
```

### ❌ Ignoring type annotations to suppress errors

```python
from dataclasses import dataclass

@dataclass
class Bad:
    name: str
    age: int

def process(b: Bad) -> None:
    b.name = 123  # error — but suppressed with `# type: ignore`
```

**Fix:** Fix the type, don't suppress. Or use `Any` deliberately where truly needed.

---

## Antipatterns with other techniques where dataclasses result in better code

### ❌ Plain class with manual `__init__` and `__eq__`

```python
# BAD — verbose, error-prone, easy to forget equality semantics
class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __eq__(self, other) -> bool:
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __repr__(self) -> str:
        return f"Point(x={self.x}, y={self.y})"
```

**Fix with dataclass:**

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float
# __init__, __eq__, __repr__ generated automatically
```

### ❌ Dict with string keys and manual validation

```python
# BAD — no type safety, typos not caught until runtime
def process_user(user: dict) -> None:
    name = user["name"]  # KeyError if missing
    age = int(user["age"])  # ValueError if not int
```

**Fix with dataclass:**

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

def process_user(user: User) -> None:
    # Type checker enforces name: str, age: int
    name = user.name
    age = user.age
```

### ❌ Namedtuple with mutable transformation logic

```python
# BAD — namedtuple is immutable but lacks constructor validation
from collections import namedtuple

Point = namedtuple("Point", ["x", "y"])
p = Point("a", "b")  # compiles, fails later when math operations run
distance = p.x ** 2  # error at runtime
```

**Fix with dataclass:**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: float
    y: float

p = Point("a", "b")  # type error: expected float, got str
```

### ❌ Separate config dict and validation function

```python
# BAD — config shape and validation diverge over time
CONFIG_SCHEMA = {
    "port": int,
    "host": str,
}

def validate_config(cfg: dict) -> None:
    if not isinstance(cfg.get("port"), int):
        raise ValueError("port must be int")
    if not isinstance(cfg.get("host"), str):
        raise ValueError("host must be str")
    # forgot to add "timeout" later
```

**Fix with dataclass:**

```python
from dataclasses import dataclass

@dataclass
class Config:
    port: int
    host: str
    timeout: int = 5000  # added field, type checker catches all usages
```

### ❌ Inheritance hierarchy with manual field forwarding

```python
# BAD — tedious to maintain, easy to forget fields
class BaseEntity:
    def __init__(self, id: int, created_at: str):
        self.id = id
        self.created_at = created_at

class Order(BaseEntity):
    def __init__(self, id: int, created_at: str, user_id: int, total: float):
        super().__init__(id, created_at)
        self.user_id = user_id
        self.total = total  # easy to miss reassigning a field
```

**Fix with dataclass inheritance:**

```python
from dataclasses import dataclass

@dataclass
class BaseEntity:
    id: int
    created_at: str

@dataclass
class Order(BaseEntity):
    user_id: int
    total: float
# all fields appear in Order.__init__ automatically
```

## Source anchors

- [PEP 557 — Data Classes](https://peps.python.org/pep-0557/)
- [PEP 681 — Data Class Transforms](https://peps.python.org/pep-0681/)
- [`dataclasses` module docs](https://docs.python.org/3/library/dataclasses.html)
- [typing spec: `dataclass_transform`](https://typing.readthedocs.io/en/latest/spec/dataclasses.html)
- [mypy docs: Dataclasses](https://mypy.readthedocs.io/en/stable/additional_features.html#dataclasses)
