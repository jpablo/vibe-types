# Effect Tracking

## The constraint

Side effects and error paths must be visible in function signatures so the
type checker can verify that callers handle failure cases explicitly, rather
than relying on invisible `raise`/`except` conventions.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| `T \| Error` return types | Encode success-or-failure as a union the checker enforces | [-> T12](../catalog/T12-effect-tracking.md) |
| `contextlib` | Scope resource effects into `with` blocks | [-> T12](../catalog/T12-effect-tracking.md) |
| `ExceptionGroup` / `except*` | Bundle multiple errors from concurrent tasks | [-> T12](../catalog/T12-effect-tracking.md) |
| `NoReturn` / `Never` | Mark functions that always raise; prune dead branches | [-> T34](../catalog/T34-never-bottom.md) |
| Type narrowing | Narrow union results with `isinstance` / `match` | [-> T14](../catalog/T14-type-narrowing.md) |

## Patterns

### A — Returning `T | Error` instead of raising

Make the error path part of the return type. The checker forces callers to
narrow before using the success value.

```python
from dataclasses import dataclass

@dataclass
class Ok[T]:
    value: T

@dataclass
class Err[E]:
    error: E

type Result[T, E] = Ok[T] | Err[E]

def parse_int(raw: str) -> Result[int, str]:
    if raw.strip().lstrip("-").isdigit():
        return Ok(int(raw))
    return Err(f"Not a number: {raw!r}")

result = parse_int("abc")
result.value              # error: "Err[str]" has no attribute "value"

match result:
    case Ok(v):
        print(v + 1)     # OK — narrowed to int
    case Err(e):
        print(e)          # OK — narrowed to str
```

### B — Context managers for scoped effects

`contextlib.contextmanager` makes resource setup/teardown explicit. The type
checker verifies the yielded type.

```python
from contextlib import contextmanager
from typing import Iterator

@contextmanager
def open_db(url: str) -> Iterator[dict[str, str]]:
    conn: dict[str, str] = {"status": "open", "url": url}
    try:
        yield conn
    finally:
        conn["status"] = "closed"

with open_db("postgres://localhost/db") as db:
    print(db["url"])     # OK — checker knows db is dict[str, str]
    db["query"] = "SELECT 1"
# db is closed here — cleanup is guaranteed by the context manager
```

### C — Exception groups for concurrent errors

`ExceptionGroup` (PEP 654) bundles multiple errors. `except*` handles
subgroups without losing the others.

```python
import asyncio

async def validate(field: str, value: str) -> str:
    if not value:
        raise ValueError(f"{field} is required")
    return value

async def validate_form(data: dict[str, str]) -> dict[str, str]:
    errors: list[ValueError] = []
    result: dict[str, str] = {}
    for field in ("name", "email"):
        try:
            result[field] = await validate(field, data.get(field, ""))
        except ValueError as e:
            errors.append(e)
    if errors:
        raise ExceptionGroup("validation failed", errors)
    return result

async def main() -> None:
    try:
        await validate_form({"name": "", "email": ""})
    except* ValueError as eg:
        for exc in eg.exceptions:
            print(f"Validation: {exc}")
```

### D — Combining `NoReturn` with result types

Use `NoReturn` for helpers that always raise, keeping the main function's
return type clean.

```python
from typing import NoReturn

def abort(msg: str) -> NoReturn:
    raise SystemExit(msg)

def load_config(path: str) -> dict[str, str]:
    if not path:
        abort("path is required")
        # checker knows this is unreachable — no "missing return" error
    return {"path": path}
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| **`T \| Error` return** | Errors visible in the type; checker enforces handling | Boilerplate at every call site; no `?` operator |
| **Context managers** | Resource cleanup is scoped and guaranteed | Effect *kind* (I/O, lock) is not in the type |
| **`ExceptionGroup`** | Handles multiple concurrent failures cleanly | Complex `except*` semantics; new in 3.11 |
| **`NoReturn`** | Prunes dead code paths; aids narrowing | Does not encode *which* errors can occur |

## When to use which feature

- **Use `T | Error` returns** when callers must explicitly handle failure — parsers, validators, API clients.
- **Use context managers** for resource lifecycle — database connections, file handles, locks.
- **Use `ExceptionGroup`** in structured concurrency where multiple tasks can fail simultaneously.
- **Use `NoReturn`** for assertion helpers and `fail()` functions that centralize raising.
- **Combine them**: a function returns `Result[T, E]`, uses a context manager for resources, and calls a `NoReturn` helper for fatal errors.

## Source anchors

- [PEP 654 — Exception Groups and except*](https://peps.python.org/pep-0654/)
- [contextlib — Context manager utilities](https://docs.python.org/3/library/contextlib.html)
- [PEP 604 — Union syntax `X | Y`](https://peps.python.org/pep-0604/)
- [typing spec: Never and NoReturn](https://typing.readthedocs.io/en/latest/spec/special-types.html#never-and-noreturn)
- [returns library — Typed monadic result types](https://returns.readthedocs.io/)
