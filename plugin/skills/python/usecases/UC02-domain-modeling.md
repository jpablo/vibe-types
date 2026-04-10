# Domain Modeling

## The constraint

Domain primitives carry semantic meaning that prevents mix-ups. A `UserId` is not an `int`; a `Config` dict has a known shape. The type checker rejects code that confuses unrelated domain concepts even when their runtime representations coincide.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Basic annotations | Attach types to parameters, returns, and variables | [-> catalog/01](../catalog/T13-null-safety.md) |
| Union / Literal | Express "one of" constraints and fixed value sets | [-> catalog/02](../catalog/T02-union-intersection.md) |
| TypedDict | Give structure to dictionaries with known keys | [-> catalog/03](../catalog/T31-record-types.md) |
| NewType | Create distinct types over the same underlying representation | [-> catalog/04](../catalog/T03-newtypes-opaque.md) |
| Enums | Named, closed sets of domain values | [-> catalog/05](../catalog/T01-algebraic-data-types.md) |
| Dataclasses | Structured domain entities with typed fields | [-> catalog/06](../catalog/T06-derivation.md) |
| Annotated | Attach validation metadata consumed by runtime libraries | [-> catalog/15](../catalog/T26-refinement-types.md) |

## Patterns

### A — NewType for primitive wrappers

Prevent accidental interchange of values that share the same runtime type.

```python
from typing import NewType

Email = NewType("Email", str)
Username = NewType("Username", str)

def send_welcome(to: Email, name: Username) -> None: ...

e = Email("alice@example.com")
u = Username("alice")

send_welcome(e, u)       # OK
send_welcome(u, e)       # error: incompatible types
send_welcome("raw", u)   # error: expected "Email", got "str"
```

### B — Dataclass for entities

Group related fields into a typed record with automatic `__init__`, `__eq__`, and `__repr__`.

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Invoice:
    invoice_id: int
    customer: str
    amount_cents: int
    issued_at: datetime

inv = Invoice(
    invoice_id=1,
    customer="Acme",
    amount_cents=9999,
    issued_at=datetime.now(),
)
inv.amount_cents = "free"  # error: Incompatible types (got "str", expected "int")
```

### C — TypedDict for external data

Type dictionaries that arrive from JSON APIs or config files without converting to classes.

```python
from typing import TypedDict

class APIResponse(TypedDict):
    status: int
    message: str
    data: list[str]

def handle(resp: APIResponse) -> str:
    return resp["message"]                   # OK
    # return resp["nonexistent"]             # error: TypedDict has no key "nonexistent"

bad: APIResponse = {"status": 200}           # error: missing keys "message" and "data"
```

### D — Annotated + Pydantic for validated models

Combine static types with runtime validation metadata.

```python
from typing import Annotated
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    price: Annotated[float, Field(gt=0)]
    sku: Annotated[str, Field(pattern=r"^[A-Z]{3}-\d{4}$")]

p = Product(name="Widget", price=9.99, sku="WDG-0001")  # OK at runtime
# Product(name="", price=-1, sku="bad")                  # ValidationError at runtime
```

### Untyped Python comparison

Without domain types, nothing prevents mixing semantically distinct values.

```python
# No types — everything is just str/int
def send_welcome(to, name):
    print(f"Hello {name}, sending to {to}")

send_welcome("alice", "alice@example.com")  # swapped — bug undetected
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **NewType** | Zero runtime cost; pure checker-level distinction | No methods or validation; just a type alias with identity |
| **Dataclass** | Full entity with fields, equality, repr; immutable via `frozen` | Heavier than a NewType for single-value wrappers |
| **TypedDict** | Natural fit for JSON/dict-shaped data; no class conversion needed | No methods; no inheritance in the OOP sense; keys are strings |
| **Annotated + Pydantic** | Combines static and runtime validation in one declaration | Runtime dependency on Pydantic; metadata ignored by plain mypy |

## When to use which feature

- **NewType** for lightweight domain primitives that wrap a single built-in type (IDs, emails, currency codes).
- **Dataclass** for domain entities with multiple fields and behavior (users, invoices, events).
- **TypedDict** for dictionary-shaped data from external sources (API responses, config files, database rows).
- **Annotated + Pydantic** when you need both static type safety and runtime validation with constraints that go beyond what the type system can express (ranges, regex patterns).

## When to Use It

Use domain modeling when you have business rules that should be enforced by the type system:

- **Entity lifecycles**: An order has different valid fields in `pending` vs `shipped` state
- **Unique domain values**: A `Temperature` shouldn't be accidentally compared to a `Pressure`, even if both are `int`
- **Invariant enforcement**: A `Rectangle` with width and height should never have negative dimensions

```python
# ✅ Good: shape reflects domain rules
from typing import Union

class Outgoing(BaseModel):
    kind: Literal["outgoing"]
    amount: Money
    recipient: AccountId

class Incoming(BaseModel):
    kind: Literal["incoming"]
    amount: Money
    sender: AccountId
    verified: Literal[True]

class Pending(BaseModel):
    kind: Literal["pending"]
    amount: Money
    expires_at: datetime

Transaction = Union[Outgoing, Incoming, Pending]
# outgoing can't have `sender`, pending always expires
```

Use it when the cost of confused types exceeds the boilerplate of domain wrappers. In a financial domain, paying `£100` to the wrong account because `user_id` was swapped with `account_id` is catastrophic — NewType prevents this.

## When Not to Use It

Skip domain modeling when:

- **Pass-through data**: You receive JSON and immediately forward it without interpreting its meaning
- **Simple configurations**: A flag like `{"dark_mode": True}` has no domain invariants to enforce
- **Prototypes/exploratory code**: Rapid iteration with mutable, untyped shapes
- **Interfacing external SDKs**: A library's opaque `Response` type shouldn't be re-modeled

```python
# ❌ Don't brand this — just a configuration bag
@dataclass
class AppConfig:
    api_key: str
    timeout_ms: int
    debug: bool

# ✅ But brand this — it's a domain concept
ApiKey = NewType("ApiKey", str)  # must never be logged raw, must be validated
```

If you find yourself creating a NewType but never preventing values that violate the semantic meaning, you're solving a problem you don't have.

## Antipatterns When Using It

### Antipattern 1 — Over-wrapping

Wrapping every string field destroys readability without value.

```python
from typing import NewType

# ❌ Over-wrapping
FirstName = NewType("FirstName", str)
LastName = NewType("LastName", str)
Address = NewType("Address", str)
Phone = NewType("Phone", str)

@dataclass
class User:
    first: FirstName
    last: LastName

def greet(u: User) -> str:
    return f"Hello {u.last}, {u.first}"  # swapped — no semantic error!

# ✅ Wrap only where confusion causes bugs
UserId = NewType("UserId", str)
TeamId = NewType("TeamId", str)  # both are IDs, easy to confuse
User = str  # no confusion risk
```

### Antipattern 2 — Empty variants

A union where every variant has identical fields defeats the purpose.

```python
from typing import Union, Literal

# ❌ Useless variants
Status = Literal["idle", "loading", "ready", "error"]

@dataclass
class Widget:
    status: Status
    value: str

# same shape — no discrimination benefit

# ✅ Discriminant drives shape
@dataclass
class WidgetIdle:
    status: Literal["idle"]

@dataclass
class WidgetLoading:
    status: Literal["loading"]
    progress: int

@dataclass
class WidgetReady:
    status: Literal["ready"]
    value: str

@dataclass
class WidgetError:
    status: Literal["error"]
    message: str

Widget = Union[WidgetIdle, WidgetLoading, WidgetReady, WidgetError]
```

### Antipattern 3 — Mutable domain objects

Domain shapes should be immutable once constructed.

```python
from dataclasses import dataclass

# ❌ Mutable domain object
@dataclass
class Order:
    id: int
    amount: int
    status: str

def process_order(o: Order) -> None:
    o.amount = 0  # silently corrupted domain state
    o.status = "Cancelled"

# ✅ Immutable with transformation
@dataclass(frozen=True)
class Order:
    id: int
    amount: int
    status: str

def cancel_order(o: Order) -> Order:
    return Order(id=o.id, amount=o.amount, status="Cancelled")  # new instance
```

### Antipattern 4 — Runtime validation gaps

Using Pydantic at the boundary but accepting raw types internally.

```python
from pydantic import BaseModel

class OrderSchema(BaseModel):
    amount: int

# ❌ Validation gap
def process(req_body: dict) -> None:
    validated = OrderSchema.model_validate(req_body)  # validated
    # but then...
    def update_amount(order: OrderSchema, amount: int) -> OrderSchema:  # raw int!
        return OrderSchema(amount=amount)  # domain invariant broken

# ✅ Consistent wrapping throughout    
Money = NewType("Money", int)

class OrderSchema(BaseModel):
    amount: Money

def update_amount(order: OrderSchema, amount: Money) -> OrderSchema:
    return OrderSchema(amount=amount)
```

## Antipatterns with Other Techniques (Where Domain Modeling Helps)

### Antipattern 1 — `Any` for unknown shapes

```python
from typing import Any

# ❌ Without domain modeling
def process_item(item: Any) -> int:
    return item["price"] * item["quantity"]  # runtime errors possible

# ✅ With domain modeling
@dataclass
class Item:
    price: int
    quantity: int

def process_item(item: Item) -> int:
    return item.price * item.quantity  # type-checked
```

### Antipattern 2 — Partial types for optionality

```python
# ❌ Optional fields lead to runtime None checks
@dataclass
class User:
    id: str
    name: str | None = None
    email: str | None = None

def send_invite(u: User) -> None:
    if not u.email:  # scattered runtime guards
        return
    send_email(u.email, ...)

# ✅ Discriminated union replaces optional runtime checks
from typing import Union

@dataclass
class AnonymousUser:
    id: str
    status: Literal["anonymous"]

@dataclass
class RegisteredUser:
    id: str
    status: Literal["registered"]
    name: str
    email: str

User = Union[AnonymousUser, RegisteredUser]

def send_invite(u: RegisteredUser) -> None:
    send_email(u.email, ...)  # email guaranteed to exist
```

### Antipattern 3 — Magic strings for states

```python
# ❌ Magic strings
@dataclass
class Order:
    state: str

def is_shipped(o: Order) -> bool:
    return o.state in ("shipped", "SHIPPED", "shipped!")

# ✅ Literal types
from typing import Literal

@dataclass
class Order:
    state: Literal["pending", "shipped", "cancelled"]

def is_shipped(o: Order) -> bool:
    return o.state == "shipped"  # exhaustive and type-safe
```

### Antipattern 4 — Validation in business logic

```python
@dataclass
class Order:
    items: list[dict[str, int]]  # price: int inside each

# ❌ Validation scattered in business logic
def calculate_tax(order: Order) -> int:
    total = 0
    for item in order.items:
        if item["price"] < 0:  # validation leak
            raise ValueError("negative price")
        total += item["price"] * 0.1
    return total

# ✅ Domain types enforce invariants at construction
@dataclass
class Item:
    price: int  # smart constructor rejects negatives

@dataclass
class Order:
    items: list[Item]

def calculate_tax(order: Order) -> int:
    return sum(item.price * 0.1 for item in order.items)  # no guards needed
```

## Source anchors

- [PEP 484 — NewType](https://peps.python.org/pep-0484/#newtype-helper-function)
- [PEP 557 — Data Classes](https://peps.python.org/pep-0557/)
- [PEP 589 — TypedDict](https://peps.python.org/pep-0589/)
- [PEP 593 — Annotated](https://peps.python.org/pep-0593/)
- [Pydantic documentation](https://docs.pydantic.dev/)
- [mypy — TypedDict](https://mypy.readthedocs.io/en/stable/typed_dict.html)
