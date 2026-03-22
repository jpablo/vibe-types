# Decorator Typing

## The constraint

Decorators must preserve or explicitly transform function signatures in a way
the type checker can see — so that decorated functions retain their parameter
types, return types, and overloads rather than collapsing to `Any`.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Generics in decorators | `TypeVar` binds the function type through the decorator | [-> catalog/07](../catalog/T04-generics-bounds.md) |
| `ParamSpec` / `TypeVarTuple` | Capture and forward full parameter signatures | [-> catalog/08](../catalog/T45-paramspec-variadic.md) |
| `Callable` / `@overload` | Annotate the decorator's own input/output function types | [-> catalog/11](../catalog/T22-callable-typing.md) |
| Generic classes / variance | Class-based decorators that preserve or transform types | [-> catalog/18](../catalog/T08-variance-subtyping.md) |

## Patterns

### Untyped comparison: decorator erasing type information

Without proper typing, a decorator collapses everything to `Any`.
The checker cannot verify callers or return values.

```python
# No type annotations — decorated function becomes (...) -> Any
def log_calls(func):
    def wrapper(*args, **kwargs):
        print(f"calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@log_calls
def add(a: int, b: int) -> int:
    return a + b

# Checker sees: add: (...) -> Any
add("x", "y")        # no error reported — type info lost
result: str = add(1, 2)  # no error reported — return type is Any
```

### A — Simple decorator with `ParamSpec`

`ParamSpec` preserves the full parameter list and return type through the
decorator, so the checker sees the original function signature.

```python
import functools
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

def retry(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        for attempt in range(3):
            try:
                return func(*args, **kwargs)
            except Exception:
                if attempt == 2:
                    raise
        raise RuntimeError("unreachable")
    return wrapper

@retry
def fetch(url: str, timeout: int = 30) -> str:
    return f"content of {url}"

fetch("https://example.com")              # OK
fetch("https://example.com", timeout=10)  # OK
fetch(123)                                # error: expected str, got int
result: int = fetch("url")               # error: str not assignable to int
```

### B — Decorator with arguments

When a decorator takes its own parameters, the outer function returns the
actual decorator. `ParamSpec` is used in the inner layer.

```python
import functools
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

def rate_limit(max_calls: int, period: float) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # rate-limiting logic here
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(max_calls=10, period=60.0)
def send_email(to: str, subject: str, body: str) -> bool:
    return True

send_email("a@b.com", "Hi", "Hello")         # OK — (str, str, str) -> bool preserved
send_email("a@b.com", "Hi")                   # error: missing argument "body"
send_email("a@b.com", "Hi", "Hello", cc=True) # error: unexpected keyword argument
```

### C — Class-based decorator

A class with `__call__` can act as a decorator. Generic type parameters
preserve the wrapped function's signature.

```python
import functools
from collections.abc import Callable
from typing import Generic, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

class CacheDecorator(Generic[P, R]):
    def __init__(self, func: Callable[P, R]) -> None:
        functools.update_wrapper(self, func)
        self._func = func
        self._cache: dict[str, R] = {}

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        key = str(args) + str(kwargs)
        if key not in self._cache:
            self._cache[key] = self._func(*args, **kwargs)
        return self._cache[key]

    def clear(self) -> None:
        self._cache.clear()

@CacheDecorator
def expensive(x: int, y: int) -> float:
    return (x ** y) * 0.1

expensive(2, 10)                  # OK — checker sees (int, int) -> float
expensive("a", "b")              # error: expected int
expensive.clear()                 # OK — extra method available on the class
```

### D — Decorator that transforms the return type

Some decorators intentionally change the return type (e.g., wrapping in a
container). Use `TypeVar` on the return to express the transformation.

```python
import functools
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import ParamSpec, TypeVar
from time import perf_counter

P = ParamSpec("P")
R = TypeVar("R")

@dataclass
class Timed(Generic[R]):
    value: R
    elapsed_ms: float

def timed(func: Callable[P, R]) -> Callable[P, Timed[R]]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Timed[R]:
        start = perf_counter()
        result = func(*args, **kwargs)
        elapsed = (perf_counter() - start) * 1000
        return Timed(value=result, elapsed_ms=elapsed)
    return wrapper

@timed
def compute(n: int) -> list[int]:
    return list(range(n))

out = compute(100)                # OK — Timed[list[int]]
out.value                         # OK — list[int]
out.elapsed_ms                    # OK — float
plain: list[int] = compute(100)  # error: Timed[list[int]] not assignable to list[int]
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| `ParamSpec` decorator | Full signature preservation; standard pattern | Requires 3.10+ or `typing_extensions` |
| Decorator with arguments | Configurable behavior with preserved types | Extra nesting; three layers of functions |
| Class-based decorator | Can hold state; extra methods on decorated function | More complex; some checkers handle class decorators less well |
| Return-type transform | Explicitly models what the decorator does to the type | Callers must adapt to the new return type |

## When to use which feature

**Use `ParamSpec` decorators** for logging, retry, auth, caching — any decorator
that wraps a function transparently without changing its signature.

**Use decorator-with-arguments** when the decorator needs configuration
(retry count, rate limit, feature flag). The outer function takes config,
the inner function takes and returns `Callable[P, R]`.

**Use class-based decorators** when the decorator needs persistent state
(caches, counters, metrics) or should expose extra methods beyond `__call__`.

**Use return-type transforms** when the decorator intentionally changes what
the function returns — timing wrappers, result wrappers, async adapters.

## Source anchors

- [PEP 612 — ParamSpec](https://peps.python.org/pep-0612/)
- [PEP 646 — TypeVarTuple](https://peps.python.org/pep-0646/)
- [PEP 484 — Callable](https://peps.python.org/pep-0484/#callable)
- [typing spec: ParamSpec](https://typing.readthedocs.io/en/latest/spec/generics.html#paramspec)
- [mypy docs: Decorators](https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators)
