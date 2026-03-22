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
- [-> UC-10](../usecases/UC29-typed-records.md) — Domain modeling where Annotated carries business rules alongside types.

## Source anchors

- [PEP 593 — Flexible function and variable annotations](https://peps.python.org/pep-0593/) — `Annotated`
- [typing spec — Annotated](https://typing.readthedocs.io/en/latest/spec/qualifiers.html#annotated)
- [Python docs — typing.Annotated](https://docs.python.org/3/library/typing.html#typing.Annotated)
- [Pydantic docs — Field](https://docs.pydantic.dev/latest/concepts/fields/) — Pydantic's `Annotated` + `Field` pattern
- [beartype docs — beartype.vale.Is](https://beartype.readthedocs.io/en/latest/api_vale/) — beartype's `Annotated` validators
