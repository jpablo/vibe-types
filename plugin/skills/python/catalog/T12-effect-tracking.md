# Effect Tracking (via Result Patterns and Context Managers)

> **Since:** `with` statement and `contextlib` Python 2.5 (PEP 343); `contextlib.ContextDecorator` Python 3.2; `ExceptionGroup` Python 3.11 (PEP 654); `|` union syntax Python 3.10 (PEP 604) | **Backport:** `exceptiongroup` (PyPI)

## What it is

Python has no formal effect system — there is no way to declare in a function's type signature that it performs I/O, raises exceptions, or mutates shared state. However, several patterns approximate effect tracking at the type level. **Result patterns** encode success/failure as explicit return types (`T | ErrorType`) instead of raising exceptions, making the error path visible to the type checker. **Context managers** (`with` blocks via `contextlib`) make resource acquisition and release explicit in the control flow. **Exception groups** (PEP 654) allow bundling multiple exceptions into a single `ExceptionGroup`, enabling structured concurrency patterns where several tasks can fail simultaneously.

The type checker tracks return types faithfully — if a function returns `Result[User, ValidationError]`, callers must handle both variants — but it cannot track *which* exceptions a function might raise, since Python has no `throws` clause.

## What constraint it enforces

**Return-type unions force callers to narrow the result before using the success value. Context managers ensure resource cleanup is syntactically scoped. The type checker enforces the return-type contract but does not track raised exceptions.**

## Minimal snippet

```python
from dataclasses import dataclass

@dataclass
class Ok[T]:
    value: T

@dataclass
class Err[E]:
    error: E

type Result[T, E] = Ok[T] | Err[E]

def parse_age(raw: str) -> Result[int, str]:
    if raw.isdigit() and 0 < int(raw) < 150:
        return Ok(int(raw))
    return Err(f"Invalid age: {raw!r}")

match parse_age("25"):
    case Ok(value):
        print(f"Age is {value}")
    case Err(error):
        print(f"Failed: {error}")
    # Type checker knows both branches are covered
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Enums / Union types** [-> T01](T01-algebraic-data-types.md) | Error variants can be modeled as enum members or union discriminants, giving exhaustiveness checking on the error path. |
| **Callable types** [-> T22](T22-callable-typing.md) | Error callbacks typed as `Callable[[Exception], None]` make error-handling strategies explicit in function signatures. |
| **Type narrowing** [-> T14](T14-type-narrowing.md) | `isinstance` or `match`/`case` narrows `Ok[T] | Err[E]` to the specific variant, unlocking access to `.value` or `.error`. |
| **Generics** [-> T04](T04-generics-bounds.md) | `Result[T, E]` is generic in both the success and error type, composing with generic pipelines. |
| **Never / bottom** [-> T34](T34-never-bottom.md) | A function that always raises can return `Never`, signaling to the checker that subsequent code is unreachable. |

## Gotchas and limitations

1. **No `throws` clause.** Python's type system cannot express which exceptions a function may raise. The only way to make errors visible to the checker is to return them as values. Libraries like `returns` provide monadic `Result` types, but they are not part of the standard library.

2. **Context managers do not encode their effect in the type.** `contextlib.contextmanager` produces a `ContextManager[T]`, which describes the yielded value but not the side effect (file I/O, lock acquisition, etc.). The type checker ensures correct usage of the `with` block but not the nature of the effect.

3. **`ExceptionGroup` complicates `except` clauses.** With `except*` (PEP 654), multiple handlers can fire for the same `ExceptionGroup`. This is powerful for structured concurrency but surprising for developers used to single-exception handling.

4. **Result patterns add boilerplate.** Without language-level support (no `?` operator like Rust), every call site needs explicit `match` or `isinstance` checks. Helper combinators (`map`, `and_then`) can reduce this, but they are not built in.

5. **`asyncio` effects are not tracked.** Whether a function is async is part of its type (`Coroutine[...]`), but other effects (database access, network I/O) are invisible to the type checker.

## Beginner mental model

Think of **return-type unions** as a doctor handing you an envelope: it either contains good news (`Ok`) or bad news (`Err`), and you must open it and check before acting. **Context managers** are like a hotel key card — you swipe in (`with`), do your business, and the door locks behind you automatically. Python's type checker acts as a receptionist who verifies you opened the envelope, but cannot tell you whether the doctor visited a lab or just guessed.

## Example A — Result type with exhaustive matching

```python
from dataclasses import dataclass
from enum import Enum

class ParseError(Enum):
    EMPTY = "empty"
    OVERFLOW = "overflow"
    INVALID = "invalid"

@dataclass
class Ok[T]:
    value: T

@dataclass
class Err[E]:
    error: E

type Result[T, E] = Ok[T] | Err[E]

def parse_port(raw: str) -> Result[int, ParseError]:
    if not raw:
        return Err(ParseError.EMPTY)
    if not raw.isdigit():
        return Err(ParseError.INVALID)
    port = int(raw)
    if port > 65535:
        return Err(ParseError.OVERFLOW)
    return Ok(port)

def describe(error: ParseError) -> str:
    # Declared return type str + enum match: the checker proves exhaustiveness —
    # remove a case and it reports the missing branch
    match error:
        case ParseError.EMPTY:
            return "Port is required"
        case ParseError.OVERFLOW:
            return "Port out of range"
        case ParseError.INVALID:
            return "Port must be numeric"

def connect(raw_port: str) -> None:
    match parse_port(raw_port):
        case Ok(port):
            print(f"Connecting to port {port}")
        case Err(error):
            print(describe(error))
```

## Example B — ExceptionGroup for concurrent errors

```python
import asyncio

async def fetch(url: str) -> str:
    if "bad" in url:
        raise ValueError(f"Bad URL: {url}")
    return f"<html from {url}>"

async def fetch_all(urls: list[str]) -> list[str]:
    results: list[str] = []
    errors: list[Exception] = []
    for url in urls:
        try:
            results.append(await fetch(url))
        except Exception as exc:
            errors.append(exc)
    if errors:
        raise ExceptionGroup("fetch failures", errors)
    return results

async def main() -> None:
    try:
        await fetch_all(["https://good.com", "https://bad.com"])
    except* ValueError as eg:
        for exc in eg.exceptions:
            print(f"Caught: {exc}")
    except* OSError as eg:
        for exc in eg.exceptions:
            print(f"Network error: {exc}")

asyncio.run(main())
```

## Use-case cross-references

- [-> UC08](../usecases/UC08-error-handling.md) — Result-type patterns for making error paths explicit and checkable.
- [-> UC01](../usecases/UC01-invalid-states.md) — Union return types prevent callers from ignoring failure states.
- [-> UC02](../usecases/UC02-domain-modeling.md) — Domain errors modeled as enum variants within Result types.

## Recommended libraries

| Library | Description |
|---|---|
| [returns](https://pypi.org/project/returns/) | Result monad for Python — `Result[T, E]`, `Maybe`, `IO` containers with Railway-oriented programming and mypy plugin |
| [result](https://pypi.org/project/result/) | Lightweight `Result[T, E]` type inspired by Rust — `Ok`, `Err` with `map`, `and_then`, `unwrap` combinators |

## When to use it

- **Operations that can fail predictably**: Parsing, validation, configuration loading.

  ```python
  from dataclasses import dataclass
  from enum import Enum

  @dataclass
  class Ok[T]:
      value: T

  @dataclass
  class Err[E]:
      error: E

  type Result[T, E] = Ok[T] | Err[E]

  class ParseError(Enum):
      INVALID = "invalid"

  def parse_int(s: str) -> Result[int, ParseError]:
      try:
          return Ok(int(s))
      except ValueError:
          return Err(ParseError.INVALID)
  ```

- **Functions with multiple failure modes**: When you need typed errors that propagate through a pipeline.

  ```python
  from dataclasses import dataclass

  @dataclass
  class Ok[T]:
      value: T

  @dataclass
  class Err[E]:
      error: E

  type Result[T, E] = Ok[T] | Err[E]

  @dataclass
  class UserData:
      name: str

  @dataclass
  class APIError:
      status: int

  @dataclass
  class NotFound:
      user_id: int

  def fetch_user_data(user_id: int) -> Result[UserData, APIError | NotFound]: ...
  ```

- **Resource management with guaranteed cleanup**: Files, locks, database connections.

  ```python
  def process(data: str) -> None:
      pass

  def process_file(path: str) -> None:
      with open(path) as f:        # closed even if process() raises
          data = f.read()
          process(data)
  ```

- **Chaining operations where failure should short-circuit**: Pipelines of computations.

  ```python
  from dataclasses import dataclass

  @dataclass
  class Ok[T]:
      value: T

  @dataclass
  class Err[E]:
      error: E

  type Result[T, E] = Ok[T] | Err[E]

  def parse_number(raw: str) -> Result[int, str]:
      return Ok(int(raw)) if raw.isdigit() else Err(f"not a number: {raw!r}")

  def validate_range(n: int) -> Result[int, str]:
      return Ok(n) if 0 < n < 100 else Err(f"out of range: {n}")

  def pipeline(raw: str) -> Result[int, str]:
      match parse_number(raw):
          case Ok(n):
              return validate_range(n)
          case Err(e):
              return Err(e)  # failure short-circuits
  ```

## When NOT to use it

- **Simple pure computations**: Basic calculations with no failure path.

  ```python
  def add(a: int, b: int) -> int:
      return a + b
  ```

- **Truly exceptional conditions**: Programmer errors, missing invariants.

  ```python
  def get_first[T](items: list[T]) -> T:
      if not items:
          raise RuntimeError("Expected non-empty list")
      return items[0]
  ```

- **Simple boolean-return functions**: Over-engineering success/failure as union types.

  ```python
  from dataclasses import dataclass
  from typing import Never

  @dataclass
  class Ok[T]:
      value: T

  @dataclass
  class Err[E]:
      error: E

  type Result[T, E] = Ok[T] | Err[E]

  # Not this:
  def is_valid_wrapped(s: str) -> Result[bool, Never]:
      return Ok(bool(s))

  # Just this:
  def is_valid(s: str) -> bool:
      return bool(s)
  ```

## Antipatterns when using it

### 1. **Wrapping operations that cannot fail**

```python
from dataclasses import dataclass
from typing import Never

@dataclass
class Ok[T]:
    value: T

@dataclass
class Err[E]:
    error: E

type Result[T, E] = Ok[T] | Err[E]

# ❌ Unnecessary wrapping
def square_wrapped(n: int) -> Result[int, Never]:
    return Ok(n * n)

# ✅ Keep it simple
def square(n: int) -> int:
    return n * n
```

### 2. **Nesting Results instead of flattening errors**

```python
from dataclasses import dataclass

@dataclass
class Ok[T]:
    value: T

@dataclass
class Err[E]:
    error: E

type Result[T, E] = Ok[T] | Err[E]

@dataclass
class Config:
    path: str

class ParseError(Exception): ...

# ❌ Result[Result[T, E1], E2] forces two layers of matching
def load_config_nested(path: str) -> Result[Result[Config, ParseError], OSError]: ...

# ✅ Flatten to a union of errors
def load_config(path: str) -> Result[Config, OSError | ParseError]: ...
```

### 3. **Ignoring the error branch**

```python
from dataclasses import dataclass

@dataclass
class Ok[T]:
    value: T

@dataclass
class Err[E]:
    error: E

type Result[T, E] = Ok[T] | Err[E]

def parse_number(raw: str) -> Result[int, str]:
    return Ok(int(raw)) if raw.isdigit() else Err(f"not a number: {raw!r}")

# ❌ Silently swallowing errors
result = parse_number("abc")
if isinstance(result, Ok):
    print(result.value)

# ✅ Handle both paths explicitly
match parse_number("abc"):
    case Ok(value):
        print(value)
    case Err(error):
        print(f"failed: {error}")
```

### 4. **Mixing exceptions and Result in one API**

```python
from dataclasses import dataclass
from enum import Enum

@dataclass
class Ok[T]:
    value: T

@dataclass
class Err[E]:
    error: E

type Result[T, E] = Ok[T] | Err[E]

class ParseError(Enum):
    EMPTY = "empty"
    INVALID = "invalid"

# ❌ Inconsistent: claims to return Result but can still raise
def process(data: str) -> Result[int, str]:
    return Ok(int(data))  # int() may raise ValueError!

# ✅ Consistent: every failure becomes an Err
def process_ok(data: str) -> Result[int, ParseError]:
    if not data:
        return Err(ParseError.EMPTY)
    if not data.isdigit():
        return Err(ParseError.INVALID)
    return Ok(int(data))
```

### 5. **Creating Result but always succeeding**

```python
from dataclasses import dataclass
from enum import Enum

@dataclass
class Ok[T]:
    value: T

@dataclass
class Err[E]:
    error: E

type Result[T, E] = Ok[T] | Err[E]

class DivisionError(Enum):
    ZERO_DIVISOR = "zero divisor"

# ❌ Pointless wrapper — claims it can fail but never returns Err
def divide_dishonest(a: int, b: int) -> Result[float, DivisionError]:
    return Ok(a / b)  # b could be 0 — raises at runtime!

# ✅ Handle the error case
def divide(a: int, b: int) -> Result[float, DivisionError]:
    if b == 0:
        return Err(DivisionError.ZERO_DIVISOR)
    return Ok(a / b)
```

## Antipatterns where effect tracking fixes them

### 1. **Exception everywhere instead of typed failures**

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str

# ❌ Without effect tracking: every step may raise, and nothing
# in the signatures says so
def get_user(username: str) -> User:
    raise KeyError(username)

def calculate_score(user: User) -> int:
    raise ValueError("bad data")

def process_user(username: str) -> int:
    user = get_user(username)      # may raise — invisible to the checker
    return calculate_score(user)   # may raise — invisible to the checker
```

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str

@dataclass
class Ok[T]:
    value: T

@dataclass
class Err[E]:
    error: E

type Result[T, E] = Ok[T] | Err[E]

# Error variants as dataclasses — they can carry context
@dataclass
class UserNotFound:
    username: str

@dataclass
class CalculationFailed:
    reason: str

type UserError = UserNotFound | CalculationFailed

def get_user(username: str) -> Result[User, UserNotFound]:
    if username == "admin":
        return Ok(User(username))
    return Err(UserNotFound(username))

def calculate_score(user: User) -> Result[int, CalculationFailed]:
    if user.name:
        return Ok(len(user.name))
    return Err(CalculationFailed("empty name"))

# ✅ With effect tracking: every failure is explicit in the types,
# and the checker verifies that all paths return a Result
def process_user(username: str) -> Result[int, UserError]:
    match get_user(username):
        case Err(e):
            return Err(e)
        case Ok(user):
            match calculate_score(user):
                case Ok(score):
                    return Ok(score)
                case Err(e):
                    return Err(e)
```

### 2. **Optional/None cascade instead of typed errors**

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str

# ❌ Without effect tracking: None pollution — the reason for
# failure is lost at every step
def find_user(name: str) -> User | None: ...
def get_role(user: User) -> str | None: ...

# Need nested None checks
user = find_user("Bob")
if user is not None:
    role = get_role(user)
    if role is not None:
        print(role)
```

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str

@dataclass
class NotFound:
    name: str

@dataclass
class Unauthorized:
    reason: str

@dataclass
class Ok[T]:
    value: T

@dataclass
class Err[E]:
    error: E

type Result[T, E] = Ok[T] | Err[E]

# ✅ With effect tracking: each failure carries its reason
def find_user(name: str) -> Result[User, NotFound]: ...
def get_role(user: User) -> Result[str, Unauthorized]: ...

match find_user("Bob"):
    case Ok(user):
        match get_role(user):
            case Ok(role):
                print(role)
            case Err(e):
                print(f"unauthorized: {e.reason}")
    case Err(e):
        print(f"not found: {e.name}")
```

### 3. **Silent callbacks hiding errors**

```python
import json
from collections.abc import Callable

def http_get(url: str) -> str:
    return '{"ok": true}'

# ❌ Without effect tracking: errors eaten inside the callback machinery
def fetch_json(url: str, callback: Callable[[dict[str, object]], None]) -> None:
    try:
        data: dict[str, object] = json.loads(http_get(url))
        callback(data)
    except Exception:
        pass  # error swallowed

fetch_json("/api", print)  # if it fails, nobody knows
```

```python
import asyncio
import json
from dataclasses import dataclass

@dataclass
class Ok[T]:
    value: T

@dataclass
class Err[E]:
    error: E

type Result[T, E] = Ok[T] | Err[E]

@dataclass
class RequestError:
    cause: Exception

async def http_get(url: str) -> str:
    return '{"ok": true}'

# ✅ With effect tracking: the failure is part of the return type
async def fetch_json(url: str) -> Result[dict[str, object], RequestError]:
    try:
        text = await http_get(url)
        data: dict[str, object] = json.loads(text)
        return Ok(data)
    except Exception as e:
        return Err(RequestError(e))

# Caller must handle both outcomes
async def main() -> None:
    match await fetch_json("/api"):
        case Ok(data):
            print(data)
        case Err(e):
            print(f"request failed: {e.cause}")

asyncio.run(main())
```

### 4. **Mixed failure signals instead of typed results**

```python
import os
from dataclasses import dataclass
from enum import Enum

@dataclass
class Ok[T]:
    value: T

@dataclass
class Err[E]:
    error: E

type Result[T, E] = Ok[T] | Err[E]

# ❌ Mixed signals: None means "missing or failed", 0 means "empty" —
# callers cannot tell the cases apart
def process_file(path: str) -> int | None:
    if not os.path.exists(path):
        return None  # missing file -> None
    try:
        with open(path) as f:
            data = f.read()
    except OSError:
        return None  # any I/O error -> also None!
    if not data:
        return 0  # empty file -> 0
    return len(data)

# ✅ Consistent pattern: typed Result
class FileInfoError(Enum):
    NOT_FOUND = "not found"
    EMPTY = "empty"
    IO_ERROR = "io error"

def process_file_ok(path: str) -> Result[int, FileInfoError]:
    if not os.path.exists(path):
        return Err(FileInfoError.NOT_FOUND)
    try:
        with open(path) as f:
            data = f.read()
    except OSError:
        return Err(FileInfoError.IO_ERROR)
    if not data:
        return Err(FileInfoError.EMPTY)
    return Ok(len(data))

# Error handling at the boundary
match process_file_ok("/tmp/data.txt"):
    case Ok(size):
        print(f"Size: {size}")
    case Err(FileInfoError.NOT_FOUND):
        print("creating missing file")
    case Err(FileInfoError.EMPTY):
        print("warning: empty file ignored")
    case Err(_):
        print("alerting admin")  # I/O errors and anything else
```

## Source anchors

- [PEP 654 — Exception Groups and except*](https://peps.python.org/pep-0654/)
- [PEP 604 — Allow writing union types as X | Y](https://peps.python.org/pep-0604/)
- [contextlib — Utilities for with-statement contexts](https://docs.python.org/3/library/contextlib.html)
- [returns library — Typed functional result types](https://returns.readthedocs.io/)
- [mypy — Union types and narrowing](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#union-types)
