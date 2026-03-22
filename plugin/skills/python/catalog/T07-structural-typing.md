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

## Source anchors

- [PEP 544 — Protocols: Structural subtyping (static duck typing)](https://peps.python.org/pep-0544/)
- [`typing` module docs — Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [typing spec: Protocols](https://typing.readthedocs.io/en/latest/spec/protocol.html)
- [mypy docs: Protocols](https://mypy.readthedocs.io/en/stable/protocols.html)
- [pyright docs: Protocols](https://microsoft.github.io/pyright/#/mypy-comparison?id=protocol-support)
