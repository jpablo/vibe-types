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
| **Generics / TypeVar** [-> catalog/07](T04-generics-bounds.md) | Protocols can be generic: `class Comparable(Protocol[T])`. TypeVars can be bounded by a Protocol: `T = TypeVar("T", bound=SupportsLessThan)`. |
| **ABC** [-> catalog/10](T05-type-classes.md) | ABCs use nominal subtyping (explicit inheritance). Protocols use structural subtyping. A class can satisfy a Protocol and inherit from an ABC simultaneously, but the two checks are independent. |
| **Callable types** [-> catalog/11](T22-callable-typing.md) | A Protocol with `__call__` is a more flexible alternative to `Callable[...]` — it can have attributes alongside the call signature. |
| **Dataclasses** [-> catalog/06](T06-derivation.md) | A dataclass automatically satisfies any Protocol whose required attributes match the dataclass fields. |
| **Generic classes / Variance** [-> catalog/18](T08-variance-subtyping.md) | Generic Protocols follow the same variance rules as generic classes. A `Protocol[T_co]` with a covariant TypeVar makes the Protocol covariant in that parameter. |

## Gotchas and limitations

1. **`@runtime_checkable` only checks method *existence*, not signatures.** `isinstance(obj, MyProtocol)` verifies that the methods exist as attributes, but does not check parameter types or return types. A class with `def close(self, force: int) -> str` passes `isinstance(x, Closeable)` even though it does not structurally match.

   ```python
   from typing import Protocol, runtime_checkable

   @runtime_checkable
   class Sized(Protocol):
       def __len__(self) -> int: ...

   class Fake:
       def __len__(self) -> str:   # wrong return type!
           return "nope"

   isinstance(Fake(), Sized)       # True at runtime (only checks __len__ exists)
   # But the type checker flags: Fake does not satisfy Sized (__len__ returns str, not int)
   ```

2. **Attribute protocols require the attribute to be settable (by default).** If a Protocol declares `x: int`, the candidate must have a *mutable* attribute `x`. To require only a read-only attribute, declare it as a property.

   ```python
   class HasX(Protocol):
       @property
       def x(self) -> int: ...     # read-only: any class with x -> int satisfies this

   class HasMutableX(Protocol):
       x: int                       # mutable: requires x to be assignable
   ```

3. **Implicit Protocol satisfaction can be fragile.** Renaming a method or changing a parameter type silently breaks Protocol compatibility. There is no explicit `implements` declaration to produce a clear error at the implementation site.

4. **Protocol members must not have default implementations (in general).** Methods in a Protocol body should use `...` as their body. If you provide a default implementation, the class becomes a mixin-like base, and checkers may treat it differently. Use `@abstractmethod` in a Protocol only for documentation — it has no effect on structural checking.

5. **Self-referential Protocols.** A Protocol method can reference the Protocol itself (e.g., `def merge(self, other: "Mergeable") -> "Mergeable"`), but the checker verifies that implementing classes provide the exact structural match, which can be tricky with covariance.

6. **Protocol does not compose with `__init__`.** Protocols typically do not constrain constructors. If you need to constrain how a class is instantiated, use a `Callable[[...], T]` or a factory Protocol.

## Beginner mental model

Think of a Protocol as a checklist posted on a door. Any class that has every item on the checklist can walk through — it does not need a badge (inheritance) from the checklist author. If the checklist says "must have `read()` returning `bytes`", then `FileReader`, `SocketStream`, and `MockReader` all pass if they have that method, even if they share no common parent. The type checker is the bouncer verifying the checklist at check time.

## Example A — File-like protocol for anything with read() and write()

```python
from typing import Protocol

class FileLike(Protocol):
    def read(self, n: int = -1) -> bytes: ...
    def write(self, data: bytes) -> int: ...

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
    def write(self, msg: str) -> None:          # str, not bytes!
        print(msg)

copy_stream(Logger(), buf_out)                  # error: "Logger" is not compatible with "FileLike"
                                                #   "write" has incompatible type
```

## Example B — Comparable protocol for sorting

```python
from typing import Protocol, TypeVar, runtime_checkable

@runtime_checkable
class SupportsLessThan(Protocol):
    def __lt__(self, other: object) -> bool: ...

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
from typing import Generic

class Container(Protocol[T]):
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

```
error: Argument 1 to "cleanup" has incompatible type "NotCloseable";
       expected "Closeable"
note: "NotCloseable" is missing following "Closeable" protocol member:
note:     close
```

**Fix:** Add the missing method with the correct signature to the class.

### pyright: `Cannot assign type "X" to type "Y"` (Protocol mismatch)

```
error: Type "Logger" is not assignable to type "FileLike"
  "Logger" is incompatible with protocol "FileLike"
    "write" is an incompatible type
      Type "(msg: str) -> None" is not assignable to type "(data: bytes) -> int"
```

**Fix:** Align the method signatures. Pyright's nested indentation shows exactly which member and which type component mismatches — read from the inside out.

### mypy: `Only @runtime_checkable protocols can be used with isinstance()`

Using `isinstance(x, MyProtocol)` where `MyProtocol` lacks the `@runtime_checkable` decorator.

```
error: Only @runtime_checkable protocols can be used with isinstance()
```

**Fix:** Add `@runtime_checkable` to the Protocol, or use type narrowing (`TypeGuard` / `TypeIs`) instead.

### mypy: `Protocol member "x" has type incompatibility`

An attribute's type in the implementing class does not match the Protocol's declaration.

```
error: Incompatible types in assignment (expression has type "str", target has type "int")
note: Following member of "Impl" is incompatible:
note:     x: expected "int", got "str"
```

**Fix:** Change the attribute type in the implementing class to match the Protocol.

## Use-case cross-references

- [-> UC-04](../usecases/UC04-generic-constraints.md) — Protocols define capability interfaces for plug-in architectures without coupling to specific classes.
- [-> UC-05](../usecases/UC05-structural-contracts.md) — Protocol-bounded TypeVars encode structural constraints that multiple unrelated types can satisfy.
- [-> UC-07](../usecases/UC07-callable-contracts.md) — Generic Protocols combine duck typing with type-parameter tracking for collections and containers.

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
   from typing import Protocol

   class Iterator(Protocol[T]): ...

   def consume(it: Iterator[int]) -> list[int]:
       return [x for x in it]

   class RangeLike:
       def __init__(self, n: int): self.n = n
       def __iter__(self):
           for i in range(self.n):
               yield i

   consume(RangeLike(3))  # OK — has __iter__
   ```

4. **Testing with mocks** — Mock objects satisfy protocols if they have the required methods.

   ```python
   from typing import Protocol

   class Database(Protocol):
       def query(self, sql: str) -> list[dict]: ...

   def get_user(db: Database, name: str) -> dict:
       results = db.query(f"SELECT * FROM users WHERE name = '{name}'")
       return results[0]

   # Mock for testing
   mock_db = type("MockDB", (), {"query": lambda sql: [{"id": 1, "name": "Alice"}]})()
   get_user(mock_db, "Alice")  # OK — has query method
   ```

## When NOT to Use Protocols

**Avoid relying solely on protocols when:**

1. **Semantic distinction matters** — Structurally identical types should not be interchangeable.

   ```python
   from typing import Protocol

   class HasValue(Protocol):
       @property
       def value(self) -> float: ...

   # Celsius and Fahrenheit are both floats — Protocol cannot distinguish
   def to_kelvin(temp: HasValue) -> float:
       return temp.value + 273.15

   # Both work, but only摄氏度 should:
   class Celsius:
       @property
       def value(self) -> float: ...
   class Fahrenheit:
       @property
       def value(self) -> float: ...

   to_kelvin(Celsius())  # OK
   to_kelvin(Fahrenheit())  # Also OK — structurally identical, semantically wrong
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

   # Any object with all three attributes satisfies all three protocols
   def process(obj: WithID & WithName & WithEmail) -> None: ...

   # Hard to track intended types
   process(type("Obj", (), {"id": 1, "name": "A", "email": "a"})())
   ```

## Antipatterns When Using Protocols

### Antipattern: Relying on `@runtime_checkable` for Signature Validation

`@runtime_checkable` only checks method *existence*, not signatures.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Closeable(Protocol):
    def close(self) -> None: ...

class WrongSig:
    def close(self, force: bool) -> str:  # wrong signature!
        return "nope"

isinstance(WrongSig(), Closeable)  # True at runtime (only checks close exists)
# But type checker flags: WrongSig does not satisfy Closeable
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

### Antipattern: Implicit Protocol Satisfaction Without Explicit Types

Relying on implicit satisfaction without explicit types makes it harder to track compatibility.

```python
from typing import Protocol

class Closeable(Protocol):
    def close(self) -> None: ...

def cleanup(resource: Closeable) -> None:
    resource.close()

class Resource:
    def close(self, force: bool = False) -> None:  # extra param!
        pass

cleanup(Resource())  # error: extra parameter breaks compatibility
# Hard to diagnose without explicit types
```

**Fix:** Add explicit type annotations to make Protocol expectations clear.

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
from abc import ABC, abstractmethod

# ❌ Antipattern: rigid nominal interface
class Closeable(ABC):
    @abstractmethod
    def close(self) -> None: ...

def cleanup(resource: Closeable) -> None:
    resource.close()

class File:
    def close(self) -> None: ...

cleanup(File())  # error: File does not inherit from Closeable

# ✅ Fix: use protocol
from typing import Protocol

class CloseableProto(Protocol):
    def close(self) -> None: ...

def cleanup(resource: CloseableProto) -> None:
    resource.close()

cleanup(File())  # OK — structural, no inheritance needed
```

### Antipattern: Manual Type Guards Instead of Protocol Bounding

Writing verbose type predicates instead of using protocol bounds.

```python
from typing import TypeVar, TypeGuard

# ❌ Antipattern: manual predicate
T = TypeVar("T")

def is_closeable(obj: T) -> TypeGuard[Closeable]:
    return hasattr(obj, 'close') and callable(obj.close)

def cleanup(obj: object) -> None:
    if is_closeable(obj):
        obj.close()  # verbose

# ✅ Fix: use protocol directly
from typing import Protocol

class Closeable(Protocol):
    def close(self) -> None: ...

def cleanup(resource: Closeable) -> None:
    resource.close()  # cleaner

class File:
    def close(self) -> None: ...

cleanup(File())  # OK — structural
```

### Antipattern: Excessive Type Assertions Instead of Structural Contracts

Using `cast()` or `as` assertions instead of letting structural typing work.

```python
from typing import cast

# ❌ Antipattern: assertions mask real errors
def handle(obj: object) -> None:
    res = cast("Closeable", obj)
    res.close()  # unsafe

# ✅ Fix: use Protocol to enforce contract
from typing import Protocol

class Closeable(Protocol):
    def close(self) -> None: ...

def handle(resource: Closeable) -> None:
    resource.close()  # type-safe

class File:
    def close(self) -> None: ...

handle(File())  # OK — structural
```

### Antipattern: Manual Adapter Patterns Instead of Protocols

Creating explicit adapter classes when protocols would allow direct usage.

```python
# ❌ Antipattern: adapter pattern
class CloseableAdapter:
    def __init__(self, obj: object):
        self.obj = obj
    def close(self) -> None:
        if hasattr(self.obj, 'close'):
            self.obj.close()

def cleanup(resource: CloseableAdapter) -> None:
    resource.close()

class File:
    def close(self) -> None: ...

cleanup(CloseableAdapter(File()))  # verbose adapter

# ✅ Fix: use protocol directly
from typing import Protocol

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
