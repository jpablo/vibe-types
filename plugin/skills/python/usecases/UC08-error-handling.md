# Error Handling with Types

## The constraint

Error paths must be tracked in the type system so the checker verifies that
callers handle failure cases explicitly — rather than relying on try/except
conventions that are invisible to static analysis.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| `Optional` / `None` | Signal that a function may return "nothing" | [-> catalog/01](../catalog/T13-null-safety.md) |
| `Union` result types | Encode success-or-error as `Union[Ok, Error]` | [-> catalog/02](../catalog/T02-union-intersection.md) |
| Enum error variants | Closed set of error codes with exhaustive matching | [-> catalog/05](../catalog/T01-algebraic-data-types.md) |
| `TypeGuard` / `TypeIs` | Narrow union results in conditional branches | [-> catalog/13](../catalog/T14-type-narrowing.md) |
| `NoReturn` / `Never` | Mark functions that always raise — checker prunes dead branches | [-> catalog/14](../catalog/T34-never-bottom.md) |

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

## When to use it

Use typed error channels when:

- An operation can fail in multiple distinct ways (Pattern B: `Union[Ok, Err]`)
- The error carries diagnostic information needed for recovery or logging
- You need to prevent invalid data from reaching domain logic (Parse, don't validate)
- A pipeline has 3+ chained fallible operations where try/except nesting becomes unwieldy
- You need exhaustiveness checking across error variants

**Example: Multi-way failure with recovery**
```python
from dataclasses import dataclass

@dataclass
class NetworkError: pass
@dataclass
class AuthError: pass
@dataclass
class ParseError: pass

def fetch_user(token: str, url: str) -> UserData | NetworkError | AuthError | ParseError:
    # Each variant drives different recovery logic
    ...
```

**Example: Validated types at boundaries**
```python
class Age(int):
    """Validated age — cannot create with invalid values"""
    pass

def parse_age(raw: str) -> Age | ParseError:
    n = int(raw)
    if n < 0 or n > 150:
        return ParseError(f"invalid age: {raw}")
    return Age(n)
```

## When not to use it

Avoid typed error channels when:

- The operation is expected to never fail under normal operation
- Error details are irrelevant — callers only need success/failure flag
- Prototyping or throwaway code where type safety is not a priority
- Integrating with APIs that use exceptions as primary error mechanism
- Simple synchronous value transformations with no external dependencies

**Example: When raising is appropriate**
```python
import json
from pathlib import Path

def load_config() -> dict:
    raw = Path("config.json").read_text()
    return json.loads(raw)  # Let unexpected parse errors crash
```

**Example: Simple optional value**
```python
def get_first(items: list[str]) -> str | None:
    return items[0] if items else None
# Not a Result — just returning presence/absence
```

## Antipatterns when using it

### Antipattern A — Swallowing errors with empty branches

```python
result = parse_input(data)
if isinstance(result, Ok):
    use(result.value)
else:
    pass  # Silent failure — error is ignored
    # or:
    print("error")  # Lost in logs
# Prefer: handle each error variant specifically
```

### Antipattern B — Nested Results without flattening

```python
def load_and_process() -> Result[Result[Data, ParseError], IOError]:
    io = fetch_data()
    if io.is_error():
        return io
    return parse(io.value)  # Returns Result[Data, ParseError]
# Returns: Result[Result[Data, ParseError], IOError] — need two unwraps!
# Prefer: use chain() or flatMap pattern with Either-style result
```

### Antipattern C — Overly broad error types

```python
from dataclasses import dataclass

@dataclass
class Error:
    message: str  # No discriminant!

def handle(result: Data | Error) -> None:
    if isinstance(result, Error):
        # Cannot distinguish between error kinds
        print(result.message)
# Prefer: discriminated union with exhaustive variants
```

### Antipattern D — Re-raising to escape error handling

```python
def process(input: str) -> Data | Error:
    parsed = parse(input)
    if isinstance(parsed, Error):
        raise RuntimeError(parsed.message)
    return parsed
# Prefer: propagate error in Result, let caller decide to raise
```

## Antipatterns with other techniques (typed-error-fixes)

### Antipattern E — Boolean return with forgotten check

```python
# BAD: Caller must remember to check the flag
age: int = 0

def parse_age(raw: str) -> bool:
    global age
    n = int(raw)
    if 0 < n < 150:
        age = n
        return True
    return False

parse_age("200")  # returns False, but age is now 200!
use_age(age)      # Uses invalid age!

# FIX with Result:
def parse_age(raw: str) -> Age | ParseError:
    n = int(raw)
    if n <= 0 or n > 150:
        return ParseError(f"invalid age: {n}")
    return Age(n)

result = parse_age("200")
if isinstance(result, ParseError):
    handle_error(result)
else:
    use_age(result)  # result is type-safe Age
```

### Antipattern F — Getting attributes on potentially None

```python
# BAD: Multiple silent failures, hard to debug
user_id = user.profile.id if user and user.profile else 0
name = user.profile.name if user and user.profile else "Unknown"

# FIX with Result:
def extract_user(u: User) -> UserInfo | MissingFieldError:
    if not u.profile or not u.profile.id:
        return MissingFieldError("id")
    if not u.profile.name:
        return MissingFieldError("name")
    return UserInfo(id=u.profile.id, name=u.profile.name)
```

### Antipattern G — try/except with string matching on exceptions

```python
# BAD: Cannot tell which error occurred reliably
try:
    data = process(input)
except Exception as e:
    if "not found" in str(e):
        handle_not_found()
    elif "timeout" in str(e):
        handle_timeout()
# String matching is fragile; adding new error types risks missing them

# FIX with Result:
def process(input: str) -> Data | NotFoundError | TimeoutError:
    # Returns specific error variant
    ...

result = process(input)
match result:
    case NotFoundError():
        handle_not_found()
    case TimeoutError():
        handle_timeout()
    case _ as unreachable:
        assert_never(unreachable)  # Type error if new variant added
```

## Source anchors

- [PEP 484 — Optional type](https://peps.python.org/pep-0484/#union-types)
- [PEP 604 — Union syntax `X | Y`](https://peps.python.org/pep-0604/)
- [PEP 655 — NoReturn](https://peps.python.org/pep-0484/#the-noreturn-type)
- [typing spec: Never and NoReturn](https://typing.readthedocs.io/en/latest/spec/special-types.html#never-and-noreturn)
- [mypy docs: Union types](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#union-types)
- [Python docs: assert_never](https://docs.python.org/3/library/typing.html#typing.assert_never)
