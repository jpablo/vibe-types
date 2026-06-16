# Macros & Metaprogramming (via Decorators and Metaclasses)

> **Since:** Decorators Python 2.4 (PEP 318); metaclasses Python 2.2 (the `metaclass=` keyword syntax arrived in Python 3.0, PEP 3115); `__init_subclass__` Python 3.6 (PEP 487); `dataclass_transform` Python 3.11 (PEP 681) | **Backport:** `typing_extensions`

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
p = Point(x="a", y=2.0)   # error: "Literal['a']" is not assignable to "float"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dataclasses / derivation** [-> T06](T06-derivation.md) | `@dataclass` is itself a decorator that performs metaprogramming. `dataclass_transform` lets custom decorators get the same checker support. |
| **ParamSpec** [-> T45](T45-paramspec-variadic.md) | `ParamSpec` preserves the wrapped function's signature through a decorator, preventing type erasure. |
| **Callable types** [-> T22](T22-callable-typing.md) | Decorators are higher-order functions: they accept and return callables. Proper typing requires `Callable[P, R]` with `ParamSpec`. |
| **Protocol** [-> T07](T07-structural-typing.md) | A metaclass can enforce that subclasses implement certain methods, but a Protocol achieves this structurally without metaclass complexity. |
| **ABC** [-> T05](T05-type-classes.md) | `ABCMeta` is itself a metaclass. Combining it with a custom metaclass requires multiple inheritance from both metaclasses. |

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
from collections.abc import Callable
from typing import ParamSpec, TypeVar

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
greet(42)                        # error: "Literal[42]" is not assignable to "str"
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
u = User(id="x", name="Alice", email="a@b.com")           # error: "Literal['x']" is not assignable to "int"
```

## Use-case cross-references

- [-> UC-07](../usecases/UC07-callable-contracts.md) — Callable-typed parameters for higher-order decorator factories.

## Recommended libraries

| Library | Description |
|---|---|
| [pluggy](https://pypi.org/project/pluggy/) | Plugin framework used by pytest — typed hook specifications and implementations with `@hookimpl` / `@hookspec` |
| [wrapt](https://pypi.org/project/wrapt/) | Robust decorator utilities that correctly handle instance methods, class methods, and descriptor protocol edge cases |

## When to Use It

Use decorators and metaprogramming when:

### Cross-cutting concerns need to be centralized

Multiple functions or classes need the same wrapper behavior (logging, caching, auth, validation).

```python
from collections.abc import Callable
from functools import wraps

def logged[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@logged
def add(a: int, b: int) -> int:
    return a + b

@logged
def multiply(a: int, b: int) -> int:
    return a * b
```

### Generating boilerplate from annotations

You have a class with type annotations and need `__init__`, validation, or serialization generated.

```python
from typing import dataclass_transform

@dataclass_transform()
def model[T](cls: type[T]) -> type[T]:
    """Generates __init__ from annotations."""
    def __init__(self: T, **kwargs: object) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    setattr(cls, "__init__", __init__)
    return cls

@model
class Point:
    x: float
    y: float

p = Point(x=1.0, y=2.0)  # checker sees __init__(x: float, y: float)
```

### Runtime behavior depends on parameterized configuration

Decorator factories allow passing config at decoration time.

```python
from collections.abc import Callable
from functools import wraps

def retry[**P, R](times: int) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if i == times - 1:
                        raise
            raise RuntimeError("unreachable")
        return wrapper
    return decorator

class Api:
    @retry(3)
    def fetch_data(self, url: str) -> str:
        # Simulating network call
        raise ConnectionError("Failed")
```

### You need automatic class registration or interface enforcement

Metaclasses can collect subclasses or validate that all subclasses implement required methods.

```python
from typing import Any

class InjectableMeta(type):
    registry: dict[str, type[Any]] = {}

    def __init__(
        cls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> None:
        super().__init__(name, bases, namespace)
        if name != "Injectable":
            InjectableMeta.registry[name] = cls

class Injectable(metaclass=InjectableMeta):
    pass

class DatabaseService(Injectable):
    pass

class EmailService(Injectable):
    pass

print(InjectableMeta.registry)
# {'DatabaseService': <class ...>, 'EmailService': <class ...>}
```

## When NOT to Use It

Avoid decorators and metaprogramming when:

### Logic is simple enough to be inline

```python
import time
from collections.abc import Callable
from functools import wraps

# Over-engineering: a decorator used by exactly one method
def single_function_timer[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.time()
        result = func(*args, **kwargs)
        print(f"Took {time.time() - start}s")
        return result
    return wrapper

class Foo:
    @single_function_timer
    def slow_method(self) -> int:
        return 42

# Simpler: time it inline
class FooSimple:
    def slow_method(self) -> int:
        start = time.time()
        result = 42
        print(f"Took {time.time() - start}s")
        return result
```

### You need to modify the type checker's view of a class

Decorators cannot add attributes to the static type of a class.

```python
# Won't work as expected — the checker cannot see runtime mutation
def add_runtime_attribute[T: type](cls: T) -> T:
    setattr(cls, "computed_value", 42)
    return cls

@add_runtime_attribute
class Entity:
    pass

e = Entity()
print(e.computed_value)  # error: Cannot access attribute "computed_value" for class "Entity"
```

### The indirection outweighs the benefit

```python
from collections.abc import Callable

# Too much indirection — decorator factories wrapping trivial behavior
def _a() -> Callable[[type], type]:
    def _wrap(cls: type) -> type:
        return cls
    return _wrap

def _b() -> Callable[[type], type]:
    def _wrap(cls: type) -> type:
        setattr(cls, "_f", lambda: 42)
        return cls
    return _wrap

@_a()
@_b()  # What does this even do?
class MysteryClass:
    pass
```

### A simpler pattern exists

Dataclasses already provide the metaprogramming pattern most often needed.

```python
from dataclasses import dataclass
from typing import dataclass_transform

# Unnecessary custom machinery
@dataclass_transform()
def simple_dataclass[T](cls: type[T]) -> type[T]:
    # Generates __init__, __repr__, __eq__ manually at runtime
    ...
    return cls

@simple_dataclass
class User:
    name: str
    age: int

# Use dataclass directly
@dataclass
class UserSimple:
    name: str
    age: int
```

## Antipatterns When Using This Technique

### Using metaclasses for simple subclass hooks

Metaclasses are heavy; `__init_subclass__` is lighter for most subclass logic.

```python
from typing import Any

# Overkill with metaclass
class RegistryMeta(type):
    _registry: dict[str, type[Any]] = {}

    def __init__(
        cls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> None:
        super().__init__(name, bases, namespace)
        if name != "Base":
            RegistryMeta._registry[name] = cls

class Base(metaclass=RegistryMeta):
    pass

class Child(Base):
    pass

# Prefer __init_subclass__ — runs only for subclasses, no metaclass needed
class SimpleBase:
    _registry: dict[str, type[Any]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        SimpleBase._registry[cls.__name__] = cls

class SimpleChild(SimpleBase):
    pass
```

### Decorators that silently mutate global state

Side effects in decorators make debugging difficult.

```python
from collections.abc import Callable
from functools import wraps

# Bad: global mutation without warning
_call_log: list[str] = []

def log_calls[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        _call_log.append(func.__name__)
        return func(*args, **kwargs)
    return wrapper

# Good: explicit state ownership
class Logger:
    def __init__(self) -> None:
        self._call_log: list[str] = []

    def decorate[**P, R](self, func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            self._call_log.append(func.__name__)
            return func(*args, **kwargs)
        return wrapper
```

### Metaclasses that depend on source introspection

Reading source code at class-creation time is fragile; inspect the class namespace instead.

```python
import inspect
from typing import Any

# Fragile: reads source code
class CodeParsingMeta(type):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> "CodeParsingMeta":
        source = inspect.getsource(bases[0])
        if "# TODO" in source:
            raise RuntimeError("TODO in source!")
        return super().__new__(mcs, name, bases, namespace)

# Robust: inspects the class dict instead
class SafeMeta(type):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> "SafeMeta":
        if namespace.get("_deprecated"):
            raise RuntimeError("Class marked as deprecated!")
        return super().__new__(mcs, name, bases, namespace)
```

### Dropping metadata by omitting `@wraps`

Without `functools.wraps`, the wrapper erases `__name__`, `__doc__`, and introspection metadata.

```python
from collections.abc import Callable
from functools import wraps

# Bad: erases metadata
def no_wraps_decorator[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)
    return wrapper

# Good: preserves metadata
def wraps_decorator[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)
    return wrapper
```

### Combining incompatible metaclasses without diamond merging

A class can only have one metaclass; incompatible metaclasses cause errors.

```python
class MetaA(type):
    pass

class MetaB(type):
    pass

class A(metaclass=MetaA):
    pass

class B(metaclass=MetaB):
    pass

class C(A, B):  # error: The metaclass of a derived class must be a subclass of the metaclasses of all its base classes
    pass

# Fix: merge the metaclasses explicitly
class MetaAB(MetaA, MetaB):
    pass

class CFixed(A, B, metaclass=MetaAB):
    pass
```

## Antipatterns Fixed by This Technique

### Repeated inline validation

Each method re-implements the same argument check.

```python
from collections.abc import Callable
from functools import wraps
from typing import cast

# Before: inline repetition
class Form:
    def submit_name(self, name: str) -> None:
        if not name:
            raise ValueError("Name required")
        self._process(name)

    def submit_email(self, email: str) -> None:
        if not email:
            raise ValueError("Email required")
        self._process(email)

    def _process(self, value: str) -> None:
        pass

# After: a decorator centralizes the validation
def requires_arg[F: Callable[..., object]](name: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(self: object, value: str, *args: object, **kwargs: object) -> object:
            if not value:
                raise ValueError(f"{name} required")
            return func(self, value, *args, **kwargs)
        return cast(F, wrapper)
    return decorator

class FormDecorated:
    @requires_arg("name")
    def submit_name(self, name: str) -> None:
        self._process(name)

    @requires_arg("email")
    def submit_email(self, email: str) -> None:
        self._process(email)

    def _process(self, value: str) -> None:
        pass
```

### Manual plugin registration

Every plugin author must remember to register the class by hand.

```python
from typing import Any

# Before: manual registration — easy to forget
plugin_registry: dict[str, type[Any]] = {}

class CSVPlugin:
    pass

class JSONPlugin:
    pass

plugin_registry["CSVPlugin"] = CSVPlugin    # must be repeated for every plugin
plugin_registry["JSONPlugin"] = JSONPlugin

# After: a metaclass registers every subclass automatically
class PluginMeta(type):
    registry: dict[str, type[Any]] = {}

    def __init__(
        cls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> None:
        super().__init__(name, bases, namespace)
        if name != "Plugin":
            PluginMeta.registry[name] = cls

class Plugin(metaclass=PluginMeta):
    pass

class AutoCSVPlugin(Plugin):
    pass

class AutoJSONPlugin(Plugin):
    pass

print(PluginMeta.registry)  # automatically populated
```

### Repeating the same wrapper pattern for caching

Each method manually implementing cache logic.

```python
from collections.abc import Callable
from functools import wraps
from typing import cast

# Before: inline cache logic repeated per method
class Fetcher:
    def __init__(self) -> None:
        self._cache: dict[int, str] = {}

    def get_user(self, user_id: int) -> str:
        if user_id in self._cache:
            return self._cache[user_id]
        data = self._fetch(user_id)
        self._cache[user_id] = data
        return data

    def get_product(self, product_id: int) -> str:
        if product_id in self._cache:
            return self._cache[product_id]
        data = self._fetch(product_id)
        self._cache[product_id] = data
        return data

    def _fetch(self, id_: int) -> str:
        return f"record-{id_}"

# After: a caching decorator
def cache[F: Callable[..., object]](func: F) -> F:
    cache_store: dict[object, object] = {}

    @wraps(func)
    def wrapper(self: object, *args: object, **kwargs: object) -> object:
        key = (func.__name__, args, tuple(sorted(kwargs.items(), key=lambda kv: kv[0])))
        if key not in cache_store:
            cache_store[key] = func(self, *args, **kwargs)
        return cache_store[key]
    return cast(F, wrapper)

class CachedFetcher:
    @cache
    def get_user(self, user_id: int) -> str:
        return self._fetch(user_id)

    @cache
    def get_product(self, product_id: int) -> str:
        return self._fetch(product_id)

    def _fetch(self, id_: int) -> str:
        return f"record-{id_}"
```

## Source anchors

- [PEP 318 — Decorators for Functions and Methods](https://peps.python.org/pep-0318/)
- [PEP 3115 — Metaclasses in Python 3000](https://peps.python.org/pep-3115/)
- [PEP 487 — Simpler customisation of class creation](https://peps.python.org/pep-0487/)
- [PEP 681 — Data Class Transforms](https://peps.python.org/pep-0681/)
- [PEP 612 — Parameter Specification Variables](https://peps.python.org/pep-0612/)
- [Python Data Model — Metaclasses](https://docs.python.org/3/reference/datamodel.html#metaclasses)
- [mypy — Decorator factories and ParamSpec](https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators)
