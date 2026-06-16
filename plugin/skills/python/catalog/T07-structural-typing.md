# Protocol (Structural Subtyping)

> **Since:** Python 3.8 (PEP 544) | **Backport:** `typing_extensions.Protocol`

## What it is

A `Protocol` class defines a structural interface — a set of methods and/or attributes that a type must have to be considered compatible. Unlike nominal subtyping (where a class must explicitly inherit from a base), structural subtyping checks whether a class *has the right shape*, regardless of its inheritance tree. This is static duck typing: if it has a `read()` method returning `bytes`, it satisfies `Readable`, even if it has never heard of `Readable`.

Protocols can declare methods (with full signatures), attributes (with types), and even `__call__` signatures. They can be generic (`Protocol[T]`), composed via multiple inheritance, and optionally decorated with `@runtime_checkable` to enable `isinstance()` checks (with limitations).

The key distinction from ABCs is that Protocol satisfaction is checked *structurally by the type checker* — no registration, no inheritance. The class either has the required members or it does not.

## What constraint it enforces

**A class satisfies a Protocol if and only if it provides all required methods and attributes with compatible types — no inheritance needed. The type checker rejects any value passed where a Protocol is expected if it lacks the required members.**

Specifically:

- Every method in the Protocol must exist on the candidate with a compatible signature (parameter types, return type).
- Every attribute must exist with a compatible type.
- The candidate may have *additional* members — only the Protocol's members are checked.
- Generic Protocols enforce type parameter consistency across the required members.

## Minimal snippet

```python
# expect-error
from typing import Protocol

class Closeable(Protocol):
    def close(self) -> None: ...

def cleanup(resource: Closeable) -> None:
    resource.close()

class FileWrapper:
    def close(self) -> None:
        print("closed")

class NotCloseable:
    pass

cleanup(FileWrapper())      # OK — has close() -> None
cleanup(NotCloseable())     # error: "NotCloseable" has no attribute "close"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Generics / TypeVar** [-> T04](T04-generics-bounds.md) | Protocols can be generic: `class Comparable(Protocol[T])`. TypeVars can be bounded by a Protocol: `T = TypeVar("T", bound=SupportsLessThan)`. |
| **ABC** [-> T05](T05-type-classes.md) | ABCs use nominal subtyping (explicit inheritance). Protocols use structural subtyping. A class can satisfy a Protocol and inherit from an ABC simultaneously, but the two checks are independent. |
| **Callable types** [-> T22](T22-callable-typing.md) | A Protocol with `__call__` is a more flexible alternative to `Callable[...]` — it can have attributes alongside the call signature. |
| **Dataclasses** [-> T06](T06-derivation.md) | A dataclass automatically satisfies any Protocol whose required attributes match the dataclass fields. |
| **Generic classes / Variance** [-> T08](T08-variance-subtyping.md) | Generic Protocols follow the same variance rules as generic classes. A `Protocol[T_co]` with a covariant TypeVar makes the Protocol covariant in that parameter. |

## Gotchas and limitations

1. **`@runtime_checkable` only checks method *existence*, not signatures.** `isinstance(obj, MyProtocol)` verifies that the methods exist as attributes, but does not check parameter types or return types. A class with `def close(self, force: int) -> str` passes `isinstance(x, Closeable)` even though it does not structurally match. Pyright even warns about this trap directly at the `isinstance` call:

   ```python
   # expect-error
   from typing import Protocol, runtime_checkable

   @runtime_checkable
   class Sized(Protocol):
       def __len__(self) -> int: ...

   class Fake:
       def __len__(self) -> str:   # wrong return type!
           return "nope"

   # True at runtime — isinstance only checks that __len__ exists
   isinstance(Fake(), Sized)  # error: Class overlaps "Sized" unsafely and could produce a match at runtime
   ```

2. **Parameter names are part of the structural match — unless you mark them positional-only.** A Protocol method `def read(self, n: int) -> bytes: ...` requires implementations to accept a *keyword* argument named `n`. Many standard-library types (e.g., `io.BytesIO`) declare their parameters positional-only with different names (`read(size, /)`, `write(buffer, /)`), so they fail to match such a Protocol. Declare Protocol parameters positional-only with `/` when only the position matters (see Example A).

3. **Attribute protocols require the attribute to be settable (by default).** If a Protocol declares `x: int`, the candidate must have a *mutable* attribute `x`. To require only a read-only attribute, declare it as a property.

   ```python
   from typing import Protocol

   class HasX(Protocol):
       @property
       def x(self) -> int: ...     # read-only: any class with x -> int satisfies this

   class HasMutableX(Protocol):
       x: int                       # mutable: requires x to be assignable
   ```

4. **Implicit Protocol satisfaction can be fragile.** Renaming a method or changing a parameter type silently breaks Protocol compatibility. There is no explicit `implements` declaration to produce a clear error at the implementation site.

5. **Protocol members must not have default implementations (in general).** Methods in a Protocol body should use `...` as their body. If you provide a default implementation, the class becomes a mixin-like base, and checkers may treat it differently. Use `@abstractmethod` in a Protocol only for documentation — it has no effect on structural checking.

6. **Self-referential Protocols.** A Protocol method can reference the Protocol itself (e.g., `def merge(self, other: "Mergeable") -> "Mergeable"`), but the checker verifies that implementing classes provide the exact structural match, which can be tricky with covariance.

7. **Protocol does not compose with `__init__`.** Protocols typically do not constrain constructors. If you need to constrain how a class is instantiated, use a `Callable[[...], T]` or a factory Protocol.

## Beginner mental model

Think of a Protocol as a checklist posted on a door. Any class that has every item on the checklist can walk through — it does not need a badge (inheritance) from the checklist author. If the checklist says "must have `read()` returning `bytes`", then `FileReader`, `SocketStream`, and `MockReader` all pass if they have that method, even if they share no common parent. The type checker is the bouncer verifying the checklist at check time.

## Example A — File-like protocol for anything with read() and write()

```python
# expect-error
from typing import Protocol

class FileLike(Protocol):
    # The `/` makes the parameters positional-only: implementations may name
    # them anything. Without it, io.BytesIO would NOT match — its read/write
    # parameters are positional-only with different names (`size`, `buffer`).
    def read(self, n: int = -1, /) -> bytes: ...
    def write(self, data: bytes, /) -> int: ...

def copy_stream(src: FileLike, dst: FileLike, chunk: int = 4096) -> int:
    total = 0
    while True:
        data = src.read(chunk)
        if not data:
            break
        total += dst.write(data)
    return total

# Works with standard library IO — no inheritance from FileLike needed
import io
buf_in = io.BytesIO(b"hello world")
buf_out = io.BytesIO()
copy_stream(buf_in, buf_out)                    # OK

# Works with custom classes
class S3Object:
    def read(self, n: int = -1) -> bytes:
        return b"data"
    def write(self, data: bytes) -> int:
        return len(data)

copy_stream(S3Object(), buf_out)                # OK

# Fails for incompatible classes
class Logger:
    def write(self, msg: str) -> None:          # str, not bytes — and no read()
        print(msg)

copy_stream(Logger(), buf_out)                  # error: "Logger" is incompatible with protocol "FileLike"
                                                #   "read" is not present
                                                #   "write" is an incompatible type
```

## Example B — Comparable protocol for sorting

```python
from typing import Any, Protocol, TypeVar, runtime_checkable

@runtime_checkable
class SupportsLessThan(Protocol):
    def __lt__(self, other: Any, /) -> bool: ...

T = TypeVar("T", bound=SupportsLessThan)

def merge_sorted(xs: list[T], ys: list[T]) -> list[T]:
    """Merge two sorted lists into one sorted list."""
    result: list[T] = []
    i = j = 0
    while i < len(xs) and j < len(ys):
        if xs[i] < ys[j]:
            result.append(xs[i])
            i += 1
        else:
            result.append(ys[j])
            j += 1
    result.extend(xs[i:])
    result.extend(ys[j:])
    return result

# OK — int supports __lt__
merge_sorted([1, 3, 5], [2, 4, 6])

# OK — str supports __lt__
merge_sorted(["a", "c"], ["b", "d"])

# error — complex does not support __lt__
merge_sorted([1+2j], [3+4j])                   # error: complex is not SupportsLessThan

# Generic Protocol with type parameter
class Container[T](Protocol):
    def get(self) -> T: ...
    def set(self, value: T) -> None: ...

class Box:
    def __init__(self, value: int) -> None:
        self._value = value
    def get(self) -> int:
        return self._value
    def set(self, value: int) -> None:
        self._value = value

def swap(c: Container[int], new: int) -> int:
    old = c.get()
    c.set(new)
    return old

swap(Box(10), 20)                               # OK — Box satisfies Container[int]
```

## Common type-checker errors and how to read them

### mypy: `"X" is not compatible with protocol "Y"`

The class is missing a required method or has an incompatible signature.

```text
error: Argument 1 to "cleanup" has incompatible type "NotCloseable";
       expected "Closeable"
note: "NotCloseable" is missing following "Closeable" protocol member:
note:     close
```

**Fix:** Add the missing method with the correct signature to the class.

### pyright: `Cannot assign type "X" to type "Y"` (Protocol mismatch)

```text
error: Type "Logger" is not assignable to type "FileLike"
  "Logger" is incompatible with protocol "FileLike"
    "write" is an incompatible type
      Type "(msg: str) -> None" is not assignable to type "(data: bytes) -> int"
```

**Fix:** Align the method signatures. Pyright's nested indentation shows exactly which member and which type component mismatches — read from the inside out.

### mypy: `Only @runtime_checkable protocols can be used with isinstance()`

Using `isinstance(x, MyProtocol)` where `MyProtocol` lacks the `@runtime_checkable` decorator.

```text
error: Only @runtime_checkable protocols can be used with isinstance()
```

**Fix:** Add `@runtime_checkable` to the Protocol, or use type narrowing (`TypeGuard` / `TypeIs`) instead.

### mypy: `Protocol member "x" has type incompatibility`

An attribute's type in the implementing class does not match the Protocol's declaration.

```text
error: Incompatible types in assignment (expression has type "str", target has type "int")
note: Following member of "Impl" is incompatible:
note:     x: expected "int", got "str"
```

**Fix:** Change the attribute type in the implementing class to match the Protocol.

## Use-case cross-references

- [-> UC04](../usecases/UC04-generic-constraints.md) — Protocols define capability interfaces for plug-in architectures without coupling to specific classes.
- [-> UC05](../usecases/UC05-structural-contracts.md) — Protocol-bounded TypeVars encode structural constraints that multiple unrelated types can satisfy.
- [-> UC07](../usecases/UC07-callable-contracts.md) — Generic Protocols combine duck typing with type-parameter tracking for collections and containers.

## Recommended libraries

| Library | Description |
|---|---|
| [beartype](https://pypi.org/project/beartype/) | Runtime Protocol checking with near-zero overhead — validates that objects satisfy Protocol contracts at call time |
| [typing_extensions](https://pypi.org/project/typing-extensions/) | Backports of `Protocol`, `runtime_checkable`, and other typing features to older Python versions |

## When to Use Protocols

**Prefer protocols when:**

1. **Designing flexible APIs** — Consumers should not need to import or inherit from your base classes.

   ```python
   from typing import Protocol

   class Closeable(Protocol):
       def close(self) -> None: ...

   def cleanup(resource: Closeable) -> None:
       resource.close()

   # Any object with close() works — no inheritance required
   class FileWrapper:
       def close(self) -> None:
           print("closed")

   class Mock:
       def close(self) -> None:
           pass

   cleanup(FileWrapper())  # OK
   cleanup(Mock())         # OK — different origin, same shape
   ```

2. **Integrating unrelated codebases** — Third-party types with matching shapes compose without adapters.

   ```python
   from typing import Protocol

   class HasSize(Protocol):
       def __len__(self) -> int: ...

   def report_size(obj: HasSize) -> str:
       return f"size: {len(obj)}"

   # Works with list, str, dict — any object with __len__
   report_size([1, 2, 3])     # OK
   report_size("hello")       # OK
   report_size({"a": 1})      # OK
   ```

3. **Defining duck-typed contracts** — When behavior matters more than origin.

   ```python
   from collections.abc import Iterator
   from typing import Protocol

   class IntSource(Protocol):
       def __iter__(self) -> Iterator[int]: ...

   def consume(src: IntSource) -> list[int]:
       return [x for x in src]

   class RangeLike:
       def __init__(self, n: int) -> None:
           self.n = n
       def __iter__(self) -> Iterator[int]:
           yield from range(self.n)

   consume(RangeLike(3))  # OK — has a compatible __iter__
   ```

4. **Testing with mocks** — Mock objects satisfy protocols if they have the required methods.

   ```python
   from typing import Any, Protocol

   class Database(Protocol):
       def query(self, sql: str) -> list[dict[str, Any]]: ...

   def get_user(db: Database, name: str) -> dict[str, Any]:
       results = db.query(f"SELECT * FROM users WHERE name = '{name}'")
       return results[0]

   # Mock for testing
   class MockDB:
       def query(self, sql: str) -> list[dict[str, Any]]:
           return [{"id": 1, "name": "Alice"}]

   get_user(MockDB(), "Alice")  # OK — has query method
   ```

## When NOT to Use Protocols

**Avoid relying solely on protocols when:**

1. **Semantic distinction matters** — Structurally identical types should not be interchangeable.

   ```python
   from typing import Protocol

   class HasValue(Protocol):
       @property
       def value(self) -> float: ...

   # Celsius and Fahrenheit are structurally identical — the Protocol
   # cannot tell them apart
   def to_kelvin(temp: HasValue) -> float:
       return temp.value + 273.15

   class Celsius:
       def __init__(self, value: float) -> None:
           self._value = value
       @property
       def value(self) -> float:
           return self._value

   class Fahrenheit:
       def __init__(self, value: float) -> None:
           self._value = value
       @property
       def value(self) -> float:
           return self._value

   to_kelvin(Celsius(20.0))     # OK
   to_kelvin(Fahrenheit(68.0))  # Also OK — structurally identical, semantically wrong
   ```

   **Fix:** Use type aliases with branding or nominal classes when semantic distinction matters.

2. **Runtime type checking is required** — Protocol checking is static only (except `@runtime_checkable`, which has limitations).

   ```python
   from typing import Protocol

   class Closeable(Protocol):
       def close(self) -> None: ...

   def maybe_close(obj: object) -> None:
       # Runtime check is impossible without @runtime_checkable
       # Even with @runtime_checkable, signature checking is not enforced
       pass
   ```

   **Fix:** Use `@runtime_checkable` sparingly (signature checks are not enforced) or add discriminant attributes.

3. **Overlapping protocols cause confusion** — Too many partial protocols can create ambiguous compatibility.

   ```python
   from typing import Protocol

   class WithID(Protocol):
       id: int

   class WithName(Protocol):
       name: str

   class WithEmail(Protocol):
       email: str

   # Combined protocol — note Protocol must be re-listed as a base,
   # otherwise this becomes a concrete (nominal) class
   class Processable(WithID, WithName, WithEmail, Protocol):
       """Requires every member of every base protocol."""

   class User:
       def __init__(self) -> None:
           self.id = 1
           self.name = "A"
           self.email = "a@example.com"

   # User satisfies WithID, WithName, WithEmail, and Processable —
   # with many small overlapping protocols it gets hard to track intent
   def process(obj: Processable) -> None: ...

   process(User())  # OK
   ```

## Antipatterns When Using Protocols

### Antipattern: Relying on `@runtime_checkable` for Signature Validation

`isinstance` against a runtime-checkable Protocol checks only that members *exist*, not that their signatures match.

```python
# expect-error
from typing import Protocol, runtime_checkable

@runtime_checkable
class Closeable(Protocol):
    def close(self) -> None: ...

class WrongSig:
    def close(self, force: bool) -> str:  # wrong signature!
        return "nope"

# True at runtime — isinstance only checks that close exists
isinstance(WrongSig(), Closeable)  # error: Class overlaps "Closeable" unsafely and could produce a match at runtime
```

**Fix:** Use `@runtime_checkable` only for optional runtime narrowing; rely on static checking for signatures.

### Antipattern: Using Protocols for Nominal Distinction

Using protocols when you need nominal type safety leads to accidental interchangeability.

```python
from typing import Protocol

class UserId(Protocol):
    @property
    def value(self) -> str: ...

class Email(Protocol):
    @property
    def value(self) -> str: ...

class ID:
    value = "user123"

def login(user_id: UserId) -> None: ...
def send_email(address: Email) -> None: ...

login(ID())           # OK
send_email(ID())      # Also OK — structurally identical, semantically wrong
```

**Fix:** Use nominal classes or branded types when semantic distinction matters.

### Antipattern: Extra Required Parameters in Implementations

An implementation method may add extra parameters *with defaults* and stay compatible — but an extra *required* parameter silently breaks Protocol satisfaction at every call site.

```python
# expect-error
from typing import Protocol

class Closeable(Protocol):
    def close(self) -> None: ...

def cleanup(resource: Closeable) -> None:
    resource.close()

class Resource:
    def close(self, force: bool) -> None:  # extra REQUIRED param!
        pass

class GentleResource:
    def close(self, force: bool = False) -> None:  # extra param with default — still compatible
        pass

cleanup(Resource())        # error: "Resource" is incompatible with protocol "Closeable"
cleanup(GentleResource())  # OK — callers can invoke close() with no arguments
```

**Fix:** Give extra parameters defaults (or remove them) so the Protocol's call shape stays satisfiable.

### Antipattern: Overly Complex Protocol Hierarchies

Creating deep protocol hierarchies defeats the simplicity of structural typing.

```python
from typing import Protocol

class Base1(Protocol): ...
class Base2(Base1, Protocol): ...
class Base3(Base2, Protocol): ...
class Base4(Base3, Protocol): ...

def process(x: Base4) -> None: ...

# Any type satisfying the full shape works, but maintenance is hard
```

**Fix:** Keep protocols flat and focused on single responsibilities.

## Antipatterns with Other Techniques: Where Protocols Help

### Antipattern: Using ABCs When Structural Typing Suffices

Using abstract base classes when protocols would be simpler and more flexible.

```python
# expect-error
from abc import ABC, abstractmethod

# ❌ Antipattern: rigid nominal interface
class Closeable(ABC):
    @abstractmethod
    def close(self) -> None: ...

def cleanup(resource: Closeable) -> None:
    resource.close()

class File:
    def close(self) -> None: ...

cleanup(File())  # error: "File" is incompatible with "Closeable" — no inheritance

# ✅ Fix: use a protocol
from typing import Protocol

class CloseableProto(Protocol):
    def close(self) -> None: ...

def cleanup_proto(resource: CloseableProto) -> None:
    resource.close()

cleanup_proto(File())  # OK — structural, no inheritance needed
```

### Antipattern: Manual Type Guards Instead of Protocol Bounding

```python
from typing import Protocol, TypeGuard

class Closeable(Protocol):
    def close(self) -> None: ...

# ❌ Antipattern: manual predicate at every call site
def is_closeable(obj: object) -> TypeGuard[Closeable]:
    return callable(getattr(obj, "close", None))

def cleanup_old(obj: object) -> None:
    if is_closeable(obj):
        obj.close()  # works, but every caller repeats the guard

# ✅ Fix: require the protocol in the signature
def cleanup(resource: Closeable) -> None:
    resource.close()  # cleaner — the checker verifies call sites

class File:
    def close(self) -> None: ...

cleanup(File())  # OK — structural
```

### Antipattern: Casting Instead of Declaring the Protocol

```python
from typing import Protocol, cast

class Closeable(Protocol):
    def close(self) -> None: ...

# ❌ Antipattern: cast masks real errors
def handle_unsafe(obj: object) -> None:
    res = cast("Closeable", obj)
    res.close()  # unchecked — crashes if obj has no close()

# ✅ Fix: declare the Protocol; the checker verifies call sites
def handle(resource: Closeable) -> None:
    resource.close()  # type-safe

class File:
    def close(self) -> None: ...

handle(File())  # OK — structural
```

### Antipattern: Adapter Classes for Shape-Compatible Objects

```python
from typing import Protocol

class File:
    def close(self) -> None: ...

# ❌ Antipattern: adapter wrapper just to "convert" the type
class CloseableAdapter:
    def __init__(self, obj: File) -> None:
        self.obj = obj
    def close(self) -> None:
        self.obj.close()

def adapt_and_close(resource: CloseableAdapter) -> None:
    resource.close()

adapt_and_close(CloseableAdapter(File()))  # verbose, no added safety

# ✅ Fix: use a protocol directly
class Closeable(Protocol):
    def close(self) -> None: ...

def cleanup(resource: Closeable) -> None:
    resource.close()

cleanup(File())  # OK — no adapter needed
```

## Source anchors

- [PEP 544 — Protocols: Structural subtyping (static duck typing)](https://peps.python.org/pep-0544/)
- [`typing` module docs — Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [typing spec: Protocols](https://typing.readthedocs.io/en/latest/spec/protocol.html)
- [mypy docs: Protocols](https://mypy.readthedocs.io/en/stable/protocols.html)
- [pyright docs: Protocols](https://microsoft.github.io/pyright/#/mypy-comparison?id=protocol-support)
