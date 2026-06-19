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
    print(result)
    # result = fetch_data("https://example.com")       # error: missing await; type is Coroutine, not str
```

### B — Awaitable and Coroutine type annotations

Use `collections.abc.Awaitable` and `collections.abc.Coroutine` for typing async parameters.

```python
from collections.abc import Awaitable, Coroutine

async def run_task(task: Awaitable[int]) -> int:
    return await task

async def run_coro(task: Coroutine[None, None, int]) -> int:
    return await task

async def producer() -> int:
    return 42

async def main() -> None:
    result = await run_task(producer())  # OK — Coroutine[Any, Any, int] is Awaitable[int]
    result2 = await run_coro(producer())  # OK — explicit Coroutine annotation
    print(result, result2)
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
    print(result)
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

## When to use it

Use type-annotated async when:

- Your function performs I/O — network requests, database queries, file operations.
- You need to coordinate multiple concurrent operations without blocking the event loop.
- Callers need to know whether to `await` the result.

## Antipatterns

### A — Forgetting to await coroutines

Creating a coroutine without awaiting or scheduling it silently drops work.

```python
# expect-error
async def send_email(user: str) -> None:
    pass

# ❌ Antipattern: coroutine created but never run
async def notify(user: str) -> None:
    await send_email(user)

async def process_order(order_id: str) -> None:
    notify("alice@example.com")
    # coroutine object is created then discarded

# ✅ Fix: await or schedule
async def process_order_fixed(order_id: str) -> None:
    await notify("alice@example.com")  # or asyncio.create_task(notify(...))
```

### B — Awaiting in loops instead of batching

Sequential awaits in a loop negate the benefit of async I/O.

```python
import asyncio

async def fetch_url(url: str) -> str:
    await asyncio.sleep(0.1)
    return url

# ❌ Antipattern: sequential awaits
async def fetch_all_slow(urls: list[str]) -> list[str]:
    results: list[str] = []
    for url in urls:
        results.append(await fetch_url(url))
    return results

# ✅ Fix: gather
async def fetch_all_fast(urls: list[str]) -> list[str]:
    tasks = [fetch_url(u) for u in urls]
    return await asyncio.gather(*tasks)
```

### C — Sync blocking in async context

Using blocking calls in async functions stalls the event loop.

❌ Antipattern: blocking call in async

```python
import asyncio

async def load_file(path: str) -> bytes:
    await asyncio.sleep(0)  # useless await
    with open(path) as f:
        return f.read().encode()  # blocks event loop!
```

✅ Fix: async file I/O

```python
import aiofiles

async def load_file(path: str) -> bytes:
    async with aiofiles.open(path, "rb") as f:
        return await f.read()
```

### D — Overusing Callable type erasure

Loose `Callable` types lose async guarantees: a plain `Callable[[], str]`
silently accepts an async function, whose real return type is a coroutine.

```python
# expect-error
from collections.abc import Callable, Awaitable
from typing import TypeVar

T = TypeVar("T")

# ❌ Antipattern: a sync Callable signature accepts an async function
def run_hook(hook: Callable[[], str]) -> str:
    return hook()

async def my_async_hook() -> str:
    return "done"

result = run_hook(my_async_hook)  # error: async fn returns Coroutine[Any, Any, str], not str

# ✅ Fix: separate sync/async hooks
def run_sync_hook(hook: Callable[[], T]) -> T:
    return hook()

async def run_async_hook(hook: Callable[[], Awaitable[T]]) -> T:
    return await hook()
```

## Anti-usecases

### A — Wrapping CPU-bound work in async

```python
import asyncio

# Bad: CPU work doesn't benefit from async
async def sum_squares_async(n: int) -> int:
    await asyncio.sleep(0)  # pointless async for CPU work
    return sum(i*i for i in range(n))

# Good: plain function
def sum_squares(n: int) -> int:
    return sum(i*i for i in range(n))
```

### B — Callback hell instead of async/await

Callbacks obscure types and error handling.

❌ Antipattern: nested callbacks

```python ignore
def fetch_user(id: int, callback: Callable[[str], None]) -> None:
    loop = asyncio.get_event_loop()
    async def inner():
        data = await fetch_user_api(id)
        callback(data)
    loop.create_task(inner())

fetch_user(123, lambda name: fetch_orders(name, lambda orders: print(orders)))
```

✅ Better: async/await with clear types

```python ignore
async def fetch_user(id: int) -> str:
    return await fetch_user_api(id)

async def fetch_orders(name: str) -> list[Order]:
    return await fetch_orders_api(name)

async def main() -> None:
    name = await fetch_user(123)
    orders = await fetch_orders(name)
    print(orders)
```

### C — Synchronous retry loops instead of async retry

Blocking retry blocks the event loop for all tasks.

❌ Antipattern: sync blocking retry

```python ignore
def fetch_with_retry(url: str) -> str:
    for attempt in range(3):
        try:
            time.sleep(2**attempt)  # blocks everything!
            return http.get(url)
        except TimeoutError:
            continue
    raise RuntimeError("failed")
```

✅ Better: async retry

```python ignore
async def fetch_with_retry(url: str) -> str:
    for attempt in range(3):
        try:
            await asyncio.sleep(2**attempt)  # non-blocking
            return await http_get(url)
        except TimeoutError:
            continue
    raise RuntimeError("failed")
```

## Source anchors

- [PEP 484 — Coroutines and awaitables](https://peps.python.org/pep-0484/#coroutines-and-awaitables)
- [PEP 525 — Asynchronous generators](https://peps.python.org/pep-0525/)
- [typing module — Awaitable, Coroutine, AsyncIterator](https://docs.python.org/3/library/typing.html#typing.Awaitable)
- [mypy — Async/await](https://mypy.readthedocs.io/en/stable/more_types.html#async-and-await)
