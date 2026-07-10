# Serialization Safety

## The constraint

Values crossing a serialization boundary should be converted from untrusted `object`/JSON shapes into typed domain values once, at the edge. After that parse step, core code should accept the parsed type rather than repeating key checks, casts, or ad-hoc validation.

Python's type checker cannot prove that `json.loads()` returned a particular schema by itself: the standard library returns `Any`. The type-safety pattern is to pair runtime parsing with a static type that records the successful parse — `TypedDict` for wire dictionaries, frozen dataclasses for domain values, `Literal` discriminants for variants, and `Annotated`/`dataclass_transform`-aware libraries when the runtime schema lives in a framework.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| **TypedDict / ReadOnly / Required / NotRequired** | Describe JSON-like object keys, optionality, and read-only fields at the wire boundary | [-> T31](../catalog/T31-record-types.md) |
| **Dataclasses and `dataclass_transform`** | Convert parsed wire data into typed domain models; let third-party model libraries expose dataclass-like typing | [-> T06](../catalog/T06-derivation.md) |
| **Literal / tagged unions** | Preserve serialized variant tags and make branch handling checkable | [-> T52](../catalog/T52-literal-types.md) |
| **Annotated metadata** | Keep validation constraints attached to the type for runtime libraries while the checker sees the base type | [-> T26](../catalog/T26-refinement-types.md) |
| **NewType / branded parsed values** | Mark identifiers or parsed payloads so raw strings/dicts cannot be passed as already-validated data | [-> T03](../catalog/T03-newtypes-opaque.md) |
| **Type narrowing** | Narrow `object` or `dict[str, object]` after runtime checks before constructing typed values | [-> T14](../catalog/T14-type-narrowing.md) |

## Patterns

### A — Parse `json.loads()` into a TypedDict at the boundary

`json.loads()` is deliberately dynamic. Do the runtime checks once, then return a precise type that downstream code can rely on.

```python
# expect-error
import json
from typing import TypedDict, cast

class UserWire(TypedDict):
    id: int
    email: str
    active: bool

def parse_user_wire(raw: str) -> UserWire:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("expected object")
    if not isinstance(data.get("id"), int):
        raise ValueError("id must be int")
    if not isinstance(data.get("email"), str):
        raise ValueError("email must be str")
    if not isinstance(data.get("active"), bool):
        raise ValueError("active must be bool")
    return cast(UserWire, data)

def send_welcome(user: UserWire) -> str:
    return user["email"].upper()

raw: object = json.loads('{"id": 1, "email": "a@example.com", "active": true}')
send_welcome(raw)  # error: object is not assignable to UserWire
send_welcome(parse_user_wire('{"id": 1, "email": "a@example.com", "active": true}'))  # OK
```

### B — Convert wire shapes into frozen domain dataclasses

Keep JSON-compatible types at the boundary and richer domain types inside the core.

```python
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict

class EventWire(TypedDict):
    kind: str
    occurred_at: str
    amount_cents: int

@dataclass(frozen=True)
class Event:
    kind: str
    occurred_at: datetime
    amount_cents: int

def parse_event(wire: EventWire) -> Event:
    return Event(
        kind=wire["kind"],
        occurred_at=datetime.fromisoformat(wire["occurred_at"]),
        amount_cents=wire["amount_cents"],
    )

def handle(event: Event) -> int:
    return event.amount_cents
```

### C — Preserve serialized variants with Literal discriminants

Tagged `TypedDict` unions let the checker narrow each serialized variant from its tag.

```python
# expect-error
from typing import Literal, TypedDict, assert_never

class Click(TypedDict):
    kind: Literal["click"]
    x: int
    y: int

class Keypress(TypedDict):
    kind: Literal["keypress"]
    key: str

WireEvent = Click | Keypress

def describe(event: WireEvent) -> str:
    match event["kind"]:
        case "click":
            return f"click at {event['x']}, {event['y']}"
        case "keypress":
            return f"key {event['key']}"
        case other:
            assert_never(other)

bad: Click = {"kind": "keypress", "x": 1, "y": 2}  # error: Literal mismatch
```

### D — Let schema libraries expose dataclass-like typing

Libraries such as Pydantic use runtime validation, but their constructors and fields can still be type checked when they expose dataclass-like semantics. PEP 681 (`dataclass_transform`) is the typing hook that lets model libraries tell checkers how generated `__init__` methods and fields behave.

```text
from pydantic import BaseModel

class UserModel(BaseModel):
    id: int
    email: str

user = UserModel(id=1, email="a@example.com")  # OK
bad = UserModel(id="not-int", email="a@example.com")  # checker error with Pydantic typing support
print(user.model_dump())
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| `TypedDict` wire type | Best match for JSON objects; precise keys and optionality | No runtime validation by itself; still a `dict` at runtime |
| Frozen dataclass domain type | Stronger domain model with methods, immutability, and constructor typing | Needs explicit conversion from wire data |
| `Literal` tagged union | Checkable variant dispatch for serialized events/messages | Requires a stable discriminator field in the wire format |
| Pydantic/msgspec/dataclass-like schemas | One runtime parser can produce typed model instances | Dependency-specific behavior; checker support depends on library typing quality |
| `NewType` parsed marker | Prevents raw IDs/strings from flowing into parsed-only APIs | Zero runtime validation; parser must be the only constructor by convention |

## When to use which feature

- Use **`TypedDict`** for raw JSON-shaped dictionaries you still want to pass around after parsing.
- Use **dataclasses or model classes** when core code needs domain behavior, immutability, or non-JSON field types such as `datetime`.
- Use **`Literal` discriminants** for event streams, messages, webhooks, and tagged payloads where the tag determines the payload shape.
- Use **`Annotated`** when a runtime library consumes validation metadata but the static checker should still see the underlying Python type.
- Use **`NewType`** for parsed IDs such as `UserId`, `OrderId`, or `AccessToken` after format validation has succeeded.

## Antipatterns

### A — Letting `Any` from JSON leak inward

```python
# expect-error
import json

def total(raw: str) -> int:
    data = json.loads(raw)      # Any
    return data["count"] + 1    # unchecked: misspelled key or str value can slip through

count: str = total('{"count": 1}')  # error only here; the boundary stayed too loose
```

### B — Duplicating wire and domain shapes without a conversion function

If `UserWire` and `User` have separate definitions, make the conversion explicit and tested. Otherwise the two shapes drift silently: a field gets added to one and forgotten in the other.

### C — Treating `cast()` as validation

`cast(UserWire, data)` only tells the checker to trust you. It does not inspect `data`. Pair it with real runtime checks or use a schema library that performs them.

## Source anchors

- [Python docs — `json` encoder and decoder](https://docs.python.org/3/library/json.html)
- [Python docs — `typing.TypedDict`](https://docs.python.org/3/library/typing.html#typing.TypedDict)
- [PEP 589 — TypedDict](https://peps.python.org/pep-0589/)
- [PEP 655 — Required / NotRequired](https://peps.python.org/pep-0655/)
- [PEP 705 — ReadOnly TypedDict items](https://peps.python.org/pep-0705/)
- [PEP 681 — Data Class Transforms](https://peps.python.org/pep-0681/)
- [Pydantic docs — Serialization](https://docs.pydantic.dev/latest/concepts/serialization/)
- [mypy docs — TypedDict](https://mypy.readthedocs.io/en/stable/typed_dict.html)
