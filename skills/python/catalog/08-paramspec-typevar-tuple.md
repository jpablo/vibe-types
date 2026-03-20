# ParamSpec and TypeVarTuple

> **Since:** `ParamSpec` Python 3.10 (PEP 612) | `TypeVarTuple` Python 3.11 (PEP 646) | **Backport:** `typing_extensions`

## What it is

`ParamSpec` and `TypeVarTuple` extend Python's generics beyond single-type placeholders, addressing two long-standing gaps in the type system.

**ParamSpec** captures an entire callable's parameter signature — not just the return type, but the names, types, positions, and defaults of every parameter. This makes it possible to type decorators that wrap functions without erasing their signatures. Before ParamSpec, decorators either lost type information (returning `Callable[..., Any]`) or required manual overloads for every arity.

**TypeVarTuple** (often written `*Ts`) captures a *variadic* sequence of types, enabling generics parameterized over an arbitrary number of type arguments. The primary use case is typed tuple operations and tensor/array shapes — for example, expressing that a `Tensor[Batch, Height, Width]` can be reshaped to `Tensor[Batch, Height * Width]` while preserving type-level shape tracking.

Both features use `Concatenate` and unpacking (`*Ts` / `Unpack[Ts]`) for composition with other type parameters.

## What constraint it enforces

**ParamSpec preserves callable signatures through wrappers: the checker guarantees the decorated function is called with the same arguments as the original. TypeVarTuple preserves variadic type structure: the checker guarantees tuple and shape operations maintain type-level arity and element types.**

## Minimal snippet

```python
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

def logged(func: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@logged
def greet(name: str, excited: bool = False) -> str:
    return f"Hello, {name}{'!' if excited else '.'}"

greet("Alice", excited=True)      # OK
greet(42)                          # error: expected str, got int
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Generics / TypeVar** [-> catalog/07](07-generics-typevar.md) | ParamSpec and TypeVarTuple are specialized TypeVar siblings. They share the same generic framework but capture different shapes: TypeVar captures one type, ParamSpec captures a signature, TypeVarTuple captures a sequence. |
| **Callable types** [-> catalog/11](11-callable-types-overload.md) | `Callable[P, R]` uses ParamSpec as the parameter specification. Without ParamSpec, `Callable` is limited to fixed positional arguments. |
| **Generic classes / Variance** [-> catalog/18](18-generic-classes-variance.md) | Classes can be parameterized with ParamSpec or TypeVarTuple: `class Middleware(Generic[P, R]):`. |
| **Protocol** [-> catalog/09](09-protocol-structural-subtyping.md) | A Protocol with `__call__[P, R]` achieves similar goals to `Callable[P, R]` but allows additional attributes alongside the call signature. |

## Gotchas and limitations

1. **`P.args` and `P.kwargs` must be used together.** You cannot capture only positional or only keyword arguments from a ParamSpec. Both must appear in the wrapper signature.

   ```python
   def bad(func: Callable[P, R]) -> Callable[P, R]:
       def wrapper(*args: P.args) -> R:      # error: P.kwargs is missing
           return func(*args)
       return wrapper
   ```

2. **`Concatenate` for prepending parameters.** To add an extra parameter before the captured ones, use `Concatenate`:

   ```python
   from typing import Concatenate

   def with_context(
       func: Callable[Concatenate[int, P], R]
   ) -> Callable[P, R]:
       def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
           return func(42, *args, **kwargs)
       return wrapper
   ```

   You can only prepend — appending parameters is not supported.

3. **Only one TypeVarTuple per generic class.** A class cannot have two TypeVarTuples because the checker cannot determine where one sequence ends and the next begins.

   ```python
   from typing import TypeVarTuple, Generic

   Ts1 = TypeVarTuple("Ts1")
   Ts2 = TypeVarTuple("Ts2")

   class Bad(Generic[*Ts1, *Ts2]): ...  # error: only one TypeVarTuple allowed
   ```

4. **Pyright has better TypeVarTuple support than mypy.** As of 2025, mypy's TypeVarTuple support is still incomplete for some patterns (e.g., unpacking in `Callable`, complex map operations). Pyright handles most PEP 646 patterns. Check your checker's documentation for the current state.

5. **ParamSpec does not decompose.** You cannot extract "the first parameter's type" from a ParamSpec. It is opaque — you can forward it or prepend to it with `Concatenate`, but you cannot inspect its internal structure.

6. **`Unpack` vs `*Ts` syntax.** Before Python 3.11, TypeVarTuple unpacking required `Unpack[Ts]`. Python 3.11+ allows `*Ts` directly. Both forms are equivalent, but mixing them in the same codebase can be confusing.

## Beginner mental model

Think of **ParamSpec** as a photocopy of a function's signature. When you write a decorator, you want the wrapper to accept the same inputs as the original — ParamSpec copies the entire parameter list (names, types, defaults) so the checker can verify callers pass the right arguments to the wrapper.

**TypeVarTuple** is like a row of variable-length blanks. Where a regular TypeVar is one blank (`___`), a TypeVarTuple is a sequence of blanks (`___, ___, ___`) whose length is determined at use. This lets you express "a tuple of any length where each element has a known type" or "a tensor whose shape dimensions are tracked at the type level."

## Example A — Decorator that preserves wrapped function's signature

```python
from typing import Callable, ParamSpec, TypeVar
from functools import wraps
import time

P = ParamSpec("P")
R = TypeVar("R")

def timed(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

@timed
def fetch_user(user_id: int, *, include_deleted: bool = False) -> dict[str, object]:
    return {"id": user_id, "deleted": include_deleted}

# Checker preserves the original signature:
fetch_user(42, include_deleted=True)        # OK
fetch_user("not-an-id")                     # error: expected int, got str
fetch_user(42, nonexistent=True)            # error: unexpected keyword argument

# Adding a parameter with Concatenate
from typing import Concatenate

def with_retry(
    func: Callable[Concatenate[int, P], R]
) -> Callable[P, R]:
    """Wraps a function that takes a retry_count as first arg."""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        for attempt in range(3):
            try:
                return func(attempt, *args, **kwargs)
            except Exception:
                if attempt == 2:
                    raise
        raise AssertionError("unreachable")
    return wrapper
```

## Example B — Typed tensor shape with TypeVarTuple

```python
from typing import TypeVarTuple, Generic, TypeVar

DType = TypeVar("DType")
Shape = TypeVarTuple("Shape")

class Tensor(Generic[DType, *Shape]):
    """A tensor whose element type and shape dimensions are tracked."""
    def __init__(self, data: list[object], dtype: type[DType]) -> None:
        self._data = data
        self._dtype = dtype

    def reshape(self, *new_shape: int) -> "Tensor[DType, *tuple[int, ...]]":
        # In practice, static shape checking would be more precise
        return Tensor(self._data, self._dtype)

# Type-level shape tracking
class Batch: ...
class Height: ...
class Width: ...
class Channels: ...

def conv2d(
    image: Tensor[float, Batch, Channels, Height, Width],
    kernel_size: int,
) -> Tensor[float, Batch, Channels, Height, Width]:
    ...

# Typed tuple operations with TypeVarTuple
from typing import Unpack

Ts = TypeVarTuple("Ts")

def head(tup: tuple[int, *Ts]) -> int:
    return tup[0]

def tail(tup: tuple[int, *Ts]) -> tuple[*Ts]:
    return tup[1:]                              # type: ignore[return-value]

t: tuple[int, str, float] = (1, "hello", 3.14)
x: int = head(t)                                # OK
rest: tuple[str, float] = tail(t)               # OK
```

## Common type-checker errors and how to read them

### mypy: `"P.args" must be used with "**P.kwargs"`

The wrapper uses `*args: P.args` but omits `**kwargs: P.kwargs` (or vice versa).

```
error: ParamSpec "P" has no attribute "args"
  note: Use "P.args" and "P.kwargs" together in the wrapper signature
```

**Fix:** Always include both `*args: P.args` and `**kwargs: P.kwargs` in the wrapper.

### pyright: `Expected no type arguments for class "X"`

Using `Callable[P, R]` without importing ParamSpec correctly or using a stale stub.

```
error: Expected no type arguments for class "function"
```

**Fix:** Verify imports: `from typing import ParamSpec, Callable, TypeVar`.

### mypy: `Argument 1 has incompatible type ... expected ...`

The decorator changed the signature — the wrapper does not match the original.

```
error: Argument 1 to "fetch_user" has incompatible type "str"; expected "int"
```

**Fix:** This is the desired behavior — ParamSpec is working. The caller is passing the wrong type.

### mypy: `Only a single TypeVarTuple is allowed in a type parameter list`

Attempting to use two `*Ts` in one generic.

```
error: Only a single TypeVarTuple is allowed
```

**Fix:** Restructure to use a single TypeVarTuple, possibly wrapping one dimension in a separate generic class.

## Use-case cross-references

- [-> UC-07](../usecases/07-api-contracts-callable.md) — ParamSpec enables type-safe decorator patterns that preserve function signatures.
- [-> UC-11](../usecases/11-decorator-typing.md) — TypeVarTuple supports variadic generics for tensor shape typing and typed tuple operations.

## Source anchors

- [PEP 612 — Parameter Specification Variables](https://peps.python.org/pep-0612/)
- [PEP 646 — Variadic Generics](https://peps.python.org/pep-0646/)
- [`typing` module docs — ParamSpec](https://docs.python.org/3/library/typing.html#typing.ParamSpec)
- [`typing` module docs — TypeVarTuple](https://docs.python.org/3/library/typing.html#typing.TypeVarTuple)
- [typing spec: ParamSpec](https://typing.readthedocs.io/en/latest/spec/callables.html#paramspec)
- [mypy docs: ParamSpec](https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators)
