# Effect Tracking (via Result Patterns and Context Managers)

> **Since:** `contextlib` Python 3.2; `ExceptionGroup` Python 3.11 (PEP 654); `|` union syntax Python 3.10 (PEP 604) | **Backport:** `exceptiongroup` (PyPI)

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
| **Enums / Union types** [-> catalog/T01](T01-algebraic-data-types.md) | Error variants can be modeled as enum members or union discriminants, giving exhaustiveness checking on the error path. |
| **Callable types** [-> catalog/T22](T22-callable-typing.md) | Error callbacks typed as `Callable[[Exception], None]` make error-handling strategies explicit in function signatures. |
| **Type narrowing** [-> catalog/T14](T14-type-narrowing.md) | `isinstance` or `match`/`case` narrows `Ok[T] | Err[E]` to the specific variant, unlocking access to `.value` or `.error`. |
| **Generics** [-> catalog/T04](T04-generics-bounds.md) | `Result[T, E]` is generic in both the success and error type, composing with generic pipelines. |
| **Never / bottom** [-> catalog/T34](T34-never-bottom.md) | A function that always raises can return `Never`, signaling to the checker that subsequent code is unreachable. |

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
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import assert_never

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

def connect(raw_port: str) -> None:
    result = parse_port(raw_port)
    match result:
        case Ok(port):
            print(f"Connecting to port {port}")
        case Err(ParseError.EMPTY):
            print("Port is required")
        case Err(ParseError.OVERFLOW):
            print("Port out of range")
        case Err(ParseError.INVALID):
            print("Port must be numeric")
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
        pages = await fetch_all(["https://good.com", "https://bad.com"])
    except* ValueError as eg:
        for exc in eg.exceptions:
            print(f"Caught: {exc}")
    except* OSError as eg:
        for exc in eg.exceptions:
            print(f"Network error: {exc}")

asyncio.run(main())
```

## Use-case cross-references

- [-> UC-08](../usecases/UC08-error-handling.md) — Result-type patterns for making error paths explicit and checkable.
- [-> UC-01](../usecases/UC01-invalid-states.md) — Union return types prevent callers from ignoring failure states.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Domain errors modeled as enum variants within Result types.

## Source anchors

- [PEP 654 — Exception Groups and except*](https://peps.python.org/pep-0654/)
- [PEP 604 — Allow writing union types as X | Y](https://peps.python.org/pep-0604/)
- [contextlib — Utilities for with-statement contexts](https://docs.python.org/3/library/contextlib.html)
- [returns library — Typed functional result types](https://returns.readthedocs.io/)
- [mypy — Union types and narrowing](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#union-types)
