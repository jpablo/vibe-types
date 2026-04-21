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
|-----|----|-----------------|
| **Generics / TypeVar** [-> catalog/07](T04-generics-bounds.md) | ParamSpec and TypeVarTuple are specialized TypeVar siblings. They share the same generic framework but capture different shapes: TypeVar captures one type, ParamSpec captures a signature, TypeVarTuple captures a sequence. |
| **Callable types** [-> catalog/11](T22-callable-typing.md) | `Callable[P, R]` uses ParamSpec as the parameter specification. Without ParamSpec, `Callable` is limited to fixed positional arguments. |
| **Generic classes / Variance** [-> catalog/18](T08-variance-subtyping.md) | Classes can be parameterized with ParamSpec or TypeVarTuple: `class Middleware(Generic[P, R]):`. |
| **Protocol** [-> catalog/09](T07-structural-typing.md) | A Protocol with `__call__[P, R]` achieves similar goals to `Callable[P, R]` but allows additional attributes alongside the call signature. |

## When to use it

| Scenario | Why ParamSpec/TypeVarTuple |
|----------|---------------------------|
| **Writing generic decorators** | Preserves exact function signatures through wrappers, maintaining type safety for callers. |
| **Building middleware frameworks** | Captures and forwards arbitrary request handlers without losing type information. |
| **Typed tuple operations** | `Head`, `Tail`, tuple concatenation while preserving per-element types. |
| **Shape-aware tensor/array classes** | Tracks dimension types at the type level for shape-preserving operations. |
| **Higher-order functions that forward args** | `map`, `filter`, `partial` implementations that work on variadic callables. |
| **Dependency injection containers** | Resolving callables by name while preserving their exact signatures for injection. |

### Good paramSpec example — Decorator that preserves signature

```python
from typing import Callable, ParamSpec, TypeVar
from functools import wraps

P = ParamSpec("P")
R = TypeVar("R")

def retry_on_failure(max_attempts: int = 3) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator factory that retries the decorated function up to max_attempts times."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exc: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
            raise last_exc  # type: ignore[raise-missing-from]
        return wrapper
    return decorator

@retry_on_failure(max_attempts=2)
def divide(a: float, b: float) -> float:
    return a / b

divide(10.0, 2.0)        # OK
divide("10", "2")        # error: argument type mismatch
divide(10.0)             # error: missing required argument
```

### Good TypeVarTuple example — Shape-preserving tuple operations

```python
from typing import TypeVarTuple, Generic, Unpack

Ts = TypeVarTuple("Ts")

def tuple_tail(tup: tuple[int, *Ts]) -> tuple[*Ts]:
    """Return the tuple minus its first element."""
    return tup[1:]  # type: ignore[return-value]

def tuple_unzip(tup: tuple[tuple[*Ts], tuple[*Ts]]) -> tuple[tuple[*Ts], tuple[*Ts]]:
    """Identity-like operation preserving variadic structure."""
    return tup

result = tuple_tail((1, "a", False))  
# result: tuple[str, bool]

# Typed tensor-like class with shape preservation
Dim1 = TypeVarTuple("Dim1")

class Vector(Generic[*Dim1]):
    def __init__(self, *dims: int) -> None:
        self._dims = dims

    def flatten(self) -> tuple[int, ...]:
        """Return shape as a flat tuple."""
        return self._dims

v = Vector(3, 4, 5)  # conceptually Vector[int, int, int]
shape = v.flatten()  # tuple[int, ...]
```

## When NOT to use it

| Scenario | Better Alternative |
|----------|-------------------|
| **Simple fixed-arity functions** | Use regular type annotations; ParamSpec adds unnecessary complexity. |
| **Runtime-only wrappers** | If the wrapper doesn't need to preserve the signature for type checking, use `Callable[..., Any]`. |
| **Homogeneous collections** | Use `list[T]`, `tuple[T, ...]`, `set[T]` when element types are uniform. |
| **Dynamic introspection-heavy code** | ParamSpec cannot decompose individual parameter types; use proper dataclasses or protocols. |
| **Overly complex type-level transformations** | If type inference becomes unclear or error messages are cryptic, simplify. |
| **Pure data containers** | Use dataclasses/namedtuples when you need named fields with independent types. |

### Bad — Overly complex decorator

```python
from typing import Callable, ParamSpec, TypeVar, Any

P = ParamSpec("P")
R = TypeVar("R")

def overly_complex(
    func: Callable[P, R],
    config: dict[str, Any],
    logger: object
) -> Callable[P, R]:
    """This signature is overly complex for what it does."""
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Config: {config}")
        return func(*args, **kwargs)  # type: ignore[no-any-return]
    return wrapper

# Simpler alternative without ParamSpec:
from typing import Callable

def log_decorator(func: Callable[..., object]) -> Callable[..., object]:
    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> object:
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)  # type: ignore[no-any-return, misc]
    return wrapper
```

### Bad — TypeVarTuple for homogeneous tuples

```python
from typing import TypeVarTuple, Generic, Unpack

Ts = TypeVarTuple("Ts")

def sum_homogeneous(tup: tuple[*Ts]) -> float:
    """Summing arbitrary types doesn't make sense."""
    total = 0.0
    for item in tup:
        total += float(item)  # type: ignore[arg-type]
    return total

# Better: use a homogeneous constraint
def sum_numbers(tup: tuple[float, ...]) -> float:
    return sum(tup)

sum_numbers((1.0, 2.5, 3.0))  # ✓ clear and simple
```

## Antipatterns when using it

```python
from typing import Callable, ParamSpec, TypeVar, TypeVarTuple, Generic, Unpack
from functools import wraps

P = ParamSpec("P")
R = TypeVar("R")
Ts = TypeVarTuple("Ts")

# ❌ Forging ParamSpec without actual preservation
def leaks_signature(func: Callable[P, R]) -> Callable[P, R]:
    """Returns Callable[P, R] but wrapper doesn't actually use P.args/P.kwargs."""
    def wrapper(*args: object, **kwargs: object) -> object:
        # Should use: *args: P.args, **kwargs: P.kwargs
        # The type annotation says it preserves signature but runtime accepts anything
        return func(*args, **kwargs)  # type: ignore
    return wrapper  # type: ignore

@leaks_signature
def safe_add(a: int, b: int) -> int:
    return a + b

safe_add("not", "ints")  # Should error but doesn't — broken preservation

# ✅ Fix: always use P.args and P.kwargs together
def proper_preservation(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)
    return wrapper


# ❌ Overusing TypeVarTuple for fixed patterns
class FixedShapeBad(Generic[*Ts]):
    """Using TypeVarTuple for fixed-size vectors is overkill."""
    def __init__(self, *dims: int) -> None:
        self._dims = dims

# Better: use explicit generics for fixed dimensions
class Vector3(Generic[T]):
    """Explicit 3D vector with uniform type."""
    def __init__(self, x: T, y: T, z: T) -> None:
        self.x, self.y, self.z = x, y, z


# ❌ Trying to extract individual parameter types from ParamSpec
def first_param_type(func: Callable[P, R]) -> object:
    """Cannot extract first param type — ParamSpec is opaque."""
    # Cannot do: P.args[0] or func.__annotations__.get('first')
    # Type checkers don't support ParamSpec decomposition
    return None


# ❌ Concatenate in the wrong direction
def wrong_concatenate(func: Callable[P, R]) -> Callable[Concatenate[int, P], R]:
    """You can only prepend with Concatenate, not append."""
    # Cannot append args: this returns a callable expecting int as first arg
    def wrapper(x: int, *args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)  # type: ignore
    return wrapper


# ❌ Nesting ParamSpec in overly complex ways
def decorator_factory(
    a: int,
    b: str,
    c: bool,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)
        return wrapper
    return decorator

# This works but becomes hard to read when deeply nested
# Prefer simpler decorators unless you truly need all parameters


# ❌ TypeVarTuple unpacking in incompatible positions
from typing import Concatenate

def bad_unpack(tup: tuple[*Ts, int], extra: tuple[*Ts]) -> None:
    """Cannot use *Ts in different positions with different trailing types."""
    pass

# The constraint becomes too complex for the checker
# Use simpler patterns or explicit types

# ✅ Fix: use consistent patterns
def good_unpack(tup: tuple[*Ts]) -> tuple[*Ts]:
    """Simple identity operation."""
    return tup
```

## Antipatterns where this technique fixes them

```python
from typing import Callable, ParamSpec, TypeVar, TypeVarTuple, Generic, Unpack
from functools import wraps

P = ParamSpec("P")
R = TypeVar("R")
Ts = TypeVarTuple("Ts")

# ❌ Antipattern: Decorator that loses type information
from typing import Any

def bad_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """Loses all signature information."""
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@bad_decorator
def greet(name: str, age: int) -> str:
    return f"{name} is {age}"

greet(42, "thirty")  # Should error but doesn't! Type info lost.

# ✅ Fix with ParamSpec
def good_decorator(func: Callable[P, R]) -> Callable[P, R]:
    """Preserves signature exactly."""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@good_decorator
def greet_fixed(name: str, age: int) -> str:
    return f"{name} is {age}"

greet_fixed(42, "thirty")  # error: argument type mismatch!


# ❌ Antipattern: HOF with erased argument types
def bad_partial(func: Callable[..., Any], first: Any) -> Callable[..., Any]:
    """Partial application loses all type info."""
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(first, *args, **kwargs)
    return wrapper

add = lambda x: lambda y: x + y
add5 = bad_partial(add, 5)
add5("hello")  # Should error but doesn't!

# ✅ Fix with proper typing
def partial_with_params(
    func: Callable[Concatenate[int, P], R]
) -> Callable[P, R]:
    """Partial application preserving remaining signature."""
    def wrapper(x: int) -> Callable[P, R]:
        @wraps(func)
        def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(x, *args, **kwargs)
        return inner
    return wrapper

def add_two(a: int, b: int, c: int) -> int:
    return a + b + c

add_five = partial_with_params(add_two)(5)
add_five(3, 4)       # OK: 12
add_five("3", 4)     # error: first arg must be int!


# ❌ Antipattern: Tuple operations returning Any
def bad_head(tup: tuple[Any, ...]) -> Any:
    """Loses first element's type."""
    return tup[0]

def bad_tail(tup: tuple[Any, ...]) -> tuple[Any, ...]:
    """Loses per-element types."""
    return tup[1:]

bad_head((1, "a", True))   # type is Any, not int
bad_tail((1, "a", True))   # type is tuple[Any, ...], not tuple[str, bool]

# ✅ Fix with TypeVarTuple
def typed_head(tup: tuple[int, *Ts]) -> int:
    """First element is known to be int."""
    return tup[0]

def typed_tail(tup: tuple[int, *Ts]) -> tuple[*Ts]:
    """Rest preserves individual types."""
    return tup[1:]  # type: ignore[return-value]

typed_head((1, "a", True))     # type is int
typed_tail((1, "a", True))     # type is tuple[str, bool]


# ❌ Antipattern: Middleware that breaks type chains
from typing import Callable, Awaitable

async def bad_middleware(
    handler: Callable[..., Awaitable[Any]],
    request: dict[str, Any]
) -> Awaitable[Any]:
    """Async middleware losing all signature info."""
    result = await handler(request)
    return result

# ✅ Fix with ParamSpec for async handlers
async def typed_middleware(
    handler: Callable[P, Awaitable[R]],
    extra: str
) -> Callable[P, Awaitable[R]]:
    """Preserves async handler signature."""
    @wraps(handler)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return await handler(*args, **kwargs)
    return wrapper


# ❌ Antipattern: Tensor operations losing shape info
class BadTensor:
    def __init__(self, data: list[int], shape: tuple[int, ...]) -> None:
        self._data = data
        self._shape = shape

    def transpose(self) -> "BadTensor":
        """Loses shape info entirely."""
        return BadTensor(self._data, self._shape[::-1])

# ✅ Fix with TypeVarTuple
class TypedTensor(Generic[*Ts]):
    """Shape tracked at type level."""
    def __init__(self, data: list[int], shape: tuple[*Ts]) -> None:
        self._data = data
        self._shape = shape

    def transpose(self) -> "TypedTensor[*Ts]":  # simplification
        """Shape structure preserved (in practice would reverse dims)."""
        return TypedTensor(self._data, self._shape)
```

## Gotchas and limitations

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

- [-> UC-07](../usecases/UC07-callable-contracts.md) — ParamSpec enables type-safe decorator patterns that preserve function signatures.

## Source anchors

- [PEP 612 — Parameter Specification Variables](https://peps.python.org/pep-0612/)
- [PEP 646 — Variadic Generics](https://peps.python.org/pep-0646/)
- [`typing` module docs — ParamSpec](https://docs.python.org/3/library/typing.html#typing.ParamSpec)
- [`typing` module docs — TypeVarTuple](https://docs.python.org/3/library/typing.html#typing.TypeVarTuple)
- [typing spec: ParamSpec](https://typing.readthedocs.io/en/latest/spec/callables.html#paramspec)
- [mypy docs: ParamSpec](https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators)
