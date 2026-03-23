# Concurrency (via asyncio Typing)

## The constraint

Asynchronous functions and coroutines must be annotated with the correct return types so the checker can verify that `await` is used on awaitables, coroutine return values are handled correctly, and sync/async boundaries are not accidentally crossed.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Effect tracking | `async def` marks a function as a coroutine; checker enforces `await` usage | [-> catalog/12](../catalog/T12-effect-tracking.md) |
| Generics / TypeVar | Parameterize async utilities over return types | [-> catalog/04](../catalog/T04-generics-bounds.md) |
| Callable typing | Type async callbacks and higher-order async functions | [-> catalog/11](../catalog/T22-callable-typing.md) |

## Patterns

### A — Basic async function annotation

Annotate async functions with their return type; the checker verifies `await` usage.

```python
import asyncio

async def fetch_data(url: str) -> str:
    await asyncio.sleep(0.1)  # simulate network
    return f"data from {url}"

async def main() -> None:
    result = await fetch_data("https://example.com")  # OK — str
    # result = fetch_data("https://example.com")       # error: missing await; type is Coroutine, not str
```

### B — Awaitable and Coroutine type annotations

Use `collections.abc.Awaitable` and `collections.abc.Coroutine` for typing async parameters.

```python
from collections.abc import Awaitable, Coroutine

async def run_task(task: Awaitable[int]) -> int:
    return await task

async def producer() -> int:
    return 42

async def main() -> None:
    result = await run_task(producer())  # OK — Coroutine[Any, Any, int] is Awaitable[int]
```

### C — Async callback typing

Type async callbacks using `Callable` that returns a coroutine.

```python
from collections.abc import Callable, Awaitable

async def retry(
    func: Callable[[], Awaitable[str]],
    attempts: int = 3,
) -> str:
    for i in range(attempts):
        try:
            return await func()
        except Exception:
            if i == attempts - 1:
                raise
    raise RuntimeError("unreachable")

async def fetch() -> str:
    return "data"

async def main() -> None:
    result = await retry(fetch)           # OK
    # await retry(lambda: "not async")    # error: str is not Awaitable[str]
```

### D — AsyncIterator and AsyncGenerator

Type async iteration with `AsyncIterator` and `AsyncGenerator`.

```python
from collections.abc import AsyncIterator

async def count_up(limit: int) -> AsyncIterator[int]:
    for i in range(limit):
        yield i

async def main() -> None:
    async for n in count_up(5):
        print(n)  # 0, 1, 2, 3, 4
```

### Untyped Python comparison

Without types, sync/async confusion surfaces as runtime errors.

```python
# No types
async def fetch():
    return "data"

def process():
    result = fetch()    # forgot await — result is a coroutine object, not "data"
    print(result.upper())  # AttributeError: 'coroutine' object has no attribute 'upper'
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| **async def + return type** | Checker enforces `await`; return type visible to callers | Must propagate `async` through entire call chain |
| **Awaitable[T] parameter** | Accepts any awaitable (coroutines, futures, tasks) | Less specific than a concrete async callable type |
| **Callable[..., Awaitable[T]]** | Types async callbacks precisely | Verbose; no built-in `AsyncCallable` shorthand |
| **AsyncIterator / AsyncGenerator** | Types async iteration fully | Requires async-for at the call site; cannot be used in sync contexts |

## When to use which feature

- **Annotate all async functions** with explicit return types — this is the single most impactful practice for async code.
- **Use `Awaitable[T]`** for parameters that accept any awaitable — coroutines, `asyncio.Task`, `asyncio.Future`.
- **Use `Callable[..., Awaitable[T]]`** for async callback parameters in retry, middleware, and scheduling utilities.
- **Use `AsyncIterator[T]`** when yielding values asynchronously — streaming responses, paginated APIs, event sources.

## Source anchors

- [PEP 484 — Coroutines and awaitables](https://peps.python.org/pep-0484/#coroutines-and-awaitables)
- [PEP 525 — Asynchronous generators](https://peps.python.org/pep-0525/)
- [typing module — Awaitable, Coroutine, AsyncIterator](https://docs.python.org/3/library/typing.html#typing.Awaitable)
- [mypy — Async/await](https://mypy.readthedocs.io/en/stable/more_types.html#async-and-await)
