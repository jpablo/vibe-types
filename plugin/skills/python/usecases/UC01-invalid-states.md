# Preventing Invalid States

## The constraint

Only valid domain states are representable in the type system; invalid combinations are flagged as type errors by the checker. If a value passes type checking, it inhabits a legal state.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Basic annotations | Declare parameter and return types so mismatches are caught | [-> catalog/01](../catalog/T13-null-safety.md) |
| Union / Literal | Restrict values to a closed set of alternatives | [-> catalog/02](../catalog/T02-union-intersection.md) |
| NewType | Create distinct types over the same underlying representation | [-> catalog/04](../catalog/T03-newtypes-opaque.md) |
| Enums | Define closed, named state sets with exhaustive matching | [-> catalog/05](../catalog/T01-algebraic-data-types.md) |

## Patterns

### A — Enums for closed state sets

Close off the state space with an `Enum`. The checker rejects values outside the enum.

```python
from enum import Enum

class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

def apply_color(c: Color) -> str:
    return f"Applying {c.value}"

apply_color(Color.RED)       # OK
apply_color("red")           # error: Argument 1 has incompatible type "str"
```

### B — Literal types for restricted values

Constrain a parameter to specific literal values without defining an enum.

```python
from typing import Literal

def set_direction(d: Literal["north", "south", "east", "west"]) -> None: ...

set_direction("north")       # OK
set_direction("up")          # error: Argument 1 has incompatible type "str"
```

### C — NewType for domain primitives

Prevent accidental interchange of values that share the same underlying type.

```python
from typing import NewType

UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)

def get_order(user: UserId, order: OrderId) -> str: ...

uid = UserId(42)
oid = OrderId(99)

get_order(uid, oid)          # OK
get_order(oid, uid)          # error: incompatible type "OrderId"; expected "UserId"
```

### D — Union with dataclasses for discriminated unions

Model states that carry different data per variant.

```python
from dataclasses import dataclass

@dataclass
class Pending:
    created_at: float

@dataclass
class Shipped:
    tracking_id: str

@dataclass
class Delivered:
    signature: str

OrderStatus = Pending | Shipped | Delivered

def describe(s: OrderStatus) -> str:
    match s:
        case Pending(created_at=ts):
            return f"Pending since {ts}"
        case Shipped(tracking_id=tid):
            return f"Shipped: {tid}"
        case Delivered(signature=sig):
            return f"Delivered, signed by {sig}"
```

### Untyped Python comparison

Without types, invalid states surface as runtime errors that may reach production.

```python
# No type annotations — checker sees nothing wrong
def get_order(user, order):
    return f"Order {order} for user {user}"

get_order(99, 42)   # silently swapped arguments — bug undetected
get_order("admin")  # TypeError at runtime: missing 1 required positional argument
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **Enums** | Named members, iteration, exhaustive matching | Verbose for simple two-value cases |
| **Literal** | Lightweight; no extra class needed | No runtime identity; string typos in non-checked code still pass |
| **NewType** | Zero runtime cost; prevents primitive mix-ups | No runtime enforcement; no methods on the wrapper |
| **Union + dataclass** | Each variant carries its own data | Requires `match`/`isinstance` to discriminate; no built-in exhaustiveness in mypy without `assert_never` |

## When to use which feature

- **Start with `Enum`** when the state space is small, fixed, and benefits from named members (statuses, roles, categories).
- **Use `Literal`** for ad-hoc value restrictions on function parameters (directions, modes, format strings).
- **Use `NewType`** when two values share a primitive type but must not be interchanged (IDs, currency amounts, indices).
- **Use Union + dataclass** when each state carries different associated data and you need pattern matching.

## Source anchors

- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
- [PEP 586 — Literal Types](https://peps.python.org/pep-0586/)
- [PEP 484 — NewType](https://peps.python.org/pep-0484/#newtype-helper-function)
- [Python `enum` module documentation](https://docs.python.org/3/library/enum.html)
- [mypy — Literal types](https://mypy.readthedocs.io/en/stable/literal_types.html)
