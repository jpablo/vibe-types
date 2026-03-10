# Error Handling with Types

## The constraint

Error paths must be tracked in the type system so the checker verifies that
callers handle failure cases explicitly — rather than relying on try/except
conventions that are invisible to static analysis.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| `Optional` / `None` | Signal that a function may return "nothing" | [-> catalog/01](../catalog/01-basic-annotations-none.md) |
| `Union` result types | Encode success-or-error as `Union[Ok, Error]` | [-> catalog/02](../catalog/02-union-literal-types.md) |
| Enum error variants | Closed set of error codes with exhaustive matching | [-> catalog/05](../catalog/05-enums-typing.md) |
| `TypeGuard` / `TypeIs` | Narrow union results in conditional branches | [-> catalog/13](../catalog/13-typeguard-typeis-narrowing.md) |
| `NoReturn` / `Never` | Mark functions that always raise — checker prunes dead branches | [-> catalog/14](../catalog/14-never-noreturn.md) |

## Patterns

### Untyped Python comparison

Without type annotations, a forgotten `None` check causes a runtime crash
that the checker could have caught.

```python
# No type annotations — checker sees nothing wrong
def find_user(user_id):
    if user_id == "admin":
        return {"name": "Admin", "role": "admin"}
    return None

user = find_user("guest")
print(user["name"])          # RuntimeError: TypeError: 'NoneType' is not subscriptable
#                              Types would have caught this at check time.
```

### A — `Optional` return for nullable results

The simplest error encoding: the function returns `None` on failure.
The checker forces a `None` check before using the value.

```python
def find_user(user_id: str) -> dict[str, str] | None:
    if user_id == "admin":
        return {"name": "Admin", "role": "admin"}
    return None

user = find_user("guest")
print(user["name"])                   # error: "None" is not subscriptable

if user is not None:
    print(user["name"])               # OK — narrowed to dict[str, str]
```

### B — `Union[Success, Error]` result type

For richer error information, return a union of distinct dataclasses.
The checker requires narrowing before accessing type-specific attributes.

```python
from dataclasses import dataclass

@dataclass
class UserData:
    name: str
    email: str

@dataclass
class UserError:
    code: int
    message: str

def get_user(user_id: str) -> UserData | UserError:
    if user_id == "42":
        return UserData(name="Alice", email="alice@example.com")
    return UserError(code=404, message="not found")

result = get_user("99")

result.email                          # error: "UserError" has no attribute "email"

if isinstance(result, UserData):
    print(result.email)               # OK — narrowed to UserData
elif isinstance(result, UserError):
    print(f"Error {result.code}")     # OK — narrowed to UserError
```

### C — `NoReturn` for error-raising utilities

`NoReturn` (or `Never` in 3.12+) tells the checker a function never returns
normally, so code after the call is unreachable. This is useful for
centralized error-raising helpers.

```python
from typing import NoReturn

def fail(message: str) -> NoReturn:
    raise RuntimeError(message)

def process(data: str | None) -> str:
    if data is None:
        fail("data is required")
        # checker knows this is unreachable — no "missing return" error
    return data.upper()               # OK — narrowed to str
```

### D — Enum error codes with exhaustive handling

Use an `Enum` for a fixed set of error codes. Combined with a `match`
statement, the checker warns if any variant is unhandled.

```python
from enum import Enum
from typing import NoReturn, assert_never

class ErrorCode(Enum):
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    RATE_LIMITED = "rate_limited"

def handle_error(err: ErrorCode) -> str:
    match err:
        case ErrorCode.NOT_FOUND:
            return "Resource not found"
        case ErrorCode.UNAUTHORIZED:
            return "Access denied"
        case ErrorCode.RATE_LIMITED:
            return "Try again later"
        # If a new variant is added to ErrorCode without updating this match,
        # adding the following exhaustiveness guard makes it a type error:
        case _ as unreachable:
            assert_never(unreachable)     # error if any variant is unmatched
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| `Optional` return | Simple; idiomatic Python | No error detail — caller only knows "failed" |
| `Union[Ok, Err]` | Rich error info; checker enforces narrowing | Boilerplate; two classes per operation |
| `NoReturn` helpers | Centralizes raise logic; helps narrowing | Does not encode *which* errors can occur |
| Enum error codes | Exhaustive matching; closed set | Rigid; cannot carry per-variant data without extra wrapping |

## When to use which feature

**Use `Optional` return** for simple lookup functions where `None` is an obvious
"not found" — dictionary lookups, search functions, cache misses.

**Use `Union[Ok, Err]`** when the caller needs structured error information and
should handle success/failure explicitly — API clients, parsers, validation.

**Use `NoReturn`** for utility functions that always raise: `fail()`, `unreachable()`,
assertion helpers. The checker uses this to prune dead code paths.

**Use Enum error codes** when your domain has a fixed, small set of failure modes
and you want the checker to enforce that every mode is handled via
exhaustive `match`.

**Combine them**: a function returns `Union[UserData, UserError]` where `UserError`
contains an `ErrorCode` enum. Helper functions marked `NoReturn` handle fatal paths.

## Source anchors

- [PEP 484 — Optional type](https://peps.python.org/pep-0484/#union-types)
- [PEP 604 — Union syntax `X | Y`](https://peps.python.org/pep-0604/)
- [PEP 655 — NoReturn](https://peps.python.org/pep-0484/#the-noreturn-type)
- [typing spec: Never and NoReturn](https://typing.readthedocs.io/en/latest/spec/special-types.html#never-and-noreturn)
- [mypy docs: Union types](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#union-types)
- [Python docs: assert_never](https://docs.python.org/3/library/typing.html#typing.assert_never)
