# Structural Contracts

## The constraint

Duck typing gets static verification through `Protocol`. Code that expects "anything with a `.read()` method" can declare that requirement as a type, and the checker enforces it without requiring the provider to inherit from a specific base class.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Generics / TypeVar | Parameterize over structural types to preserve specificity | [-> catalog/07](../catalog/T04-generics-bounds.md) |
| Protocol | Define structural interfaces checked at type-check time | [-> catalog/09](../catalog/T07-structural-typing.md) |
| ABC | Nominal alternative when explicit opt-in is desired | [-> catalog/10](../catalog/T05-type-classes.md) |

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

## When to Use It

Use Protocols when you want to accept any matching shape without requiring inheritance or explicit opt-in.

- **Accepting third-party types**: You cannot modify a library to inherit from your base class, but you can define what shape you need
  ```python
  from typing import Protocol

  class Logger(Protocol):
      def log(self, msg: str) -> None: ...

  def with_logging(logger: Logger, fn: callable) -> None:
      logger.log("starting")
      fn()

  import logging
  with_logging(logging.getLogger(__name__), lambda: None)  # OK — has .log()
  ```

- **Loose coupling between modules**: Different teams can provide implementations without importing the Protocol definition
  ```python
  class Writable(Protocol):
      def write(self, data: bytes) -> int: ...

  def flush_buffer(buf: bytes, sink: Writable) -> None:
      sink.write(buf)

  import sys
  flush_buffer(b"data", sys.stdout)  # OK — no import coupling
  ```

- **Testing and mocking**: Any object with the right shape works, no need to create mock classes
  ```python
  from typing import Protocol

  class DataSource(Protocol):
      def fetch(self) -> list[dict]: ...

  def process(source: DataSource) -> int:
      return len(source.fetch())

  process({"fetch": lambda: [{"id": 1}]})  # OK — ad-hoc mock
  ```

- **Ad-hoc inline implementations**: Quick one-off implementations without boilerplate
  ```python
  class Handler(Protocol):
      def __call__(self, event: dict) -> None: ...

  def register(handler: Handler) -> None: ...

  register(lambda e: print(e))  # OK — callable has the shape
  ```

## When Not to Use It

Avoid Protocols when you need explicit membership, shared state, default implementations, or runtime identity.

- **Need default implementations**: Protocols cannot provide method bodies
  ```python
  class Service(Protocol):
      def connect(self) -> None: ...
      def disconnect(self) -> None: ...

  # Every implementation must define both methods
  # Cannot share common connect/disconnect logic
  ```

- **Need to enforce invariants**: Protocols only check method existence, not behavior or state constraints
  ```python
  class Counter(Protocol):
      def increment(self) -> int: ...

  class BadCounter:
      def increment(self) -> int:
          return -1  # Invalid but structurally OK

  use_counter(BadCounter())  # Passes type check, fails at runtime
  ```

- **Need runtime type checking**: Protocols are compile-time only unless `@runtime_checkable` is used
  ```python
  class Drawable(Protocol):
      def draw(self) -> None: ...

  shapes: list[object] = [Circle(), Square()]
  for s in shapes:
      if isinstance(s, Drawable):  # error: Drawable not runtime_checkable
          s.draw()
  ```

- **Need to distinguish incompatible implementations**: Two different classes with the same Protocol are indistinguishable at runtime
  ```python
  class Serializer(Protocol):
      def serialize(self, v: object) -> str: ...

  csv_serializer: Serializer = ...
  json_serializer: Serializer = ...
  # Cannot tell them apart at runtime to choose format-specific logic
  ```

## Antipatterns When Using It

### Antipattern A — Protocol with optional methods

Defining a Protocol with many optional methods creates loose coupling and loses type safety benefits.

```python
from typing import Protocol

# ❌ Bad: Protocol with optional methods loses guarantees
class LooseConfig(Protocol):
    host: str
    port: int
    timeout: int | None = ...
    retries: int | None = ...
    logger: object | None = ...

def connect(cfg: LooseConfig) -> None:
    cfg.logger.log()  # runtime error: Optional[None] has no .log()
```

```python
from typing import Protocol

# ✅ Good: split into focused Protocols or use dataclass
class NetworkConfig(Protocol):
    host: str
    port: int
    timeout: int

class AdvancedConfig(NetworkConfig, Protocol):
    retries: int
    logger: object
```

### Antipattern B — Over-constraining with Protocol

Requiring more methods than needed limits what can satisfy the Protocol.

```python
from typing import Protocol

# ❌ Bad: requires full dict interface when only .keys() is needed
class DictLike(Protocol):
    def keys(self) -> list[str]: ...
    def values(self) -> list[object]: ...
    def items(self) -> list[tuple[str, object]]: ...
    def get(self, k: str) -> object: ...

def list_keys(d: DictLike) -> list[str]:
    return d.keys()

class SparseDict:
    def keys(self) -> list[str]:
        return ["a", "b"]

list_keys(SparseDict())  # error: missing other methods
```

```python
from typing import Protocol

# ✅ Good: minimal Protocol for the use case
class HasKeys(Protocol):
    def keys(self) -> list[str]: ...

def list_keys(d: HasKeys) -> list[str]:
    return d.keys()

list_keys(SparseDict())  # OK
```

### Antipattern C — Runtime check without `@runtime_checkable`

Forgetting `@runtime_checkable` when `isinstance` is needed causes type errors or runtime failures.

```python
from typing import Protocol

# ❌ Bad: Protocol not runtime_checkable
class Writable(Protocol):
    def write(self, data: bytes) -> int: ...

def safe_write(sink: object, data: bytes) -> None:
    if isinstance(sink, Writable):  # error: Writable not runtime_checkable
        sink.write(data)
```

```python
from typing import Protocol, runtime_checkable

# ✅ Good: add runtime_checkable
@runtime_checkable
class Writable(Protocol):
    def write(self, data: bytes) -> int: ...

def safe_write(sink: object, data: bytes) -> None:
    if isinstance(sink, Writable):
        sink.write(data)  # OK
```

### Antipattern D — Protocol for stateful contracts

Using Protocol for types that need shared state or lifecycle management is better served by ABC.

```python
from typing import Protocol

# ❌ Bad: Protocol cannot enforce close() after open()
class Resource(Protocol):
    def open(self) -> None: ...
    def close(self) -> None: ...

class FileResource:
    def open(self) -> None: ...
    def close(self) -> None: ...

def use(r: Resource) -> None:
    r.open()
    # r.close() might be forgotten — no enforcement
```

```python
from contextlib import contextmanager
from abc import ABC, abstractmethod

# ✅ Good: ABC with context manager pattern
class Resource(ABC):
    @abstractmethod
    def __enter__(self) -> "Resource": ...

    @abstractmethod
    def __exit__(self, *args: object) -> None: ...

@contextmanager
def use_resource() -> Resource:
    with open("file.txt") as f:
        yield f
```

## Antipatterns with Other Techniques

### Antipattern A — ABC when Protocol would work

Forcing inheritance when structural typing would suffice creates unnecessary coupling.

```python
from abc import ABC, abstractmethod

# ❌ Bad: requires explicit inheritance
class Handler(ABC):
    @abstractmethod
    def handle(self, event: dict) -> None: ...

def register(handler: Handler) -> None: ...

# Third-party library with compatible shape but no inheritance
class ExternalHandler:
    def handle(self, event: dict) -> None: ...

register(ExternalHandler())  # error: ExternalHandler not a Handler
```

```python
from typing import Protocol

# ✅ Good: Protocol accepts any matching shape
class Handler(Protocol):
    def handle(self, event: dict) -> None: ...

def register(handler: Handler) -> None: ...

register(ExternalHandler())  # OK
```

### Antipattern B — Union type when Protocol suffices

Using union types to accept multiple similar types loses composability.

```python
# ❌ Bad: union type, not composable
def process_json(data: dict) -> None: ...
def process_list(data: list) -> None: ...
def process_str(data: str) -> None: ...

def log_size(data: dict | list | str) -> None:
    if isinstance(data, dict):
        print(len(data))
    elif isinstance(data, list):
        print(len(data))
    else:
        print(len(data))
    # Cannot add new type without modifying this function
```

```python
from typing import Protocol

# ✅ Good: single Protocol, composable
class Sized(Protocol):
    def __len__(self) -> int: ...

def log_size(data: Sized) -> None:
    print(len(data))  # works with dict, list, str, set, custom types
```

### Antipattern C — Type guards for every call instead of Protocol parameter

Adding runtime guards at every call site instead of using Protocol in function signature is redundant.

```python
# ❌ Bad: guards repeated everywhere
def process(data: object) -> None:
    if hasattr(data, "read"):
        data.read()
    else:
        raise TypeError("Expected readable")

def transform(data: object) -> None:
    if hasattr(data, "read"):  # repeated check
        data.read()
    # ...
```

```python
from typing import Protocol

# ✅ Good: Protocol enforces at call site
class Readable(Protocol):
    def read(self) -> str: ...

def process(data: Readable) -> None:
    data.read()  # guaranteed

def transform(data: Readable) -> None:
    data.read()  # guaranteed
# Type checker catches wrong argument: process(42) is error
```

### Antipattern D — Named tuple when Protocol would work

Using named tuples for contracts that describe capabilities rather than data structures.

```python
from collections import namedtuple

# ❌ Bad: named tuple for capability
Point = namedtuple("Point", ["x", "y", "draw"])

def render(p: Point) -> None:
    p.draw()  # awkward: methods in data namedtuple
```

```python
from typing import Protocol

# ✅ Good: Protocol for capability
class Renderable(Protocol):
    x: float
    y: float
    def draw(self) -> None: ...

def render(p: Renderable) -> None:
    p.draw()  # clean: any object with x, y, draw
```

## Source anchors

- [PEP 544 — Protocols: Structural subtyping](https://peps.python.org/pep-0544/)
- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
- [mypy — Protocols and structural subtyping](https://mypy.readthedocs.io/en/stable/protocols.html)
- [Python `abc` module documentation](https://docs.python.org/3/library/abc.html)
- [typing module — Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
