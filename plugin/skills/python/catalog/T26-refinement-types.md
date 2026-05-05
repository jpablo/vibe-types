# Annotated and Type Metadata

> **Since:** Python 3.9 (PEP 593) | **Backport:** `typing_extensions` (Python 3.7+)

## What it is

`Annotated[T, metadata1, metadata2, ...]` wraps a base type `T` with arbitrary metadata objects that static type checkers see as `T` but runtime tools (Pydantic, beartype, attrs, FastAPI) can inspect via `typing.get_type_hints(include_extras=True)`. This creates a clean separation: the static checker enforces the type `T`, while runtime validators enforce the metadata constraints. It is the standard mechanism for embedding domain rules — value ranges, string patterns, custom validators — directly in type annotations without inventing new types.

## What constraint it enforces

**The static type checker treats `Annotated[T, ...]` exactly as `T`, enforcing all normal type constraints. The metadata is invisible to the checker but available at runtime for frameworks that perform additional validation. This means `Annotated` does not add static constraints — it adds a standardized channel for runtime constraints that coexist with static types.**

## Minimal snippet

```python
from typing import Annotated

type PositiveInt = Annotated[int, "must be > 0"]

def square(n: PositiveInt) -> int:
    return n * n

square(5)       # OK — int is compatible with Annotated[int, ...]
square("hi")    # error — str is not compatible with int
square(-3)      # OK to the static checker (it ignores the metadata)
                # but a runtime validator would reject this
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Basic annotations** [-> catalog/01](T13-null-safety.md) | `Annotated` wraps any base type. `Annotated[int \| None, ...]` works as expected — the checker sees `int \| None`. |
| **TypedDict** [-> catalog/03](T31-record-types.md) | TypedDict values can be `Annotated` to attach per-field metadata: `class User(TypedDict): age: Annotated[int, Gt(0)]`. |
| **Dataclasses** [-> catalog/06](T06-derivation.md) | Dataclass fields with `Annotated` types let runtime validators (Pydantic dataclasses, beartype) enforce constraints on construction. |
| **Unpack / kwargs** [-> catalog/19](T46-kwargs-typing.md) | `Annotated` can appear inside `Unpack[TypedDict]` field types, attaching metadata to individual keyword arguments. |

## Gotchas and limitations

1. **The static checker ignores all metadata.** `Annotated[int, Gt(0)]` is just `int` to mypy and pyright. If you expect the checker to reject `square(-3)`, it will not. Runtime validation is a separate step.

2. **Metadata objects must be immutable or at least hashable in practice.** While Python does not enforce this, mutable metadata leads to subtle bugs when frameworks cache or compare annotations.

3. **Nesting `Annotated` flattens.** `Annotated[Annotated[int, A], B]` is equivalent to `Annotated[int, A, B]`. The metadata is merged, not nested.

4. **`get_type_hints()` strips metadata by default.** You must pass `include_extras=True` to preserve `Annotated` wrappers. This is a common source of bugs in custom framework code.

   ```python
   from typing import get_type_hints, Annotated

   class Cfg:
       x: Annotated[int, "meta"]

   get_type_hints(Cfg)                          # {'x': int}  — metadata lost
   get_type_hints(Cfg, include_extras=True)      # {'x': Annotated[int, 'meta']}
   ```

5. **Not all frameworks interpret metadata the same way.** Pydantic, beartype, and cattrs each have their own metadata protocols. There is no universal standard for what metadata objects mean — only a standard for where they live.

6. **`Annotated` requires at least one metadata argument.** `Annotated[int]` is invalid and will raise a `TypeError` at runtime.

## Beginner mental model

Think of `Annotated` as a **sticky note attached to a type**. The type checker reads the type and ignores the sticky note. Runtime validators read the sticky note and enforce whatever rules it describes. This lets you write `Annotated[int, Gt(0)]` and get two layers of safety: the checker ensures it is an `int`, and Pydantic (or beartype, etc.) ensures it is positive.

## Example A — Pydantic model with Annotated field constraints

```python
from typing import Annotated
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    price: Annotated[float, Field(gt=0, description="Price in USD")]
    quantity: Annotated[int, Field(ge=0, le=10_000)]

# Static checker sees: name: str, price: float, quantity: int
# Pydantic enforces: name length, price > 0, 0 <= quantity <= 10000

p = Product(name="Widget", price=9.99, quantity=50)   # OK

p = Product(name="", price=9.99, quantity=50)
# Runtime: ValidationError — name must have at least 1 character
# Static: no error (checker sees str, "" is a valid str)

p = Product(name="Widget", price=-1, quantity=50)
# Runtime: ValidationError — price must be > 0
# Static: no error (checker sees float, -1 is a valid float)

# Type aliases for reuse across models
type NonEmptyStr = Annotated[str, Field(min_length=1)]
type USD = Annotated[float, Field(gt=0)]
type BoundedCount = Annotated[int, Field(ge=0, le=10_000)]

class Order(BaseModel):
    customer: NonEmptyStr
    total: USD
    item_count: BoundedCount
```

FastAPI uses the same pattern for request validation:

```python
from typing import Annotated
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/items")
def list_items(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> list[dict[str, str]]:
    ...

# The static checker sees: skip: int, limit: int
# FastAPI enforces: skip >= 0, 1 <= limit <= 100
# OpenAPI docs are auto-generated from the metadata
```

## Example B — Custom validator metadata for domain rules

```python
from typing import Annotated, Any, get_type_hints
from dataclasses import dataclass

# Define custom metadata classes
@dataclass(frozen=True)
class Gt:
    value: float

@dataclass(frozen=True)
class MaxLen:
    value: int

@dataclass(frozen=True)
class Pattern:
    regex: str

# Use them in annotations
type Email = Annotated[str, Pattern(r"^[\w.+-]+@[\w-]+\.[\w.]+$"), MaxLen(254)]
type Age = Annotated[int, Gt(0)]
type Username = Annotated[str, MaxLen(32), Pattern(r"^[a-zA-Z0-9_]+$")]

@dataclass
class UserProfile:
    email: Email
    age: Age
    username: Username

# Static checker sees: email: str, age: int, username: str
# A custom runtime validator can inspect the metadata:

def validate_field(value: Any, annotation: Any) -> bool:
    """Minimal validator that reads Annotated metadata."""
    if not hasattr(annotation, "__metadata__"):
        return True
    for meta in annotation.__metadata__:
        if isinstance(meta, Gt) and not (value > meta.value):
            return False
        if isinstance(meta, MaxLen) and len(value) > meta.value:
            return False
    return True

hints = get_type_hints(UserProfile, include_extras=True)
# hints["age"] is Annotated[int, Gt(value=0)]

validate_field(25, hints["age"])     # True
validate_field(-1, hints["age"])     # False
validate_field("a" * 300, hints["email"])  # False
```

Combining with beartype for automatic runtime enforcement:

```python
from typing import Annotated
from beartype import beartype
from beartype.vale import Is

type Probability = Annotated[float, Is[lambda x: 0.0 <= x <= 1.0]]

@beartype
def log_odds(p: Probability) -> float:
    import math
    return math.log(p / (1 - p))

log_odds(0.8)    # OK at runtime
log_odds(1.5)    # beartype raises BeartypeCallHintParamViolation
# Static checker: no error in either case (it sees float)
```

## Common type-checker errors and how to read them

### No error when you expect one

The most common "error" with `Annotated` is the absence of a static error. Remember: the checker ignores metadata entirely. `Annotated[int, Gt(0)]` is just `int` to the checker. If you need static enforcement of value constraints, consider `Literal`, `NewType`, or an enum instead.

### `error: Argument 1 has incompatible type "str"; expected "int"`

This is a normal type error on the base type. `Annotated[int, ...]` is `int`, so passing a `str` is rejected. The metadata plays no role.

### `TypeError: Annotated needs at least two arguments` (runtime)

You wrote `Annotated[int]` without any metadata. Add at least one metadata argument: `Annotated[int, "some constraint"]`.

### `error: Type alias "X" is not valid as a type` (mypy, some versions)

Older mypy versions had limited support for `type` statement aliases involving `Annotated`. Use explicit `TypeAlias` or upgrade mypy.

### Metadata lost in `get_type_hints` output

You called `get_type_hints(cls)` without `include_extras=True`. The returned dict will show plain `int` instead of `Annotated[int, ...]`. Always pass `include_extras=True` when you need metadata.

## Use-case cross-references

- [-> UC-02](../usecases/UC02-domain-modeling.md) — API boundary validation where Annotated bridges static types and runtime enforcement.
- [-> UC-09](../usecases/UC09-builder-config.md) — Pydantic/FastAPI models that use Annotated for field constraints and OpenAPI schema generation.

## When to use

- **API boundaries** — validate untrusted input (HTTP requests, CLI args, config files) once at entry points, then pass validated values downstream
- **Domain primitives with invariants** — values like email addresses, ports, currency amounts, ISO codes that have specific validation rules
- **Public library APIs** — guarantee consumers cannot construct invalid state without going through your validated constructors
- **Configuration objects** — ensure config is validated before any runtime logic depends on it

```python
from typing import Annotated
from pydantic import BaseModel, Field

# ✅ Validate at API boundary, then use branded type
type Email = Annotated[str, Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")]

class User(BaseModel):
    email: Email  # validated by Pydantic at construction
```

## When not to use

- **High-frequency inner loops** — avoid runtime validation on hot paths; validate once upstream instead
- **Trusted internal values** — values constructed entirely within code that cannot produce invalid state
- **Transitory computed values** — temporary values where validation cost outweighs benefit
- **Simple structural types** — if a value has no predicate (just shape), use plain types or dataclasses

```python
# ❌ Don't validate in hot loops
def process_numbers(nums: list[Annotated[int, Field(ge=0)]]) -> int:
    total = 0
    for n in nums:
        total += n  # validation already happened, no need here
    return total

# ✅ Validate once upstream, then use plain int
def process_numbers(nums: list[int]) -> int:
    # assumes nums already validated at boundary
    return sum(nums)
```

## Antipatterns when using Annotated

### Re-validating already-validated values

`Annotated` metadata is for single validation at entry points, not repeated checks:

```python
from typing import Annotated
from pydantic import BaseModel, Field

type PositiveInt = Annotated[int, Field(gt=0)]

class Order(BaseModel):
    quantity: PositiveInt

# ❌ Double validation
def process_order(order: Order) -> None:
    if order.quantity <= 0:  # redundant — already validated by Pydantic
        raise ValueError
    # ...

# ✅ Trust the type — validation already happened
def process_order(order: Order) -> None:
    # order.quantity is guaranteed > 0
    total = order.quantity * 9.99
```

### Using metadata as a replacement for actual validation logic

Metadata alone does nothing — you need a runtime validator that interprets it:

```python
from typing import Annotated

type MustBePositive = Annotated[int, "must be > 0"]

def process(n: MustBePositive) -> int:
    return n * 2

process(-5)  # ❌ No error — nothing enforces "must be > 0"

# ✅ Use a validator that actually checks the metadata
from pydantic import BaseModel, Field

type PositiveInt = Annotated[int, Field(gt=0)]

class Config(BaseModel):
    value: PositiveInt

Config(value=-5)  # ValidationError at runtime
```

### Bypassing the validator with raw values casting

Don't manually construct values that should come from a validated source:

```python
from typing import Annotated
from pydantic import BaseModel, Field

type Email = Annotated[str, Field(pattern=r".+@.+")]

class User(BaseModel):
    email: Email

# ❌ Bypassing validation by directly assigning raw string
user_email = "invalid"  # type: ignore
user = User(email=user_email)  # validation skipped

# ✅ Let Pydantic validate at construction
user = User(email="valid@example.com")
```

### Over-using Annotated for semantic naming without constraints

Using `Annotated` purely for nominal typing wastes the runtime validation opportunity:

```python
from typing import Annotated

# ❌ Empty metadata serves no purpose
type UserId = Annotated[str, "user id"]
type OrderId = Annotated[str, "order id"]

# ✅ Use NewType for nominal typing at static level
from typing import NewType

UserId = NewType("UserId", str)
OrderId = NewType("OrderId", str)
```

## Antipatterns where Annotated + validation results in better code

### Repeated inline validation at every call site

Checking the same predicate everywhere instead of validating once at the boundary:

```python
import re

# ❌ Validation repeated at every use site
def send_email(to: str) -> None:
    if not re.match(r"[^\s@]+@[^\s@]+\.[^\s@]+$", to):
        raise ValueError(f"Invalid email: {to}")
    # send...

def add_recipient(email: str) -> None:
    if not re.match(r"[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        raise ValueError(f"Invalid email: {email}")
    # add...

def notify_admin(email: str) -> None:
    if not re.match(r"[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        raise ValueError(f"Invalid email: {email}")
    # notify...

# ✅ Single validation upstream, branded type downstream
from typing import Annotated
from pydantic import Field

type Email = Annotated[str, Field(pattern=r"[^\s@]+@[^\s@]+\.[^\s@]+$")]

def send_email(to: Email) -> None:
    # no validation needed — Email type guarantees validity
    # send...

def add_recipient(email: Email) -> None:
    # no validation needed
    # add...

# Validate once at boundary
from pydantic import BaseModel

class Request(BaseModel):
    email: Email

req = Request(email="user@example.com")  # validated once
send_email(req.email)  # req.email is Email, already validated
```

### Magic string constants without validation

Using raw string literals that could be typos or invalid:

```python
# ❌ Magic strings — no static or runtime safety
ADMIN_EMAIL = "admin@example.com"
SUPPORT_EMAIL = "support@exampl.com"  # typo, no one catches this

# ✅ Branded type with validation
from typing import Annotated
from pydantic import Field

type Email = Annotated[str, Field(pattern=r"[^\s@]+@[^\s@]+\.[^\s@]+$")]

ADMIN_EMAIL: Email = "admin@example.com"  # type: ignore  # still needs validation source
SUPPORT_EMAIL: Email = "support@example.com"  # type: ignore

# Better: use Pydantic model to validate constants
class Config(BaseModel):
    admin_email: Email
    support_email: Email

config = Config(
    admin_email="admin@example.com",
    support_email="support@example.com",
)  # both validated at once
```

### Partially validated unions with repeated checks

Having a union like `str | None` and checking validity at every call site:

```python
from typing import Optional

# ❌ Union type with validity check everywhere
type UserIdInput = Optional[str]

def delete_user(id: UserIdInput) -> None:
    if not id or not id.strip():
        raise ValueError("Invalid user ID")
    # ...

def archive_user(id: UserIdInput) -> None:
    if not id or not id.strip():
        raise ValueError("Invalid user ID")
    # ...

def transfer_user(id: UserIdInput) -> None:
    if not id or not id.strip():
        raise ValueError("Invalid user ID")
    # ...

# ✅ Single validation, then branded type
from typing import Annotated
from pydantic import BaseModel, Field

type UserId = Annotated[str, Field(min_length=1, regex=r"^\w+$")]

class UserInput(BaseModel):
    id: UserId

def delete_user(id: UserId) -> None:
    # id guaranteed valid
    # ...

def archive_user(id: UserId) -> None:
    # id guaranteed valid
    # ...

# Validate once
input_data = UserInput(id="user123")  # validated
delete_user(input_data.id)  # type-safe, no check
```

### Type guard predicates scattered throughout codebase

Checking the same predicate with type guards at every use site instead of having a single validated constructor:

```python
from typing import TypeGuard

# ❌ Type guard check at every location
def is_valid_port(n: int) -> TypeGuard[int]:
    return 1 <= n <= 65535

def connect(host: str, port: int) -> None:
    if not is_valid_port(port):
        raise ValueError("Invalid port")
    # connect...

def configure_server(port: int) -> None:
    if not is_valid_port(port):
        raise ValueError("Invalid port")
    # configure...

def validate_config(port: int) -> None:
    if not is_valid_port(port):
        raise ValueError("Invalid port")
    # validate...

# ✅ Single validation, branded type ensures safety downstream
from typing import Annotated
from pydantic import Field

type Port = Annotated[int, Field(ge=1, le=65535)]

class ServerConfig(BaseModel):
    host: str
    port: Port

def connect(host: str, port: Port) -> None:
    # port is guaranteed 1-65535
    # connect...

def configure_server(port: Port) -> None:
    # port is guaranteed valid
    # configure...

# Validate once at boundary
config = ServerConfig(host="localhost", port=8080)  # validated
connect(config.host, config.port)  # no checks needed
```

## Source anchors

- [PEP 593 — Flexible function and variable annotations](https://peps.python.org/pep-0593/) — `Annotated`
- [typing spec — Annotated](https://typing.readthedocs.io/en/latest/spec/qualifiers.html#annotated)
- [Python docs — typing.Annotated](https://docs.python.org/3/library/typing.html#typing.Annotated)
- [Pydantic docs — Field](https://docs.pydantic.dev/latest/concepts/fields/) — Pydantic's `Annotated` + `Field` pattern
- [beartype docs — beartype.vale.Is](https://beartype.readthedocs.io/en/latest/api_vale/) — beartype's `Annotated` validators
