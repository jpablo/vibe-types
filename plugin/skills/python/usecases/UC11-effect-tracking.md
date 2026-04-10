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

## When to use it

Use effect tracking when:

- The caller must explicitly handle failures (parsing, validation, network calls).
- You want error paths visible in function signatures for tooling and readability.
- Resources require guaranteed cleanup (files, sockets, locks, DB connections).
- Multiple concurrent operations can fail and you want to report all errors.
- You're building a library API where silent failures would be surprising.

### Example: API client returns `Result` so callers cannot ignore errors

```python
from dataclasses import dataclass
from typing import TypedDict

@dataclass
class HttpError:
    status: int
    message: str

type HttpResponse[T] = T | HttpError

def get_user(url: str) -> HttpResponse[dict[str, str]]:
    # In real code: make HTTP request
    return {"id": "1", "name": "Alice"}

def process_user(url: str) -> None:
    resp = get_user(url)
    match resp:
        case {"id": id_, "name": name}:
            print(f"User {id_}: {name}")
        case HttpError(status=status):
            log(f"Failed with {status}")
```

## When not to use it

Avoid effect tracking when:

- Performance-critical hot paths (boxing/unboxing adds overhead).
- You're wrapping third-party code that already raises exceptions uniformly.
- The "error" case is actually a valid control flow (e.g., cache miss).
- Interfacing with codebases that expect plain exceptions (adds friction).
- Quick scripts or one-offs where boilerplate outweighs benefits.

### Example: Don't wrap cache misses as errors

```python
from typing import Any

# ❌ Wrong: cache miss is normal, not an error
def get_cached(key: str) -> Result[str, str]:
    val = cache.get(key)
    return Ok(val) if val else Err("cache miss")

# ✅ Right: use Optional for absence
def get_cached(key: str) -> str | None:
    return cache.get(key)
```

## Antipatterns when using it

### 1. Nesting results instead of flattening

```python
@dataclass
class OuterErr: pass

@dataclass
class InnerErr: pass

def fetch() -> Result[Result[int, InnerErr], OuterErr]:
    ...

# ❌ Deeply nested — caller must match twice
result = fetch()
match result:
    case Ok(inner):
        match inner:
            case Ok(value): ...
            case InnerErr(e): ...
    case OuterErr(e): ...

# ✅ Flatten early
def fetch() -> Result[int, OuterErr | InnerErr]:
    ...
```

### 2. Swallowing errors with `if isinstance(...)`

```python
def run() -> None:
    r = parse_input()
    if isinstance(r, Ok):
        process(r.value)
    # ❌ Error silently ignored — defeats the purpose

# ✅ Force explicit handling
match parse_input():
    case Ok(v): process(v)
    case Err(e): handle_error(e)
```

### 3. Creating new error wrapper functions

```python
def my_try(fn: Callable[[], T]) -> Result[T, Exception]:
    try:
        return Ok(fn())
    except Exception as e:
        return Err(e)

# ❌ Adds boilerplate without gaining anything

# ✅ Just use try/except inline or let exceptions propagate
```

### 4. Using `Result` for flow control

```python
def next_page(current: int) -> Result[int, str]:
    if current >= MAX_PAGES:
        return Err("no more pages")
    return Ok(current + 1)

# ❌ "no more pages" is not an error — it's a condition

# ✅ Return `None` or use a dedicated type
def next_page(current: int) -> int | None:
    return current + 1 if current < MAX_PAGES else None
```

## Antipatterns in other techniques that effect tracking fixes

### 1. "Bare" returns with implicit failure

```python
# ❌ TypeScript/Python without effect tracking
def loadConfig(path: str) -> dict:
    return json.load(open(path))  # May raise FileNotFoundError!

# ✅ With effect tracking — failure is explicit
def loadConfig(path: str) -> Result[dict, FileNotFoundError]:
    try:
        return Ok(json.load(open(path)))
    except FileNotFoundError as e:
        return Err(e)
```

### 2. Return code conventions

```python
# ❌ C-style return codes — easy to ignore
def divide(a: float, b: float, out: list[float]) -> int:
    if b == 0:
        return -1  # ← caller often forgets to check
    out.append(a / b)
    return 0

# ✅ Effect tracking enforces handling
def divide(a: float, b: float) -> Result[float, ZeroDivisionError]:
    if b == 0:
        return Err(ZeroDivisionError("divide by zero"))
    return Ok(a / b)
```

### 3. Global state / mutable flags

```python
# ❌ Error state in global
parse_error: str | None = None

def parse(s: str) -> int:
    global parse_error
    try:
        return int(s)
    except ValueError as e:
        parse_error = str(e)
        return 0  # ← caller must check global state

# ✅ Error is local and required
def parse(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError as e:
        return Err(str(e))
```

### 4. Exceptions thrown across API boundaries

```python
# ❌ API throws — forces try/except everywhere
class UserClient:
    def get(self, id: int) -> dict:
        resp = http_get(f"/users/{id}")
        if resp.status == 404:
            raise NotFoundError(id)  # ← propagates as exception
        return resp.json()

# ✅ Error is part of the type
class UserClient:
    def get(self, id: int) -> Result[dict, NotFoundError]:
        resp = http_get(f"/users/{id}")
        if resp.status == 404:
            return Err(NotFoundError(id))
        return Ok(resp.json())
```

## Source anchors

- [PEP 654 — Exception Groups and except*](https://peps.python.org/pep-0654/)
- [contextlib — Context manager utilities](https://docs.python.org/3/library/contextlib.html)
- [PEP 604 — Union syntax `X | Y`](https://peps.python.org/pep-0604/)
- [typing spec: Never and NoReturn](https://typing.readthedocs.io/en/latest/spec/special-types.html#never-and-noreturn)
- [returns library — Typed monadic result types](https://returns.readthedocs.io/)
