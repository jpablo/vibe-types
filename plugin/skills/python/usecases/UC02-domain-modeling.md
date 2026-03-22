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

## Source anchors

- [PEP 484 — NewType](https://peps.python.org/pep-0484/#newtype-helper-function)
- [PEP 557 — Data Classes](https://peps.python.org/pep-0557/)
- [PEP 589 — TypedDict](https://peps.python.org/pep-0589/)
- [PEP 593 — Annotated](https://peps.python.org/pep-0593/)
- [Pydantic documentation](https://docs.pydantic.dev/)
- [mypy — TypedDict](https://mypy.readthedocs.io/en/stable/typed_dict.html)
