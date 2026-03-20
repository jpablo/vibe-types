# Type Narrowing and Exhaustiveness

## The constraint

After a type check, the type is narrowed so only valid operations are available. All cases of a Union or enum must be handled; missing a branch is a type error. The checker guarantees that no case falls through unhandled.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Basic annotations / Optional | `X | None` forces explicit None handling before use | [-> catalog/01](../catalog/01-basic-annotations-none.md) |
| Union | Multi-type values that must be narrowed before use | [-> catalog/02](../catalog/02-union-literal-types.md) |
| Enums | Closed sets of named values enabling exhaustive matching | [-> catalog/05](../catalog/05-enums-typing.md) |
| TypeGuard / TypeIs | User-defined narrowing functions for custom type predicates | [-> catalog/13](../catalog/13-typeguard-typeis-narrowing.md) |
| Never / assert_never | Bottom type that proves exhaustiveness — unreachable code is a type error if reachable | [-> catalog/14](../catalog/14-never-noreturn.md) |

## Patterns

### A — isinstance narrowing on Union

The checker narrows the type inside each branch of an `isinstance` check.

```python
def area(shape: "Circle | Rectangle") -> float:
    if isinstance(shape, Circle):
        return 3.14159 * shape.radius ** 2    # OK — shape is Circle here
    elif isinstance(shape, Rectangle):
        return shape.width * shape.height      # OK — shape is Rectangle here
    # If a new variant is added to the Union, the checker can warn
    # about the missing branch (especially with assert_never below)

from dataclasses import dataclass

@dataclass
class Circle:
    radius: float

@dataclass
class Rectangle:
    width: float
    height: float
```

### B — None checking on Optional

Narrowing `X | None` to `X` via an explicit None check.

```python
def first_word(text: str | None) -> str:
    if text is None:
        return ""                   # OK — None case handled
    return text.split()[0]          # OK — narrowed to str

def unsafe(text: str | None) -> str:
    return text.split()[0]          # error: "None" has no attribute "split"
```

### C — match/case with assert_never for exhaustiveness

Use `assert_never` in the default branch so adding a new variant forces a type error.

```python
from enum import Enum
from typing import Never, assert_never

class Direction(Enum):
    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "W"

def move(d: Direction) -> tuple[int, int]:
    match d:
        case Direction.NORTH:
            return (0, 1)          # OK
        case Direction.SOUTH:
            return (0, -1)         # OK
        case Direction.EAST:
            return (1, 0)          # OK
        case Direction.WEST:
            return (-1, 0)         # OK
        case _ as unreachable:
            assert_never(unreachable)  # OK — all cases covered, type is Never

# If we add Direction.UP but forget a branch:
#   case _ as unreachable:
#       assert_never(unreachable)
#       # error: Argument of type "Direction" cannot be assigned to "Never"
```

### D — Custom TypeGuard functions

Write a predicate that narrows a type for the checker, useful when `isinstance` is not enough.

```python
from typing import TypeGuard

def is_str_list(val: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(item, str) for item in val)

def process(data: list[object]) -> str:
    if is_str_list(data):
        return ", ".join(data)     # OK — narrowed to list[str]
    return "mixed data"
```

### Untyped Python comparison

Without narrowing and exhaustiveness, missing cases surface only at runtime.

```python
# No types — new enum member silently falls through
def move(d):
    if d == "N":
        return (0, 1)
    elif d == "S":
        return (0, -1)
    # forgot "E" and "W" — returns None silently
    # caller gets TypeError when unpacking None
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **isinstance narrowing** | Built-in; works with any class hierarchy | Verbose with many branches; does not work for `Literal` or `NewType` |
| **None checks** | Simple, universally understood | Only handles the `None` case; does not scale to multi-variant unions |
| **match + assert_never** | Compiler-enforced exhaustiveness; adding a variant is a guaranteed error | Requires Python 3.10+; mypy support for match exhaustiveness is still maturing |
| **TypeGuard** | Custom narrowing logic for complex predicates | One-directional: the negative branch is not narrowed; `TypeIs` (3.13+) narrows both directions |

## When to use which feature

- **isinstance** for narrowing Union types composed of distinct classes — the most common and readable approach.
- **`is None` / `is not None`** for any `Optional` / `X | None` parameter — always prefer explicit checks over truthiness.
- **match + assert_never** when you have an enum or union and need a guarantee that every variant is handled; especially valuable when the type evolves over time.
- **TypeGuard / TypeIs** when the narrowing condition is not a simple `isinstance` check — e.g., validating the contents of a container, or checking a string format.

## Source anchors

- [PEP 647 — User-Defined Type Guards](https://peps.python.org/pep-0647/)
- [PEP 742 — Narrowing types with TypeIs](https://peps.python.org/pep-0742/)
- [PEP 655 — Required and NotRequired for TypedDict](https://peps.python.org/pep-0655/)
- [typing.assert_never documentation](https://docs.python.org/3/library/typing.html#typing.assert_never)
- [mypy — Type narrowing](https://mypy.readthedocs.io/en/stable/type_narrowing.html)
- [PEP 634 — Structural Pattern Matching](https://peps.python.org/pep-0634/)
