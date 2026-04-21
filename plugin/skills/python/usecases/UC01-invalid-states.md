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

### E — Parse, don't validate

Instead of checking a condition and discarding the proof, return a refined type that carries the guarantee. A parser is a function from less-structured input to more-structured output.

```python
from dataclasses import dataclass
from typing import Self

# Validation: checks and throws — caller gains no type-level info
def validate_non_empty(items: list[str]) -> None:
    if not items:
        raise ValueError("list cannot be empty")

# Parsing: checks and returns a refined type
@dataclass(frozen=True)
class NonEmptyList[T]:
    head: T
    tail: list[T]

    @classmethod
    def parse(cls, items: list[T]) -> Self | None:
        if not items:
            return None
        return cls(head=items[0], tail=items[1:])

# Smart constructor for a domain primitive
@dataclass(frozen=True)
class PortNumber:
    _value: int

    @classmethod
    def parse(cls, n: int) -> Self | None:
        if 0 < n < 65536:
            return cls(n)
        return None

    @property
    def value(self) -> int:
        return self._value

# Downstream code never needs to re-validate
def connect(port: PortNumber) -> None:
    print(f"Connecting to port {port.value}")  # always valid

match PortNumber.parse(8080):
    case PortNumber() as p:
        connect(p)
    case None:
        print("invalid port")
```

**Key insight:** functions returning `None` or raising after checks are validation — they discard the information. Functions returning a refined type (`T | None`, a wrapper class) are parsing — they preserve it. Prefer parsing.

See: [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)

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

## When to use this technique

Use when your domain has invariants that should be enforced by the type system rather than runtime checks:

```python
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"

def transition(order_status: OrderStatus, new_status: OrderStatus) -> None:
    if order_status == OrderStatus.CANCELLED and new_status != OrderStatus.CANCELLED:
        raise ValueError("Cannot transition from cancelled")
```

Use when data depends on state:

```python
from dataclasses import dataclass
from typing import Union

@dataclass
class Idle:
    status: str = "idle"

@dataclass
class Loading:
    status: str = "loading"
    data: bytes

@dataclass
class Success:
    status: str = "success"
    data: bytes
    result: str

FormState = Union[Idle, Loading, Success]
```

Use at system boundaries where untrusted input enters:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class UserId:
    _value: str

    @classmethod
    def parse(cls, raw: str) -> "UserId | None":
        return cls(raw.strip()) if len(raw) >= 3 else None
```

## When NOT to use this technique

Do NOT use when the cost of type complexity exceeds the benefit:

```python
def add_tax(amount: float, rate: float) -> float:
    return amount * (1 + rate)

# Tax rate validation can be a simple runtime check
```

Do NOT use when dynamic flexibility is required:

```python
def load_config(path: str) -> dict[str, object]:
    import json
    with open(path) as f:
        return json.load(f)

# Runtime flexibility needed; phantom types or branded types add no value here
```

Do NOT use in tight numerical loops where boxing adds overhead:

```python
import numpy as np

def process(buffer: np.ndarray) -> None:
    np.sin(buffer, out=buffer)

# Wrapping ndarray elements in branded types would require boxing/unboxing
```

## Antipatterns when using this technique

### Antipattern 1 — Over-nesting unions

```python
from dataclasses import dataclass
from typing import Union

@dataclass
class ListResponse:
    kind: str = "list"
    items: list[object] | None = None

@dataclass
class ItemResponse:
    kind: str = "item"
    item: object

@dataclass
class Response:
    kind: str
    data: Union[ListResponse, ItemResponse, None]  # ❌ deeply nested unions

# ✅ Better: flatten with meaningful state names
@dataclass
class OkList:
    kind: str = "ok-list"
    items: list[object]

@dataclass
class OkItem:
    kind: str = "ok-item"
    item: object

@dataclass
class Empty:
    kind: str = "empty"

@dataclass
class Error:
    kind: str = "error"
    code: int
    message: str

Response = Union[OkList, OkItem, Empty, Error]
```

### Antipattern 2 — Using NewType without validation

```python
from typing import NewType

EmailAddress = NewType("EmailAddress", str)

def send_email(email: EmailAddress) -> None:
    # ❌ No validation — "invalid" is a valid EmailAddress
    print(f"Sending to {email}")

send_email(EmailAddress("invalid"))  # No guarantee of validity

# ✅ Better: use dataclass with parser
from dataclasses import dataclass

@dataclass(frozen=True)
class Email:
    _value: str

    @classmethod
    def parse(cls, raw: str) -> "Email | None":
        import re
        return cls(raw.strip().lower()) if re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", raw) else None
```

### Antipattern 3 — Overusing enums for simple cases

```python
from enum import Enum

# ❌ Overhead for binary state
class BooleanState(Enum):
    TRUE = True
    FALSE = False

# ✅ Use bool or Literal
from typing import Literal

def set_enabled(v: Literal[True, False]) -> None: ...
```

### Antipattern 4 — Optional fields instead of discriminated unions

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: str
    name: Optional[str] = None
    email: Optional[str] = None

user = User(id="1")  # ❌ Invalid: minimal user with no identity

# ✅ Better: use discriminated union
@dataclass
class AnonymizedUser:
    kind: str = "anonymized"
    id: str

@dataclass
class FullUser:
    kind: str = "full"
    id: str
    name: str
    email: str

User = AnonymizedUser | FullUser
```

### Antipattern 5 — Validating downstream instead of at boundary

```python
def is_valid_email(raw: str) -> bool:
    import re
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", raw))

def send_email(raw: str) -> None:
    if not is_valid_email(raw):
        raise ValueError("Invalid email")
    # ... repeated check at every call site

# ✅ Better: parse at boundary, types enforce validity
def send_email(email: Email) -> None:
    # email is guaranteed valid — no check needed
    pass
```

## Antipatterns other techniques create (that this fixes)

### Runtime guards repeated everywhere

```python
def connect(host: str, port: int) -> None:
    if not (1 <= port <= 65535):
        raise ValueError(f"Invalid port: {port}")
    print(f"Connecting to {host}:{port}")

def bind(host: str, port: int) -> None:
    if not (1 <= port <= 65535):  # ❌ duplicate check
        raise ValueError(f"Invalid port: {port}")
    print(f"Binding to {host}:{port}")

# ✅ Fix: branded type validates once
@dataclass(frozen=True)
class Port:
    _value: int

    @classmethod
    def parse(cls, n: int) -> "Port | None":
        return cls(n) if 1 <= n <= 65535 else None

def connect(host: str, port: Port) -> None:
    print(f"Connecting to {host}:{port._value}")  # always valid

def bind(host: str, port: Port) -> None:
    print(f"Binding to {host}:{port._value}")  # always valid
```

### Boolean returns lose information

```python
def is_valid_email(s: str) -> bool:
    import re
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", s))

ok = is_valid_email("test")  # ❌ bool carries no type info
# s is still str, no guarantee of validity

# ✅ Fix: parser returns refined type
@dataclass(frozen=True)
class EmailAddress:
    _value: str

    @classmethod
    def parse(cls, s: str) -> "EmailAddress | None":
        import re
        return cls(s.strip().lower()) if re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", s) else None

email = EmailAddress.parse("test@example.com")
if email is not None:
    send(to=email)  # typed EmailAddress
```

### Dataclass with optional fields

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Payment:
    amount: float
    transaction_id: Optional[str] = None
    refund_date: Optional[str] = None

# ❌ Invalid state: both transaction_id and refund_date without proper flow
invalid = Payment(amount=100, transaction_id="tx1", refund_date="2024-01-01")

# ✅ Fix: discriminated union enforces valid states
@dataclass
class Unpaid:
    kind: str = "unpaid"
    amount: float

@dataclass
class Paid:
    kind: str = "paid"
    amount: float
    transaction_id: str

@dataclass
class Refunded:
    kind: str = "refunded"
    amount: float
    transaction_id: str
    refund_date: str

Payment = Unpaid | Paid | Refunded
```

### Documentation as spec

```python
from dataclasses import dataclass

@dataclass
class HttpRequest:
    method: str  # @must be "GET"|"POST"|"PUT"|"DELETE"
    body: object | None = None  # @required when method is "POST" or "PUT"

# ❌ State documented but not enforced
request = HttpRequest(method="PATCH", body=None)

# ✅ Fix: types enforce the spec
@dataclass
class GetRequest:
    kind: str = "GET"
    body: None = None

@dataclass
class PostRequest:
    kind: str = "POST"
    body: object

@dataclass
class PutRequest:
    kind: str = "PUT"
    body: object

@dataclass
class DeleteRequest:
    kind: str = "DELETE"
    body: None = None

HttpRequest = GetRequest | PostRequest | PutRequest | DeleteRequest
```

## Source anchors

- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
- [PEP 586 — Literal Types](https://peps.python.org/pep-0586/)
- [PEP 484 — NewType](https://peps.python.org/pep-0484/#newtype-helper-function)
- [Python `enum` module documentation](https://docs.python.org/3/library/enum.html)
- [mypy — Literal types](https://mypy.readthedocs.io/en/stable/literal_types.html)
