# Async Iteration and Generators

> **Since:** `async`/`await` and async iteration protocol Python 3.5 (PEP 492); asynchronous generators Python 3.6 (PEP 525); `collections.abc.AsyncIterator`/`AsyncGenerator` generics are available for annotations in modern Python.

## What it is

Python's async iteration protocol models streams whose next value is produced asynchronously. An `AsyncIterable[T]` is any object that can produce an `AsyncIterator[T]`; an `AsyncIterator[T]` has `__anext__` returning an awaitable next item; an `AsyncGenerator[YieldType, SendType]` is produced by `async def` functions that use `yield`.

For typing work, the important point is that the element type travels with the stream. If a function returns `AsyncIterator[Row]`, every `async for row in ...` consumer sees `row` as `Row`; if a consumer expects `AsyncIterable[bytes]`, passing an async stream of `str` is a type error.

## What constraint it enforces

**Async streams carry a statically checked element type across producers, transformers, and consumers; the checker rejects yielding the wrong item type, consuming a stream as the wrong element type, or using a synchronous iterator where an async iterable is required.**

## Minimal snippet

```python
# expect-error
from collections.abc import AsyncIterator

async def count(limit: int) -> AsyncIterator[int]:
    for n in range(limit):
        yield n

async def render() -> None:
    async for n in count(3):
        text: str = n  # error: int is not assignable to str
        print(n + 1)   # OK — n is int
```

## Interaction with other features

| Feature | How it composes |
|---|---|
| **Effect tracking** [-> T12](T12-effect-tracking.md) | `async def` makes asynchrony visible in the return type; async iteration is the streaming form of that effect. |
| **Generics / TypeVar** [-> T04](T04-generics-bounds.md) | Generic stream utilities such as `collect[T](AsyncIterable[T]) -> list[T]` preserve the element type. |
| **Callable typing** [-> T22](T22-callable-typing.md) | Async stream transforms often accept typed async callbacks, e.g. `Callable[[T], Awaitable[U]]`. |
| **Recursive types** [-> T61](T61-recursive-types.md) | Async tree or graph walkers can stream recursively typed nodes without materializing the whole structure. |
| **Structural typing** [-> T07](T07-structural-typing.md) | Any object with the async iterator protocol can satisfy `AsyncIterable[T]`; inheritance is not required. |

## Gotchas and limitations

1. **Annotate async generators by yielded type, not coroutine type.** An `async def` that contains `yield` should usually be annotated as `AsyncIterator[T]` or `AsyncGenerator[T, SendT]`, not `Coroutine[..., T]`.

2. **`AsyncGenerator` has two parameters, not three.** In Python typing, `AsyncGenerator[YieldType, SendType]` omits a return type because asynchronous generators cannot return a value.

3. **Breaking early must still close resources.** Put cleanup in `finally` inside the generator, or wrap resource management in `async with`. The type checker tracks the element type, not resource lifetime.

4. **A single generator object is one-shot.** Re-iterate by calling the generator function again; do not try to reuse a consumed generator instance.

5. **`Iterable[T]` and `AsyncIterable[T]` are different protocols.** A normal `for` loop cannot consume `AsyncIterable[T]`, and `async for` expects async iteration support.

## Beginner mental model

Think of an `AsyncIterator[T]` as a conveyor belt where each item may take time to arrive. The type checker labels the belt with `T`; every producer must put only `T` items on it, and every consumer gets a `T` without guessing or casting.

## Example A — Paginated API stream

```python
from collections.abc import AsyncIterator
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    id: int
    name: str

@dataclass(frozen=True)
class Page:
    users: list[User]
    next_cursor: str | None

async def fetch_page(cursor: str | None) -> Page:
    # Network call omitted; the annotation says exactly what this boundary yields.
    return Page([User(1, "Ada")], None)

async def stream_users() -> AsyncIterator[User]:
    cursor: str | None = None
    while True:
        page = await fetch_page(cursor)
        for user in page.users:
            yield user
        if page.next_cursor is None:
            break
        cursor = page.next_cursor

async def collect_names() -> list[str]:
    names: list[str] = []
    async for user in stream_users():
        names.append(user.name)  # OK — user is User
    return names
```

## Example B — Generic async stream transform

```python
from collections.abc import AsyncIterable, AsyncIterator, Callable
from typing import TypeVar

T = TypeVar("T")
U = TypeVar("U")

async def amap(source: AsyncIterable[T], func: Callable[[T], U]) -> AsyncIterator[U]:
    async for item in source:
        yield func(item)

async def numbers() -> AsyncIterator[int]:
    yield 1
    yield 2

async def strings() -> list[str]:
    out: list[str] = []
    async for value in amap(numbers(), str):
        out.append(value)  # value is str
    return out
```

## Common type-checker errors and how to read them

### Yielding the wrong type

```text
# pyright
error: Return type of async generator function must be compatible with "AsyncIterator[int]"
```

**Cause:** The function annotation promises one yield type, but a `yield` expression produces another.
**Fix:** Correct the yielded value or the annotation.

### Passing the wrong stream element type

```text
# pyright
error: Argument of type "AsyncIterator[str]" cannot be assigned to parameter of type "AsyncIterable[bytes]"
```

**Cause:** Both values are async streams, but their element types do not match.
**Fix:** Transform the stream explicitly, or change the consumer's expected element type.

## Use-case cross-references

- [-> UC21](../usecases/UC21-concurrency.md) — Typed async functions and coroutine boundaries.
- [-> UC07](../usecases/UC07-callable-contracts.md) — Async callbacks used in stream transformers.
- [-> UC14](../usecases/UC14-extensibility.md) — Accepting any async stream implementation via protocol shape.

## Source anchors

- [Python docs — `typing.AsyncIterator`](https://docs.python.org/3/library/typing.html#typing.AsyncIterator)
- [Python docs — `typing.AsyncGenerator`](https://docs.python.org/3/library/typing.html#typing.AsyncGenerator)
- [Python docs — `collections.abc.AsyncIterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.AsyncIterator)
- [PEP 492 — Coroutines with async and await syntax](https://peps.python.org/pep-0492/)
- [PEP 525 — Asynchronous Generators](https://peps.python.org/pep-0525/)
