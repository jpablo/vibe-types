# API Contracts and Callable Typing

## The constraint

Callback and decorator signatures must preserve parameter and return types across
higher-order boundaries so the checker can verify that callers pass correct
arguments and consumers use the correct return type — even when functions are
passed through other functions.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Generics (`TypeVar`) | Preserve a concrete type through a generic wrapper | [-> catalog/07](../catalog/T04-generics-bounds.md) |
| `ParamSpec` | Capture and forward an entire parameter signature | [-> catalog/08](../catalog/T45-paramspec-variadic.md) |
| Protocol `__call__` | Describe complex callable shapes structurally | [-> catalog/09](../catalog/T07-structural-typing.md) |
| `Callable` / `@overload` | Annotate simple callbacks and multi-signature APIs | [-> catalog/11](../catalog/T22-callable-typing.md) |
| `Self` | Return the same type from fluent/chained methods | [-> catalog/16](../catalog/T33-self-type.md) |

## Patterns

### A — `Callable` for simple callbacks

Use `Callable[[ArgTypes], ReturnType]` when the callback shape is straightforward.

```python
from collections.abc import Callable

def apply_twice(f: Callable[[int], int], x: int) -> int:
    return f(f(x))

apply_twice(lambda n: n + 1, 10)        # OK — returns 12
apply_twice(lambda s: s.upper(), 10)     # error: (str) -> str not compatible
apply_twice(lambda n: str(n), 10)        # error: return type str, expected int
```

### B — Protocol `__call__` for complex signatures

When a callable has keyword arguments, overloads, or optional parameters,
`Callable` cannot express the shape. Use a `Protocol` with `__call__` instead.

```python
from typing import Protocol

class Formatter(Protocol):
    def __call__(self, value: str, *, width: int = 80) -> str: ...

def render(text: str, fmt: Formatter) -> str:
    return fmt(text, width=40)                # OK

def simple_fmt(value: str, *, width: int = 80) -> str:
    return value.ljust(width)

render("hello", simple_fmt)                   # OK — structurally matches
render("hello", lambda v, **kw: v)            # error: signature mismatch
```

### C — `ParamSpec` for signature-preserving decorators

`ParamSpec` captures the full parameter list so the decorator's return type
keeps the original function's signature visible to the checker.

```python
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

def log_calls(func: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@log_calls
def add(a: int, b: int) -> int:
    return a + b

add(1, 2)             # OK — checker sees (int, int) -> int
add("x", "y")         # error: expected int, got str
```

### D — `@overload` for multi-signature APIs

When a single function has distinct input/output type relationships,
`@overload` lets the checker see each mapping individually.

```python
from typing import overload

@overload
def fetch(url: str, raw: bool = ...) -> str: ...       # type: ignore[overload-overlap]
@overload
def fetch(url: str, raw: bool = ...) -> bytes: ...     # type: ignore[overload-overlap]

# Precise overloads:
@overload
def fetch(url: str) -> str: ...
@overload
def fetch(url: str, raw: bool) -> bytes: ...

def fetch(url: str, raw: bool = False) -> str | bytes:
    data = b"<html>"
    return data if raw else data.decode()

text: str = fetch("https://example.com")         # OK
blob: bytes = fetch("https://example.com", True)  # OK
num: int = fetch("https://example.com")           # error: str not assignable to int
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| `Callable` | Simple, concise, widely understood | Cannot express keyword args, defaults, or overloads |
| Protocol `__call__` | Full signature expressiveness | More boilerplate; less familiar to newcomers |
| `ParamSpec` | Perfectly preserves signatures in decorators | Requires Python 3.10+ or `typing_extensions` |
| `@overload` | Precise per-combination typing | Combinatorial explosion with many parameter variants |

## When to use which feature

**Use `Callable`** for simple callbacks with positional parameters and a single
return type — event handlers, sort keys, map/filter functions.

**Use Protocol `__call__`** when the callable has keyword-only arguments, optional
parameters, or you need structural matching against existing functions.

**Use `ParamSpec`** whenever you write a decorator that should preserve the
decorated function's full signature. This is the standard approach for
logging, retry, caching, and authorization decorators.

**Use `@overload`** when the return type depends on the *value* or *type* of an
argument (e.g., `json.loads` returning `dict` vs `list` depending on input).

**Combine them**: a `ParamSpec` decorator can wrap an `@overload`-ed function,
and a `Protocol` can describe callbacks that themselves use `@overload`.

## Source anchors

- [PEP 484 — Callable types](https://peps.python.org/pep-0484/#callable)
- [PEP 612 — ParamSpec](https://peps.python.org/pep-0612/)
- [PEP 544 — Protocols with __call__](https://peps.python.org/pep-0544/)
- [PEP 484 — @overload](https://peps.python.org/pep-0484/#function-method-overloading)
- [typing spec: Callable](https://typing.readthedocs.io/en/latest/spec/callables.html)
- [mypy docs: Protocols and callable types](https://mypy.readthedocs.io/en/stable/protocols.html)
