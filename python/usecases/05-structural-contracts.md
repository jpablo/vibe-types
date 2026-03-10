# Structural Contracts

## The constraint

Duck typing gets static verification through `Protocol`. Code that expects "anything with a `.read()` method" can declare that requirement as a type, and the checker enforces it without requiring the provider to inherit from a specific base class.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Generics / TypeVar | Parameterize over structural types to preserve specificity | [-> catalog/07](../catalog/07-generics-typevar.md) |
| Protocol | Define structural interfaces checked at type-check time | [-> catalog/09](../catalog/09-protocol-structural-subtyping.md) |
| ABC | Nominal alternative when explicit opt-in is desired | [-> catalog/10](../catalog/10-abc-abstract-classes.md) |

## Patterns

### A — Protocol for file-like objects

Define a structural contract for anything readable, without coupling to `io.IOBase`.

```python
from typing import Protocol

class Readable(Protocol):
    def read(self, n: int = -1) -> str: ...

def first_line(source: Readable) -> str:
    content = source.read()
    return content.split("\n")[0]  # OK — .read() guaranteed by Protocol

import io
first_line(io.StringIO("hello\nworld"))   # OK — StringIO has .read()
first_line("not a file")                   # error: "str" has no "read" method
```

### B — Protocol for iterables and sized containers

Express "has `__len__` and `__iter__`" without requiring inheritance.

```python
from typing import Protocol, Iterator

class SizedIterable(Protocol[_T_co := ...]):
    """Simplified — real generic Protocol shown for illustration."""
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator: ...

# In practice, use typing.Sized and typing.Iterable from collections.abc.
# But custom Protocols let you combine capabilities precisely:

class HasLenAndContains(Protocol):
    def __len__(self) -> int: ...
    def __contains__(self, item: object) -> bool: ...

def summary(c: HasLenAndContains) -> str:
    return f"Collection with {len(c)} items"  # OK

summary([1, 2, 3])           # OK — list has __len__ and __contains__
summary({1, 2})              # OK — set has both
summary(42)                  # error: "int" missing "__len__" and "__contains__"
```

### C — Runtime-checkable Protocol

Add `@runtime_checkable` so `isinstance` checks work at runtime, while still getting static checking.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Closable(Protocol):
    def close(self) -> None: ...

def safe_close(resource: object) -> None:
    if isinstance(resource, Closable):  # OK — runtime check
        resource.close()                # OK — narrowed to Closable

import io
safe_close(io.StringIO())    # OK — has .close()
safe_close("not closable")   # OK — isinstance returns False, no call made
```

### D — Protocol vs ABC comparison

Illustrate the difference between structural (Protocol) and nominal (ABC) contracts.

```python
from typing import Protocol
from abc import ABC, abstractmethod

# --- Structural: Protocol ---
class Renderable(Protocol):
    def render(self) -> str: ...

# --- Nominal: ABC ---
class RenderableABC(ABC):
    @abstractmethod
    def render(self) -> str: ...

# This class does NOT inherit from either:
class HtmlWidget:
    def render(self) -> str:
        return "<div>widget</div>"

def show_protocol(r: Renderable) -> str:
    return r.render()

def show_abc(r: RenderableABC) -> str:
    return r.render()

show_protocol(HtmlWidget())  # OK — structural match: has .render() -> str
show_abc(HtmlWidget())       # error: "HtmlWidget" is not a subtype of "RenderableABC"
```

### Untyped Python comparison

Without Protocol, duck typing has no static safety net.

```python
# No types — "duck typing" is just hope
def first_line(source):
    content = source.read()    # AttributeError at runtime if source has no .read()
    return content.split("\n")[0]

first_line(42)  # AttributeError: 'int' object has no attribute 'read'
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **Protocol** | Structural: works with any type that has matching methods; no inheritance required | Cannot enforce invariants or provide default implementations |
| **runtime_checkable Protocol** | Bridges static and runtime checking; enables `isinstance` | Only checks method existence at runtime, not signatures; slight performance cost |
| **ABC** | Nominal: explicit opt-in; can provide default implementations and enforce abstract methods | Requires inheritance; cannot type-check third-party classes that happen to match |
| **Protocol + Generics** | Preserves specific types through generic calls while requiring structural capabilities | More complex to define; error messages may be harder to interpret |

## When to use which feature

- **Protocol** as the default for structural contracts — whenever you want to say "anything with these methods" without requiring inheritance. This is idiomatic Python.
- **runtime_checkable Protocol** when you need `isinstance` checks at runtime in addition to static checking, e.g., for defensive programming or plugin systems.
- **ABC** when you want to enforce explicit opt-in, provide default method implementations, or when the contract includes state invariants that structural matching cannot capture.
- **Protocol + Generics** when a generic function needs to both preserve the input type and require structural capabilities (e.g., `T` where `T` has `.size()`).

## Source anchors

- [PEP 544 — Protocols: Structural subtyping](https://peps.python.org/pep-0544/)
- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
- [mypy — Protocols and structural subtyping](https://mypy.readthedocs.io/en/stable/protocols.html)
- [Python `abc` module documentation](https://docs.python.org/3/library/abc.html)
- [typing module — Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
