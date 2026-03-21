# Enums with Static Typing

## What it is

Python's `enum` module (PEP 435, Python 3.4) provides named, immutable sets of values. When combined with type annotations, enums give the type checker a *closed set* of members — it knows every possible value and can verify exhaustiveness. `IntEnum` and `StrEnum` (PEP 663, Python 3.11) extend this by making members directly usable as `int` or `str`. With `match`/`case` (PEP 634, Python 3.10), type checkers can verify that every enum member is handled, catching forgotten cases at check time.

**Since:** `enum` — Python 3.4 (PEP 435); `match`/`case` — Python 3.10 (PEP 634); `StrEnum` — Python 3.11 (PEP 663)

## What constraint it enforces

**Values are restricted to a closed, named set of members; the type checker can verify exhaustive handling and reject values outside the set.**

Unlike a bare `str` or `int`, an `Enum` type parameter guarantees that only declared members can be passed. Combined with exhaustiveness checking, the checker can prove that all branches in a `match`/`case` or `if`/`elif` chain are covered, so adding a new member surfaces every location that needs updating.

## Minimal snippet

```python
from enum import Enum

class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

def describe(c: Color) -> str:
    match c:
        case Color.RED:
            return "warm"
        case Color.GREEN:
            return "natural"
        # Missing Color.BLUE — pyright reports:
        # error: Cases within match statement do not exhaustively handle all values
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Literal types** [-> [catalog/02](02-union-literal-types.md)] | `Literal[Color.RED, Color.GREEN]` narrows an enum to a subset of members. Literal and Enum are complementary: Literal restricts *which* members, Enum defines the full set. |
| **TypeGuard / narrowing** [-> [catalog/13](13-typeguard-typeis-narrowing.md)] | `isinstance(val, Color)` narrows a `Color | str` to `Color`. Inside `match`/`case`, each branch narrows to the specific member. |
| **Never / exhaustiveness** [-> [catalog/14](14-never-noreturn.md)] | After handling all enum members, the remaining type is `Never`. `assert_never()` confirms the match is exhaustive. |
| **Union** [-> [catalog/02](02-union-literal-types.md)] | Enums are often a better alternative to `Union[Literal["a"], Literal["b"]]` because they provide methods, a namespace, and exhaustiveness support. |
| **NewType** [-> [catalog/04](04-newtype.md)] | For simple value-level tagging without methods, `NewType` may suffice. Enums are richer: they have identity, methods, and iteration. |

## Gotchas and limitations

1. **Exhaustiveness checking is checker-dependent.** pyright checks `match`/`case` exhaustiveness by default (with `reportMatchNotExhaustive`). mypy does not check `match` exhaustiveness automatically — you need `assert_never()` in a default branch or enable `warn_unreachable`.

2. **`IntEnum` and `StrEnum` weaken type safety.** Because `IntEnum` is a subtype of `int`, you can accidentally pass an `IntEnum` member where any `int` is expected, and arithmetic operations return `int`, not the enum type:

   ```python
   from enum import IntEnum
   class Priority(IntEnum):
       LOW = 1
       HIGH = 2

   x: int = Priority.LOW           # OK — IntEnum is an int (no error, but less safe)
   result = Priority.LOW + 1       # type is int, not Priority
   ```

3. **`Flag` members combine via `|`.** `Flag` and `IntFlag` support bitwise OR, producing composite values that may not match any single member. Checking `flag in MyFlag` and iterating over `MyFlag` are the primary ways to work with them.

4. **Enum members are singletons.** `Color.RED is Color.RED` is always `True`. This means `is` comparison works for enum members, but creating a new instance like `Color("red")` returns the existing member, not a new one.

5. **Cannot extend enum classes.** An enum with members cannot be subclassed to add more members. This is by design (it would break exhaustiveness), but surprises developers coming from class hierarchies.

6. **String representation differences.** `str(Color.RED)` returns `"Color.RED"` (changed in Python 3.11 from `"Color.RED"` to match `repr`). Use `.value` for the underlying value and `.name` for the member name.

## Beginner mental model

Think of an enum as a **dropdown menu in a form**. The menu has a fixed set of choices (Red, Green, Blue), and you cannot type in a custom value. The type checker acts like form validation: it ensures you handle every choice in the dropdown. When you add a new option to the menu (a new enum member), the checker highlights every place in your code that needs to handle the new option.

## Example A — Status enum with exhaustive match/case

```python
from enum import Enum
from typing import assert_never


class OrderStatus(Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


def next_action(status: OrderStatus) -> str:
    match status:
        case OrderStatus.PENDING:
            return "Process payment"
        case OrderStatus.SHIPPED:
            return "Track package"
        case OrderStatus.DELIVERED:
            return "Request review"
        case OrderStatus.CANCELLED:
            return "Archive order"
        case _ as unreachable:
            assert_never(unreachable)  # proves all cases handled


# If a new member is added (e.g., RETURNED), checkers flag the assert_never:
# error: Argument of type "Literal[OrderStatus.RETURNED]" is not assignable
#        to parameter of type "Never"


# Type safety: only OrderStatus values accepted
next_action(OrderStatus.PENDING)   # OK
next_action("pending")             # error: expected "OrderStatus", got "str"
```

## Example B — Permission flags with Flag enum

```python
from enum import Flag, auto


class Permission(Flag):
    READ = auto()      # 1
    WRITE = auto()     # 2
    EXECUTE = auto()   # 4
    ADMIN = READ | WRITE | EXECUTE


def check_access(required: Permission, actual: Permission) -> bool:
    return required in actual   # OK — Flag supports containment checks


# Compose permissions with bitwise OR
user_perms = Permission.READ | Permission.WRITE         # OK
admin_perms = Permission.ADMIN                          # OK

print(check_access(Permission.READ, user_perms))        # True
print(check_access(Permission.EXECUTE, user_perms))     # False
print(check_access(Permission.EXECUTE, admin_perms))    # True


# Type safety still applies
def grant(perm: Permission) -> None: ...

grant(Permission.READ)       # OK
grant(Permission.READ | Permission.WRITE)  # OK
grant(4)                     # error: expected "Permission", got "int"
```

## Common type-checker errors and how to read them

### Non-exhaustive match

```
# pyright
error: Cases within match statement do not exhaustively handle all values
       of type "OrderStatus"
       If exhaustive handling is not intended, add "case _: pass"

# mypy (with assert_never pattern)
error: Argument 1 to "assert_never" has incompatible type
       "Literal[OrderStatus.RETURNED]"; expected "Never"
```

**Cause:** A new enum member was added but not handled in the match statement.
**Fix:** Add a `case` branch for the missing member.

### Passing wrong type where Enum expected

```
# mypy
error: Argument 1 to "next_action" has incompatible type "str";
       expected "OrderStatus"

# pyright
error: Argument of type "str" cannot be assigned to parameter "status"
       of type "OrderStatus"
```

**Cause:** You passed a raw value instead of an enum member.
**Fix:** Use the enum member: `OrderStatus.PENDING` instead of `"pending"`. If you have a runtime string, convert with `OrderStatus(value)`.

### Comparing enum with non-member value

```
# mypy
error: Non-overlapping equality check (left operand type: "OrderStatus",
       right operand type: "Literal['pending']")
```

**Cause:** Comparing an enum member with a string literal. Enum members are compared by identity, not by value.
**Fix:** Compare with the enum member: `status == OrderStatus.PENDING`. Or use `.value` for value comparison: `status.value == "pending"`.

### IntEnum used where Enum expected

```
# pyright
error: Argument of type "Priority" cannot be assigned to parameter
       of type "OrderStatus"
```

**Cause:** Different enum types are not interchangeable, even if both inherit from `IntEnum`.
**Fix:** Use the correct enum type or convert explicitly.

## Use-case cross-references

- [-> UC-01](../usecases/01-preventing-invalid-states.md) — Enum parameters enforce valid states in public APIs.
- [-> UC-02](../usecases/02-domain-modeling.md) — Pipeline stages represented as enum members.
- [-> UC-03](../usecases/03-type-narrowing-exhaustiveness.md) — Database status columns mapped to exhaustive enums.
- [-> UC-08](../usecases/08-error-handling-types.md) — Enum error codes with exhaustive match ensure all error variants are handled.

## Source anchors

- [PEP 435 — Adding an Enum type to the Python standard library](https://peps.python.org/pep-0435/)
- [PEP 586 — Literal Types (Literal enum members)](https://peps.python.org/pep-0586/)
- [PEP 634 — Structural Pattern Matching](https://peps.python.org/pep-0634/)
- [PEP 663 — Standardizing Enum str(), repr(), and format() behaviors / StrEnum](https://peps.python.org/pep-0663/)
- [enum module documentation](https://docs.python.org/3/library/enum.html)
- [mypy — Enums](https://mypy.readthedocs.io/en/stable/literal_types.html#enum-types)
