# Macros & Metaprogramming (via Decorators and Metaclasses)

> **Since:** Decorators Python 2.4 (PEP 318); Metaclasses Python 3.0; `__init_subclass__` Python 3.6 (PEP 487); `dataclass_transform` Python 3.11 (PEP 681) | **Backport:** `typing_extensions`

## What it is

Python has no compile-time macro system. Instead, metaprogramming happens at **import time** through decorators, metaclasses, and special dunder hooks. **Decorators** wrap or replace functions and classes — they are the primary mechanism for code transformation (logging, caching, access control, dataclass generation). **Metaclasses** control class creation itself via `type.__new__` and `type.__init__`, enabling patterns like automatic registration, interface enforcement, and ORM field collection. **`__init_subclass__`** (PEP 487) provides a simpler hook that runs when a class is subclassed, without a full metaclass. **`__set_name__`** lets descriptors know the attribute name they were assigned to.

For type checkers, **`dataclass_transform`** (PEP 681) is the key bridge: it tells the checker that a decorator or metaclass behaves like `@dataclass`, so the checker can synthesize `__init__`, `__eq__`, and other methods. Without this marker, checkers cannot see the methods that metaprogramming creates at runtime.

## What constraint it enforces

**Decorators and metaclasses transform classes and functions at import time. The type checker can only see the results if the transformation is annotated with `dataclass_transform`, `ParamSpec`, or explicit return-type annotations on the decorator. Unannotated metaprogramming is invisible to static analysis.**

## Minimal snippet

```python
from typing import dataclass_transform, TypeVar

T = TypeVar("T")

@dataclass_transform()
def auto_init(cls: type[T]) -> type[T]:
    """Decorator that generates __init__ from class annotations."""
    # Runtime implementation omitted — the decorator reads __annotations__
    # and creates __init__ dynamically.
    ...
    return cls

@auto_init
class Point:
    x: float
    y: float

p = Point(x=1.0, y=2.0)   # OK — checker sees __init__(self, x: float, y: float)
p = Point("a")             # error: expected float, got str
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dataclasses / derivation** [-> catalog/T06](T06-derivation.md) | `@dataclass` is itself a decorator that performs metaprogramming. `dataclass_transform` lets custom decorators get the same checker support. |
| **ParamSpec** [-> catalog/T45](T45-paramspec-variadic.md) | `ParamSpec` preserves the wrapped function's signature through a decorator, preventing type erasure. |
| **Callable types** [-> catalog/T22](T22-callable-typing.md) | Decorators are higher-order functions: they accept and return callables. Proper typing requires `Callable[P, R]` with `ParamSpec`. |
| **Protocol** [-> catalog/T07](T07-structural-typing.md) | A metaclass can enforce that subclasses implement certain methods, but a Protocol achieves this structurally without metaclass complexity. |
| **ABC** [-> catalog/T05](T05-type-classes.md) | `ABCMeta` is itself a metaclass. Combining it with a custom metaclass requires multiple inheritance from both metaclasses. |

## Gotchas and limitations

1. **Type checkers cannot follow arbitrary runtime logic.** A decorator that builds methods by reading a config file or database schema produces methods invisible to the checker. Only `dataclass_transform`, `@overload`, and `ParamSpec`-annotated decorators are understood.

2. **Metaclass conflicts.** A class can have only one metaclass. If two libraries each require their own metaclass (e.g., `ABCMeta` and a custom ORM metaclass), you must create a combined metaclass inheriting from both.

3. **`__init_subclass__` cannot modify the subclass's type signature.** The hook runs after the class is created, so changes it makes (adding methods, modifying `__init__`) are invisible to the type checker unless `dataclass_transform` is used.

4. **`dataclass_transform` is limited to dataclass-like patterns.** It tells the checker to synthesize `__init__`, `__eq__`, `__hash__`, and ordering methods. It cannot describe arbitrary code generation (e.g., auto-generated validation methods or serialization).

5. **Decorator ordering matters.** Decorators apply bottom-up. `@a @b def f` means `a(b(f))`. Changing the order can change both runtime behavior and the type the checker infers.

6. **`type: ignore` is common in metaprogramming-heavy code.** When the checker cannot see dynamically generated members, developers resort to suppressing errors, which undermines type safety.

## Beginner mental model

Think of a **decorator** as a gift wrapper — you hand in your plain function, and the decorator wraps it with extra behavior (logging, timing, access checks) before handing it back. A **metaclass** is the factory that builds the box itself — it controls what the class looks like when it is created. The type checker can read the label on the wrapped gift only if the wrapper follows a known pattern (`dataclass_transform` or `ParamSpec`); otherwise, the checker sees an opaque package and guesses `Any`.

## Example A — Typed decorator preserving signatures with ParamSpec

```python
import functools
import time
from typing import ParamSpec, TypeVar, Callable

P = ParamSpec("P")
R = TypeVar("R")

def timed(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that prints execution time."""
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

@timed
def greet(name: str, excited: bool = False) -> str:
    return f"Hello, {name}{'!' if excited else '.'}"

greet("Alice", excited=True)    # OK — signature preserved
greet(42)                        # error: expected str, got int
```

## Example B — dataclass_transform for a custom ORM base

```python
from typing import dataclass_transform, ClassVar

@dataclass_transform()
class ModelMeta(type):
    """Metaclass that auto-generates __init__ from annotations."""
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
    ) -> "ModelMeta":
        cls = super().__new__(mcs, name, bases, namespace)
        # Runtime: generate __init__, __repr__, etc. from annotations
        return cls

class Model(metaclass=ModelMeta):
    """Base class for ORM models."""

class User(Model):
    id: int
    name: str
    email: str
    _table: ClassVar[str] = "users"   # ClassVar excluded from __init__

u = User(id=1, name="Alice", email="alice@example.com")   # OK
u = User(id="x", name="Alice", email="a@b.com")           # error: expected int
```

## Use-case cross-references

- [-> UC-28](../usecases/UC28-decorator-typing.md) — Typing decorators with ParamSpec to preserve wrapped signatures.
- [-> UC-07](../usecases/UC07-callable-contracts.md) — Callable-typed parameters for higher-order decorator factories.
- [-> UC-27](../usecases/UC27-gradual-adoption.md) — Adding types to metaprogramming-heavy codebases incrementally.

## Source anchors

- [PEP 318 — Decorators for Functions and Methods](https://peps.python.org/pep-0318/)
- [PEP 487 — Simpler customisation of class creation](https://peps.python.org/pep-0487/)
- [PEP 681 — Data Class Transforms](https://peps.python.org/pep-0681/)
- [PEP 612 — Parameter Specification Variables](https://peps.python.org/pep-0612/)
- [Python Data Model — Metaclasses](https://docs.python.org/3/reference/datamodel.html#metaclasses)
- [mypy — Decorator factories and ParamSpec](https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators)
