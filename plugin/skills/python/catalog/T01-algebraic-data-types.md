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
| **Literal types** [-> [catalog/02](T02-union-intersection.md)] | `Literal[Color.RED, Color.GREEN]` narrows an enum to a subset of members. Literal and Enum are complementary: Literal restricts *which* members, Enum defines the full set. |
| **TypeGuard / narrowing** [-> [catalog/13](T14-type-narrowing.md)] | `isinstance(val, Color)` narrows a `Color | str` to `Color`. Inside `match`/`case`, each branch narrows to the specific member. |
| **Never / exhaustiveness** [-> [catalog/14](T34-never-bottom.md)] | After handling all enum members, the remaining type is `Never`. `assert_never()` confirms the match is exhaustive. |
| **Union** [-> [catalog/02](T02-union-intersection.md)] | Enums are often a better alternative to `Union[Literal["a"], Literal["b"]]` because they provide methods, a namespace, and exhaustiveness support. |
| **NewType** [-> [catalog/04](T03-newtypes-opaque.md)] | For simple value-level tagging without methods, `NewType` may suffice. Enums are richer: they have identity, methods, and iteration. |

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

- [-> UC-01](../usecases/UC01-invalid-states.md) — Enum parameters enforce valid states in public APIs.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Pipeline stages represented as enum members.
- [-> UC-03](../usecases/UC03-exhaustiveness.md) — Database status columns mapped to exhaustive enums.
- [-> UC-08](../usecases/UC08-error-handling.md) — Enum error codes with exhaustive match ensure all error variants are handled.

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
from enum import Enum

class Color(Enum):
    RED = "red"
    GREEN = "green"

def is_red(c: Color) -> bool:
    return c == "red"  # type error: comparing Color with str literal

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

```python
from enum import IntEnum

class Priority(IntEnum):
    LOW = 1
    HIGH = 2

def set_priority(p: Priority) -> None:
    pass

set_priority(Priority.LOW)  # OK
set_priority(1)             # no error! IntEnum is subtype of int
set_priority(99)            # no error! any int accepted
```

**Fix:** Use regular `Enum` with integer values, or validate at runtime:

```python
from enum import Enum

class Priority(Enum):
    LOW = 1
    HIGH = 2

set_priority(1)  # error: expected "Priority", got "int"
```

#### 4. Forgetting exhaustiveness in pattern matching

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
            return 10
        # Missing TRIANGLE! — pyright warns, mypy needs assert_never
```

**Fix:** Use catch-all with `assert_never`:

```python
from typing import assert_never

def area(s: Shape) -> float:
    match s:
        case Shape.CIRCLE:
            return 3.14
        case Shape.RECT:
            return 10
        case Shape.TRIANGLE:
            return 5
        case _ as e:
            assert_never(e)  # catches missing cases during refactoring
```

#### 5. Using `isinstance` when exact member check is needed

```python
from enum import Enum

class Status(Enum):
    PENDING = "pending"
    APPROVED = "approved"

def check(s: Status | str) -> bool:
    if isinstance(s, Status):  # checks if Status, not which member
        return True  # returns True for both PENDING and APPROVED
```

**Fix:** Match on specific members or use `in`:

```python
def is_pending(s: Status | str) -> bool:
    return s == Status.PENDING
    # or: return s in (Status.PENDING,)
```

### Antipatterns with Other Techniques → Enum Is Better

#### 1. Magic strings without type checking

```python
# Bad: typos compile but fail at runtime
def process_order(status: str) -> str:
    if status == "pending":
        return "processing"
    elif status == "shipped":
        return "in transit"
    # typo: "shiped" passes type check, fails at runtime

def process_order_v2(status: str) -> str:
    if status == "pending":
        return "processing"
    elif status == "shipped":
        return "in transit"
    elif status == "cancelled":  # added new case
        return "cancelled"
    # what if called with "SHIPED"? No error until runtime
```

**Fix:** Enum enforces closed set:

```python
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    SHIPPING = "shipping"
    CANCELLED = "cancelled"

def process_order(status: OrderStatus) -> str:
    match status:
        case OrderStatus.PENDING:
            return "processing"
        case OrderStatus.SHIPPING:
            return "in transit"
        case OrderStatus.CANCELLED:
            return "cancelled"

process_order("pending")  # error: expected OrderStatus, got str
process_order("SHIPED")   # error: "SHIPED" not a valid value
```

#### 2. Union of strings without exhaustiveness

```python
from typing import Literal

Status = Literal["pending", "shipped", "cancelled"]

def handle(status: Status) -> str:
    if status == "pending":
        return "processing"
    elif status == "shipped":
        return "tracking"
    # No way to detect missing "cancelled" at type-check time
```

**Fix:** Enum with `match` provides exhaustiveness checking:

```python
from enum import Enum

class Status(Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"

def handle(status: Status) -> str:
    match status:
        case Status.PENDING:
            return "processing"
        case Status.SHIPPED:
            return "tracking"
        # Missing CANCELLED — pyright: "Cases do not exhaustively handle"
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
    def __init__(self):
        self.status = OrderStatus.PENDING

order = Order()
order.status = OrderStatus.SHIPPED  # OK — only one state at a time
# order.status = OrderStatus.PENDING | OrderStatus.SHIPPED  # type error
```

#### 4. Integer constants scattered across codebase

```python
# Bad: magic numbers, no grouping, no type safety
PENDING = 0
SHIPPED = 1
DELIVERED = 2

def get_status_name(status_code: int) -> str:
    if status_code == 0:
        return "pending"
    elif status_code == 1:
        return "shipped"
    # What does 99 mean? Any int passes type check
```

**Fix:** Enum groups constants with type safety:

```python
from enum import Enum

class OrderStatus(Enum):
    PENDING = 0
    SHIPPED = 1
    DELIVERED = 2

def get_status_name(status: OrderStatus) -> str:
    return status.name.lower()

get_status_name(99)  # error: expected "OrderStatus", got "Literal[99]"
```

#### 5. Using `Flag` for non-composite states

```python
from enum import Flag

# Bad: Flag implies states can combine
class UserStatus(Flag):
    ACTIVE = auto()
    BANNED = auto()
    VERIFIED = auto()

status = UserStatus.ACTIVE | UserStatus.BANNED  # combines to composite value
# Can a user be ACTIVE and BANNED at the same time? Probably not.
```

**Fix:** Use regular `Enum` for mutually exclusive states:

```python
from enum import Enum

class UserStatus(Enum):
    ACTIVE = "active"
    BANNED = "banned"
    VERIFIED = "verified"

# status = UserStatus.ACTIVE | UserStatus.BANNED  # error: unsupported operand
```

Use `Flag` only when the domain allows combinations (permissions, bit flags).

## Use-Case Cross-References

- [-> UC-01](../usecases/UC01-invalid-states.md) — Enum parameters enforce valid states in public APIs.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Pipeline stages represented as enum members.
- [-> UC-03](../usecases/UC03-exhaustiveness.md) — Database status columns mapped to exhaustive enums.
- [-> UC-08](../usecases/UC08-error-handling.md) — Enum error codes with exhaustive match ensure all error variants are handled.

## Source Anchors

- [PEP 435 — Adding an Enum type to the Python standard library](https://peps.python.org/pep-0435/)
- [PEP 586 — Literal Types (Literal enum members)](https://peps.python.org/pep-0586/)
- [PEP 634 — Structural Pattern Matching](https://peps.python.org/pep-0634/)
- [PEP 663 — Standardizing Enum str(), repr(), and format() behaviors / StrEnum](https://peps.python.org/pep-0663/)
- [enum module documentation](https://docs.python.org/3/library/enum.html)
- [mypy — Enums](https://mypy.readthedocs.io/en/stable/literal_types.html#enum-types)
