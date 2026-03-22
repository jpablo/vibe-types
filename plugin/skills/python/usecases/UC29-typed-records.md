# Typed Dictionaries and Records

## The constraint

Dictionary-shaped data must have known keys with typed values so the checker
rejects unknown-key access, wrong-value-type assignment, and missing required
keys — catching at check time what would otherwise be `KeyError` or subtle
data corruption at runtime.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| `Literal` for key narrowing | Restrict dictionary keys to specific string values | [-> catalog/02](../catalog/T02-union-intersection.md) |
| `TypedDict` | Dict with per-key type annotations and required/optional control | [-> catalog/03](../catalog/T31-record-types.md) |
| `Annotated` on values | Carry validation metadata alongside value types | [-> catalog/15](../catalog/T26-refinement-types.md) |
| `Unpack` | Pass TypedDict shapes as typed `**kwargs` | [-> catalog/19](../catalog/T46-kwargs-typing.md) |

## Patterns

### A — `TypedDict` for API responses

Model JSON-shaped API responses so the checker knows exactly which keys exist
and what types their values have.

```python
from typing import TypedDict

class UserResponse(TypedDict):
    id: int
    username: str
    email: str
    is_active: bool

def display_user(user: UserResponse) -> str:
    return f"{user['username']} <{user['email']}>"      # OK

def bad_access(user: UserResponse) -> str:
    return user["phone"]                                 # error: key "phone" not in TypedDict

def wrong_type(user: UserResponse) -> None:
    user["is_active"] = "yes"                            # error: str not assignable to bool
```

### B — `TypedDict` inheritance for shared fields

Extract common fields into a base `TypedDict` and extend it.
This mirrors API versioning or shared response shapes.

```python
from typing import TypedDict, NotRequired

class BaseResponse(TypedDict):
    status: int
    message: str

class UserDetail(BaseResponse):
    user_id: int
    username: str
    avatar_url: NotRequired[str]

class ErrorDetail(BaseResponse):
    error_code: str
    retry_after: NotRequired[int]

def handle_user(resp: UserDetail) -> str:
    # Inherited fields are available and typed:
    if resp["status"] != 200:                            # OK — int
        return resp["message"]                           # OK — str
    return resp["username"]                              # OK — str

def bad_inherit(resp: UserDetail) -> str:
    return resp["error_code"]                            # error: key not in UserDetail
```

### C — `ReadOnly` TypedDict for immutable records

Python 3.13 (PEP 705) introduces `ReadOnly` for TypedDict fields, preventing
mutation after construction.

```python
from typing import ReadOnly, TypedDict

class FrozenConfig(TypedDict):
    version: ReadOnly[int]
    name: ReadOnly[str]
    debug: bool                      # mutable — can be toggled

cfg: FrozenConfig = {"version": 1, "name": "app", "debug": False}
cfg["debug"] = True                  # OK — not read-only
cfg["version"] = 2                   # error: "version" is read-only
cfg["name"] = "new"                  # error: "name" is read-only
```

### D — `Literal` key access patterns

Use `Literal` to type dictionary access helpers that return different types
depending on which key is requested.

```python
from typing import Literal, TypedDict, overload

class Settings(TypedDict):
    timeout: int
    verbose: bool
    name: str

@overload
def get_setting(s: Settings, key: Literal["timeout"]) -> int: ...
@overload
def get_setting(s: Settings, key: Literal["verbose"]) -> bool: ...
@overload
def get_setting(s: Settings, key: Literal["name"]) -> str: ...

def get_setting(s: Settings, key: str) -> int | bool | str:
    return s[key]                                  # type: ignore[literal-required]

settings: Settings = {"timeout": 30, "verbose": True, "name": "app"}

t: int = get_setting(settings, "timeout")          # OK
v: bool = get_setting(settings, "verbose")         # OK
x: int = get_setting(settings, "name")             # error: str not assignable to int
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| Plain `TypedDict` | Direct JSON mapping; checker validates keys and values | No methods; no default values; no runtime enforcement |
| Inherited `TypedDict` | Code reuse for shared fields; mirrors API shapes | Deep hierarchies become hard to track; no diamond resolution |
| `ReadOnly` fields | Immutability at the type level without `frozen` dataclass | Requires Python 3.13+ or `typing_extensions`; dict is still mutable at runtime |
| `Literal` key access | Per-key return type precision | Requires an `@overload` per key; boilerplate grows with key count |

## When to use which feature

**Use `TypedDict`** whenever you work with dict-shaped data from external
sources — JSON APIs, config files, database rows returned as dicts.

**Use inheritance** when multiple response types share a common shape
(status codes, pagination fields) and you want the checker to see the
shared fields in a base type.

**Use `ReadOnly`** when a TypedDict represents a configuration or snapshot
that should not be mutated after creation — config loaded from a file,
cached API responses, environment records.

**Use `Literal` key access** in generic getter/setter abstractions where the
return type should depend on which key is passed — settings managers,
feature flag systems, typed row accessors.

**Prefer dataclasses** over TypedDict when the data is constructed in Python,
needs methods, or benefits from frozen immutability. TypedDict shines for
data that arrives as a dictionary.

## Source anchors

- [PEP 589 — TypedDict](https://peps.python.org/pep-0589/)
- [PEP 655 — Required and NotRequired](https://peps.python.org/pep-0655/)
- [PEP 705 — ReadOnly for TypedDict](https://peps.python.org/pep-0705/)
- [PEP 586 — Literal types](https://peps.python.org/pep-0586/)
- [mypy docs: TypedDict](https://mypy.readthedocs.io/en/stable/typed_dict.html)
- [typing spec: TypedDict](https://typing.readthedocs.io/en/latest/spec/typeddict.html)
