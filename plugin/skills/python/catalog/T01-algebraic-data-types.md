# Enums with Static Typing

## What it is

Python's `enum` module (PEP 435, Python 3.4) provides named, immutable sets of values. When combined with type annotations, enums give the type checker a *closed set* of members — it knows every possible value and can verify exhaustiveness. `IntEnum` (Python 3.4, part of PEP 435) and `StrEnum` (Python 3.11, no dedicated PEP) extend this by making members directly usable as `int` or `str`. With `match`/`case` (PEP 634, Python 3.10), type checkers can verify that every enum member is handled, catching forgotten cases at check time.

**Since:** `enum`, `IntEnum` — Python 3.4 (PEP 435); `match`/`case` — Python 3.10 (PEP 634); `StrEnum` — Python 3.11

## What constraint it enforces

**Values are restricted to a closed, named set of members; the type checker can verify exhaustive handling and reject values outside the set.**

Unlike a bare `str` or `int`, an `Enum` type parameter guarantees that only declared members can be passed. Combined with exhaustiveness checking, the checker can prove that all branches in a `match`/`case` or `if`/`elif` chain are covered, so adding a new member surfaces every location that needs updating.

## Minimal snippet

```python
# expect-error
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
        # error: Function with declared return type "str" must return value on all code paths
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Literal types** [-> T02](T02-union-intersection.md) | `Literal[Color.RED, Color.GREEN]` narrows an enum to a subset of members. Literal and Enum are complementary: Literal restricts *which* members, Enum defines the full set. |
| **TypeGuard / narrowing** [-> T14](T14-type-narrowing.md) | `isinstance(val, Color)` narrows a `Color | str` to `Color`. Inside `match`/`case`, each branch narrows to the specific member. |
| **Never / exhaustiveness** [-> T34](T34-never-bottom.md) | After handling all enum members, the remaining type is `Never`. `assert_never()` confirms the match is exhaustive. |
| **Union** [-> T02](T02-union-intersection.md) | Enums are often a better alternative to `Union[Literal["a"], Literal["b"]]` because they provide methods, a namespace, and exhaustiveness support. |
| **NewType** [-> T03](T03-newtypes-opaque.md) | For simple value-level tagging without methods, `NewType` may suffice. Enums are richer: they have identity, methods, and iteration. |

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

6. **String representation differences.** For a plain `Enum`, `str(Color.RED)` returns `"Color.RED"`. Python 3.11 changed `str()` for `IntEnum`, `IntFlag`, and `StrEnum` to return just the value (e.g., `str(Priority.LOW)` is `"1"`), and changed `format()` of plain enums to match `str()`. Rather than relying on string formatting, use `.value` for the underlying value and `.name` for the member name.

## Beginner mental model

Think of an enum as a **dropdown menu in a form**. The menu has a fixed set of choices (Red, Green, Blue), and you cannot type in a custom value. The type checker acts like form validation: it ensures you handle every choice in the dropdown. When you add a new option to the menu (a new enum member), the checker highlights every place in your code that needs to handle the new option.

## Example A — Status enum with exhaustive match/case

```python
# expect-error
from enum import Enum


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


# The declared `-> str` return type keeps the match honest: if a new member
# (e.g., RETURNED) is added, pyright reports both a non-exhaustive match
# (reportMatchNotExhaustive) and a missing return path (reportReturnType).


# Type safety: only OrderStatus values accepted
next_action(OrderStatus.PENDING)   # OK
next_action("pending")             # error: Argument of type "Literal['pending']" cannot be assigned to parameter "status" of type "OrderStatus"
```

## Example B — Permission flags with Flag enum

```python
# expect-error
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
grant(4)                     # error: Argument of type "Literal[4]" cannot be assigned to parameter "perm" of type "Permission"
```

## Common type-checker errors and how to read them

### Non-exhaustive match

```text
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

```text
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

```text
# mypy
error: Non-overlapping equality check (left operand type: "OrderStatus",
       right operand type: "Literal['pending']")

# pyright
error: Condition will always evaluate to False since the types
       "OrderStatus" and "Literal['pending']" have no overlap
```

**Cause:** Comparing an enum member with a string literal. Enum members are compared by identity, not by value.
**Fix:** Compare with the enum member: `status == OrderStatus.PENDING`. Or use `.value` for value comparison: `status.value == "pending"`.

### IntEnum used where Enum expected

```text
# pyright
error: Argument of type "Priority" cannot be assigned to parameter
       of type "OrderStatus"
```

**Cause:** Different enum types are not interchangeable, even if both inherit from `IntEnum`.
**Fix:** Use the correct enum type or convert explicitly.

## When to Use

- **Closed sets of named constants** — statuses (`Pending | Shipped | Delivered`), directions (`North | South | East | West`), log levels, HTTP method enums
- **State machines** — each state as an enum member; `match`/`case` guarantees all state transitions are handled
- **Exhaustive handling required** — when forgetting a case is a bug (e.g., parsing protocol messages, handling API response types)
- **Replacing magic strings/numbers** — `"pending"` → `OrderStatus.PENDING` for type safety and IDE autocomplete
- **Flags and bitmasks** — `Permission.READ | Permission.WRITE` using `Flag` enum with bitwise operations
- **Serializer compatibility** — `StrEnum` members serialize as strings without extra mapping code

### When NOT to Use

- **Open/extensible value sets** — if new values may be added at runtime or by external plugins
- **Values that need complex behavior** — enums with custom methods that diverge significantly should be classes
- **Simple string/number literals** — `Literal["red", "green", "blue"]` is simpler when you don't need a namespace
- **Bitwise operations on `Enum`** — use `Flag` or `IntFlag` for flag-like behavior; regular `Enum` values don't combine
- **Inheriting to add behavior** — enums cannot be subclassed after defining members; define all members first
- **When values are computed** — enum members are compile-time constants, not computed values

### Antipatterns When Using Enums

#### 1. Comparing enum member with raw value

```python
# expect-error
from enum import Enum

class Color(Enum):
    RED = "red"
    GREEN = "green"

def is_red(c: Color) -> bool:
    return c == "red"  # error: Condition will always evaluate to False since the types "Color" and "Literal['red']" have no overlap

def is_red_fixed(c: Color) -> bool:
    return c == Color.RED  # correct
    # or: return c.value == "red"  # value comparison
```

#### 2. Switching on `.value` instead of the member

```python
from enum import Enum

class Status(Enum):
    ACTIVE = 1
    INACTIVE = 2

def label(s: Status) -> str:
    match s.value:  # bad: loses type narrowing
        case 1:
            return "active"
        case 2:
            return "inactive"

def label_fixed(s: Status) -> str:
    match s:  # good: proper narrowing and exhaustiveness
        case Status.ACTIVE:
            return "active"
        case Status.INACTIVE:
            return "inactive"
```

#### 3. Using `IntEnum` where strict type safety is needed

The leak is one-directional: the checker still rejects a bare `int` where a `Priority` is expected, but `IntEnum` members silently flow *out* into any `int` context, where the `Priority`-ness is lost:

```python
from enum import IntEnum

class Priority(IntEnum):
    LOW = 1
    HIGH = 2

def send_alert(level: int) -> None:
    pass

send_alert(Priority.LOW)      # accepted — IntEnum members pass as plain int
timeout = Priority.HIGH * 60  # result type is int, not Priority
is_low = Priority.LOW == 1    # True — value comparison crosses the type boundary
```

**Fix:** Use a regular `Enum` if members should never be interchangeable with `int`:

```python
# expect-error
from enum import Enum

class Priority(Enum):
    LOW = 1
    HIGH = 2

def send_alert(level: int) -> None:
    pass

send_alert(Priority.LOW)  # error: Argument of type "Literal[Priority.LOW]" cannot be assigned to parameter "level" of type "int"
```

#### 4. Forgetting exhaustiveness in pattern matching

```python
# expect-error
from enum import Enum

class Shape(Enum):
    CIRCLE = "circle"
    RECT = "rect"
    TRIANGLE = "triangle"

def area(s: Shape) -> float:  # error: Function with declared return type "float" must return value on all code paths
    match s:  # error: Cases within match statement do not exhaustively handle all values
        case Shape.CIRCLE:
            return 3.14
        case Shape.RECT:
            return 10.0
        # forgot Shape.TRIANGLE
```

**Fix:** Handle every member; the declared return type keeps the match honest:

```python
from enum import Enum

class Shape(Enum):
    CIRCLE = "circle"
    RECT = "rect"
    TRIANGLE = "triangle"

def area(s: Shape) -> float:
    match s:
        case Shape.CIRCLE:
            return 3.14
        case Shape.RECT:
            return 10.0
        case Shape.TRIANGLE:
            return 5.0
```

For mypy (which does not check match exhaustiveness by default), or for functions whose return type does not force coverage, add a `case _ as unreachable: assert_never(unreachable)` branch.

### Antipatterns Fixed by Enums

#### 1. Magic strings scattered across the codebase

```python
# Bad: typos type-check; failures surface only at runtime
def process_order(status: str) -> str:
    if status == "pending":
        return "processing"
    elif status == "shipped":
        return "in transit"
    return "unknown"  # any typo silently lands here

process_order("shiped")  # typo passes the type checker
```

**Fix:** Enum enforces a closed set:

```python
# expect-error
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    SHIPPED = "shipped"

def process_order(status: OrderStatus) -> str:
    match status:
        case OrderStatus.PENDING:
            return "processing"
        case OrderStatus.SHIPPED:
            return "in transit"

process_order("shiped")  # error: Argument of type "Literal['shiped']" cannot be assigned to parameter "status" of type "OrderStatus"
```

#### 2. String handlers with no exhaustiveness safety net

When a handler returns nothing, no return-type analysis forces you to cover every value — a missing branch is silently skipped:

```python
from typing import Literal

type Status = Literal["pending", "shipped", "cancelled"]

def log_status(status: Status) -> None:
    if status == "pending":
        print("processing")
    elif status == "shipped":
        print("tracking")
    # "cancelled" silently falls through — the checker stays quiet
```

**Fix:** A `match` statement over an enum (or a `Literal`) gets exhaustiveness checking from pyright even without a return type:

```python
# expect-error
from enum import Enum

class Status(Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"

def log_status(status: Status) -> None:
    match status:  # error: Cases within match statement do not exhaustively handle all values
        case Status.PENDING:
            print("processing")
        case Status.SHIPPED:
            print("tracking")
        # pyright flags the missing CANCELLED case (reportMatchNotExhaustive)
```

#### 3. Boolean flags for mutually exclusive states

```python
# Bad: invalid state representation possible
class Order:
    def __init__(self):
        self.is_pending = True
        self.is_shipped = False
        self.is_delivered = False

order = Order()
order.is_pending = True
order.is_shipped = True  # order pending AND shipped? Invalid state!
```

**Fix:** Enum makes invalid states unrepresentable:

```python
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"

class Order:
    def __init__(self) -> None:
        self.status = OrderStatus.PENDING

order = Order()
order.status = OrderStatus.SHIPPED  # OK — exactly one state at a time
```

#### 4. Integer constants scattered across codebase

```python
# Bad: magic numbers, no grouping, no type safety
PENDING = 0
SHIPPED = 1

def get_status_name(status_code: int) -> str:
    if status_code == 0:
        return "pending"
    elif status_code == 1:
        return "shipped"
    return "unknown"  # what does 99 mean? Any int passes the type checker

get_status_name(99)  # accepted — silently "unknown"
```

**Fix:** Enum groups the constants with type safety:

```python
# expect-error
from enum import Enum

class OrderStatus(Enum):
    PENDING = 0
    SHIPPED = 1

def get_status_name(status: OrderStatus) -> str:
    return status.name.lower()

get_status_name(99)  # error: Argument of type "Literal[99]" cannot be assigned to parameter "status" of type "OrderStatus"
```

#### 5. Using `Flag` for non-composite states

```python
from enum import Flag, auto

# Bad: Flag implies states can combine
class UserStatus(Flag):
    ACTIVE = auto()
    BANNED = auto()
    VERIFIED = auto()

status = UserStatus.ACTIVE | UserStatus.BANNED  # combines to a composite value
# Can a user be ACTIVE and BANNED at the same time? Probably not.
```

**Fix:** Use regular `Enum` for mutually exclusive states:

```python
# expect-error
from enum import Enum

class UserStatus(Enum):
    ACTIVE = "active"
    BANNED = "banned"
    VERIFIED = "verified"

status = UserStatus.ACTIVE | UserStatus.BANNED  # error: Operator "|" not supported for types "Literal[UserStatus.ACTIVE]" and "Literal[UserStatus.BANNED]"
```

Use `Flag` only when the domain allows combinations (permissions, bit flags).

## Use-case cross-references

- [-> UC01](../usecases/UC01-invalid-states.md) — Enum parameters enforce valid states in public APIs.
- [-> UC02](../usecases/UC02-domain-modeling.md) — Pipeline stages represented as enum members.
- [-> UC03](../usecases/UC03-exhaustiveness.md) — Database status columns mapped to exhaustive enums.
- [-> UC08](../usecases/UC08-error-handling.md) — Enum error codes with exhaustive match ensure all error variants are handled.

## Source Anchors

- [PEP 435 — Adding an Enum type to the Python standard library](https://peps.python.org/pep-0435/)
- [PEP 586 — Literal Types (Literal enum members)](https://peps.python.org/pep-0586/)
- [PEP 634 — Structural Pattern Matching](https://peps.python.org/pep-0634/)
- [enum module documentation (including `StrEnum`, added in 3.11)](https://docs.python.org/3/library/enum.html)
- [mypy — Enums](https://mypy.readthedocs.io/en/stable/literal_types.html#enum-types)
