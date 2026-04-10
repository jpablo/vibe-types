# Type Narrowing and Exhaustiveness

## The constraint

After a type check, the type is narrowed so only valid operations are available. All cases of a Union or enum must be handled; missing a branch is a type error. The checker guarantees that no case falls through unhandled.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Basic annotations / Optional | `X | None` forces explicit None handling before use | [-> catalog/01](../catalog/T13-null-safety.md) |
| Union | Multi-type values that must be narrowed before use | [-> catalog/02](../catalog/T02-union-intersection.md) |
| Enums | Closed sets of named values enabling exhaustive matching | [-> catalog/05](../catalog/T01-algebraic-data-types.md) |
| TypeGuard / TypeIs | User-defined narrowing functions for custom type predicates | [-> catalog/13](../catalog/T14-type-narrowing.md) |
| Never / assert_never | Bottom type that proves exhaustiveness — unreachable code is a type error if reachable | [-> catalog/14](../catalog/T34-never-bottom.md) |

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

---

## When to Use This Technique

Use exhaustiveness checking when:

- **Adding variants should be a breaking change** — you want the type checker to enforce that all handlers are updated when a new variant is added.
- **The union is closed (internal)** — you control the type definition and know all variants upfront.
- **Silent failures are unacceptable** — unhandled variants could cause data loss or incorrect behavior.

**Example: Payment processing (must handle all methods)**

```python
from dataclasses import dataclass
from typing import assert_never

@dataclass
class CardPayment:
    method: str = "card"
    number: str
    cvv: str

@dataclass
class PayPalPayment:
    method: str = "paypal"
    email: str

@dataclass
class CryptoPayment:
    method: str = "crypto"
    wallet: str

Payment = CardPayment | PayPalPayment | CryptoPayment

def process_payment(p: Payment) -> None:
    match p:
        case CardPayment(number=num):
            print(f"Charging card ending {num[-4:]}")
        case PayPalPayment(email=email):
            print(f"Charging PayPal {email}")
        case CryptoPayment(wallet=wallet):
            print(f"Transferring to {wallet}")
        case _:
            assert_never(p)  # type error if new method added
```

---

## When NOT to Use This Technique

Avoid exhaustiveness checking when:

- **The union is external or evolving** — third-party APIs may add variants you don't handle yet.
- **You want gradual rollout** — new variants should work even if handlers are not ready.
- **The type is effectively open** — e.g., user-defined enum values or plugin architectures.

**Example: Event listener (forward-compatible)**

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class ClickEvent:
    type: str = "click"
    x: int
    y: int

@dataclass
class ScrollEvent:
    type: str = "scroll"
    top: int

@dataclass
class ResizeEvent:
    type: str = "resize"
    width: int
    height: int

WindowEvent = ClickEvent | ScrollEvent | ResizeEvent

def handle_event(e: WindowEvent) -> None:
    match e:
        case ClickEvent(x=x, y=y):
            print(f"click at {x},{y}")
        case ScrollEvent(top=top):
            print(f"scroll at {top}")
        case ResizeEvent(width=w, height=h):
            print(f"resize to {w}x{h}")
        case _:
            print(f"Unhandled event: {e}")  # intentional
```

---

## Antipatterns When Using This Technique

### 1. Omitting `assert_never` default

**Antipattern:**

```python
from dataclasses import dataclass
from typing import assert_never

@dataclass
class Circle:
    kind: str = "circle"
    radius: float

@dataclass
class Rectangle:
    kind: str = "rectangle"
    width: float
    height: float

@dataclass
class Triangle:
    kind: str = "triangle"
    base: float
    height: float

Shape = Circle | Rectangle | Triangle

def area(s: Shape) -> float:
    match s:
        case Circle(radius=r):
            return 3.14159 * r ** 2
        case Rectangle(width=w, height=h):
            return w * h
        # forgot Triangle!
        case _:
            return 0  # silent bug
```

**Fix:**

```python
def area(s: Shape) -> float:
    match s:
        case Circle(radius=r):
            return 3.14159 * r ** 2
        case Rectangle(width=w, height=h):
            return w * h
        case Triangle(base=b, height=h):
            return 0.5 * b * h
        case _:
            assert_never(s)  # type checker catches omissions
```

### 2. Using exhaustive pattern on open/evolving types

**Antipattern:**

```python
from dataclasses import dataclass
from typing import assert_never

@dataclass
class ApiStatus:
    status: str
    message: str

def render_status(s: ApiStatus) -> str:
    match s.status:
        case "idle":
            return "Waiting..."
        case "loading":
            return "Loading..."
        case "success":
            return "Done"
        case "error":
            return "Failed"
        case _:
            assert_never(s)  # breaks when API adds "retrying"
```

**Fix:**

```python
HANDLED_STATUSES = {"idle", "loading", "success", "error"}

STATUS_MESSAGES = {
    "idle": "Waiting...",
    "loading": "Loading...",
    "success": "Done",
    "error": "Failed"
}

def render_status(s: ApiStatus) -> str:
    return STATUS_MESSAGES.get(s.status, "Unknown status")  # handles future variants
```

### 3. `assert_never` at wrong nesting level

**Antipattern:**

```python
from dataclasses import dataclass
from typing import assert_never

@dataclass
class PushAction:
    type: str = "push"

@dataclass
class PopAction:
    type: str = "pop"

@dataclass
class ClearAction:
    type: str = "clear"

Action = PushAction | PopAction | ClearAction

def handle(a: Action) -> None:
    if a.type != "clear":
        match a:
            case PushAction():
                print("push")
            case _:
                assert_never(a)  # error here but misses pop, clear
```

**Fix:**

```python
def handle(a: Action) -> None:
    match a:
        case PushAction():
            print("push")
        case PopAction():
            print("pop")
        case ClearAction():
            print("clear")
        case _:
            assert_never(a)
```

---

## Antipatterns Where Exhaustiveness Wins

### 1. Default fallback instead of exhaustive match

**Antipattern:**

```python
from dataclasses import dataclass

class Command:
    def __init__(self, cmd: str):
        self.cmd = cmd

def execute(cmd: Command) -> str:
    if cmd.cmd == "start":
        return "▶️"
    if cmd.cmd == "stop":
        return "⏹"
    if cmd.cmd == "pause":
        return "⏸"
    return "?"  # forgot resume, silent bug
```

**Better with exhaustiveness:**

```python
from dataclasses import dataclass
from typing import assert_never

@dataclass
class StartCmd:
    type: str = "start"

@dataclass
class StopCmd:
    type: str = "stop"

@dataclass
class PauseCmd:
    type: str = "pause"

@dataclass
class ResumeCmd:
    type: str = "resume"

Command = StartCmd | StopCmd | PauseCmd | ResumeCmd

def execute(cmd: Command) -> str:
    match cmd:
        case StartCmd():
            return "▶️"
        case StopCmd():
            return "⏹"
        case PauseCmd():
            return "⏸"
        case ResumeCmd():
            return "⏯"
        case _:
            assert_never(cmd)
```

### 2. Magic string comparison instead of discriminated union

**Antipattern:**

```python
def status_icon(status: str) -> str:
    if status == "pending":
        return "🕐"
    if status == "shipped":
        return "🚚"
    return "❓"  # typo "shiped" passes silently
```

**Better with exhaustiveness:**

```python
from dataclasses import dataclass
from typing import assert_never

@dataclass
class Order:
    status: "Pending | Shipped | Delivered"
    
Pending = "pending"
Shipped = "shipped"
Delivered = "delivered"

def status_icon(o: Order) -> str:
    match o.status:
        case "pending":
            return "🕐"
        case "shipped":
            return "🚚"
        case "delivered":
            return "✅"
        case _:
            assert_never(o.status)
```

### 3. Runtime string checks for JSON data

**Antipattern:**

```python
def area(data: dict) -> float:
    kind = data.get("kind")
    if kind == "circle" and "radius" in data:
        return 3.14159 * data["radius"] ** 2
    if kind == "rectangle":
        return data.get("width", 0) * data.get("height", 0)
    return 0  # loses all type safety
```

**Better with exhaustiveness:**

```python
from dataclasses import dataclass
from typing import assert_never

@dataclass
class Circle:
    kind: str = "circle"
    radius: float

@dataclass
class Rectangle:
    kind: str = "rectangle"
    width: float
    height: float

Shape = Circle | Rectangle

def area(s: Shape) -> float:
    match s:
        case Circle(radius=r):
            return 3.14159 * r ** 2
        case Rectangle(width=w, height=h):
            return w * h
        case _:
            assert_never(s)
```

### 4. Partial handling with forgotten TODO comment

**Antipattern:**

```python
from dataclasses import dataclass

@dataclass
class User:
    role: str  # "admin" | "moderator" | "viewer"

def can_ban(u: User) -> bool:
    if u.role == "admin":
        return True
    # TODO: handle moderator
    return False  # incomplete, comment forgotten
```

**Better with exhaustiveness:**

```python
from dataclasses import dataclass
from typing import assert_never

@dataclass
class Admin:
    role: str = "admin"

@dataclass
class Moderator:
    role: str = "moderator"

@dataclass
class Viewer:
    role: str = "viewer"

User = Admin | Moderator | Viewer

def can_ban(u: User) -> bool:
    match u:
        case Admin():
            return True
        case Moderator():
            return True
        case Viewer():
            return False
        case _:
            assert_never(u)  # type checker enforces completeness
```
