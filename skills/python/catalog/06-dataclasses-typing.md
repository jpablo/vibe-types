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
| **Basic annotations** [-> catalog/01](01-basic-annotations-none.md) | Field annotations drive the generated `__init__` signature and attribute types. |
| **Final / ClassVar** [-> catalog/12](12-final-classvar.md) | `ClassVar[T]` fields are excluded from `__init__`. `Final` fields cannot be reassigned even in non-frozen classes. |
| **Annotated metadata** [-> catalog/15](15-annotated-metadata.md) | `Annotated[int, Gt(0)]` carries validator metadata; Pydantic and beartype use this at runtime while checkers see the base type. |
| **Generics** [-> catalog/07](07-generics-typevar.md) | Dataclasses can be generic: `@dataclass class Box(Generic[T]): value: T`. |
| **Protocol** [-> catalog/09](09-protocol-structural-subtyping.md) | A dataclass can satisfy a Protocol if it has the required attributes/methods — no inheritance needed. |

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

- [-> UC-02](../usecases/02-domain-modeling.md) — Dataclasses model domain entities with enforced field types.
- [-> UC-06](../usecases/06-immutability-finality.md) — Frozen dataclasses guarantee immutability of value objects.
- [-> UC-09](../usecases/09-configuration-builder.md) — `@dataclass_transform` enables typed data modeling across ORM and validation libraries.

## Source anchors

- [PEP 557 — Data Classes](https://peps.python.org/pep-0557/)
- [PEP 681 — Data Class Transforms](https://peps.python.org/pep-0681/)
- [`dataclasses` module docs](https://docs.python.org/3/library/dataclasses.html)
- [typing spec: `dataclass_transform`](https://typing.readthedocs.io/en/latest/spec/dataclasses.html)
- [mypy docs: Dataclasses](https://mypy.readthedocs.io/en/stable/additional_features.html#dataclasses)
