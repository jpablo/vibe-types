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
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar("T")

def logged(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args, **kwargs):
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
def model(cls: type) -> type:
    """Generates __init__ from annotations."""
    annotations = cls.__annotations__
    init_args = list(annotations.keys())

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    setattr(cls, "__init__", __init__)
    return cls

@model
class Point:
    x: float
    y: float

p = Point(x=1.0, y=2.0)  # Has __init__(x: float, y: float)
```

### Runtime behavior depends on parameterized configuration

Decorator factories allow passing config at decoration time.

```python
def retry(times: int):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == times - 1:
                        raise e
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
class InjectableMeta(type):
    registry = {}

    def __init__(cls, name, bases, namespace):
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

The wrapper behavior is specific to one function or class.

```python
# Over-engineering
def single_function_timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        print(f"Took {time.time() - start}s")
        return result
    return wrapper

class Foo:
    @single_function_timer
    def slow_method(self):
        return 42

# Simpler
class Foo:
    def slow_method(self):
        import time
        start = time.time()
        result = 42
        print(f"Took {time.time() - start}s")
        return result
```

### You need to modify the type checker's view of a class

Decorators cannot add attributes to the static type of a class.

```python
# Won't work as expected
def add_runtime_attribute(cls):
    setattr(cls, "computed_value", 42)
    return cls

@add_runtime_attribute
class Entity:
    pass

e: Entity
e.computed_value  # Type error: 'Entity' has no attribute 'computed_value'
```

### The metaprogramming creates "magic" codebases

Junior developers cannot understand how behavior or attributes are derived.

```python
# Too much indirection
def _a:
    def _b:
        def _c(cls):
            setattr(cls, "_f", lambda: 42)
            return cls
        return _c
    return _b
return _a

@_a()
@_b()  # What does this even do?
class MysteryClass:
    pass
```

### A simpler pattern exists

Dataclasses already provide the metaprogramming pattern most often needed.

```python
# Unnecessary metaclass
@dataclass_transform()
def simple_dataclass(cls):
    # Generates __init__, __repr__, __eq__ manually
    ...
    return cls

@simpl...
class User:
    name: str
    age: int

# Use dataclass directly
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int
```

## Antipatterns When Using This Technique

### Using metaclasses for simple subclass hooks

Metaclasses are heavy; `__init_subclass__` is lighter for most subclass logic.

```python
# Overkill with metaclass
class RegistryMeta(type):
    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
        if name != "Base":
            RegistryMeta._registry[name] = cls

    _registry = {}

class Base(metaclass=RegistryMeta):
    pass

class Child(Base):
    pass

# Prefer __init_subclass__
class Base:
    _registry = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__name__ != "Base":
            Base._registry[cls.__name__] = cls

class Child(Base):
    pass
```

### Decorators that silently fail or mutate global state

Side effects in decorators make debugging difficult.

```python
# Bad: global mutation without warning
_call_log = []

def log_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        _call_log.append(func.__name__)
        return func(*args, **kwargs)
    return wrapper

# Good: explicit state ownership
class Logger:
    def __init__(self):
        self._call_log = []

    def decorate(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self._call_log.append(func.__name__)
            return func(*args, **kwargs)
        return wrapper

logger = Logger()
@logger.decorate
def process():
    pass
```

### Metaclasses that inspect stringified AST instead of class dict

Reading `sourcecode` to analyze decorators is fragile and breaks with transpilers.

```python
# Fragile: reads source code
import inspect

class CodeParsingMeta(type):
    def __new__(mcs, name, bases, namespace):
        source = inspect.getsource(bases[0])
        if "# TODO" in source:
            raise RuntimeError("TODO in source!")
        return super().__new__(mcs, name, bases, namespace)

# Robust: inspects class dict
class SafeMeta(type):
    def __new__(mcs, name, bases, namespace):
        if namespace.get("_deprecated"):
            raise RuntimeError("Class marked as deprecated!")
        return super().__new__(mcs, name, bases, namespace)
```

### Decorators without `@wraps` that erase function metadata

Losing `__name__`, `__doc__`, and signature breaks logging, help(), and type inference.

```python
# Bad: erases metadata
def no_wraps_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

# Good: preserves metadata
def wraps_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

### Combining incompatible metaclasses without diamond merging

A class can only have one metaclass; incompatible metaclasses cause runtime errors.

```python
# Error: metaclass conflict
class MetaA(type):
    pass

class MetaB(type):
    pass

class A(metaclass=MetaA):
    pass

class C(A, B):  # TypeError: metaclass conflict
    pass

# Fix: merge metaclasses
class MetaAB(MetaA, MetaB):
    pass

class C(A, B, metaclass=MetaAB):
    pass
```

## Antipatterns With Other Techniques (Fixed Using This Technique)

### Repetitive validation logic across methods

Duplicating validation inside multiple method bodies.

```python
# Before: inline repetition
class Form:
    def submit_name(self, name: str):
        if not name:
            raise ValueError("Name required")
        return self._process(name)

    def submit_email(self, email: str):
        if not email:
            raise ValueError("Email required")
        return self._process(email)

    def _process(self, value: str):
        pass

# After: decorator for validation
def requires_arg(name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(self, value: str, *args, **kwargs):
            if not value:
                raise ValueError(f"{name} required")
            return func(self, value, *args, **kwargs)
        return wrapper
    return decorator

class Form:
    @requires_arg("name")
    def submit_name(self, name: str):
        return self._process(name)

    @requires_arg("email")
    def submit_email(self, email: str):
        return self._process(email)
```

### Manual deep readonly/partial instead of type utilities

Repeating the same nested readonly pattern for every model.

```python
# Before: manual repetition
class Config:
    db_host: str
    db_port: int
    cache_enabled: bool

# Have to manually document "this is readonly"
# No type-enforced pattern exists

# After: use built-in utilities
from typing import TypedDict, NotRequired

class Config(TypedDict, total=False):
    db_host: str
    db_port: int
```

Note: Python's `TypedDict` provides partial types at static analysis time, eliminating manual repetition.

### Repetitive subclass registration

Every subclass manually registering itself in a dict.

```python
# Before: manual registration
plugins = {}

class Plugin:
    def __init__(self):
        plugins[self.__class__.__name__] = self

class CSVPlugin(Plugin):
    pass

class JSONPlugin(Plugin):
    pass
# Each subclass must remember to call super().__init__()

# After: metaclass handles it
class PluginMeta(type):
    registry = {}

    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
        if name != "Plugin":
            PluginMeta.registry[name] = cls

class Plugin(metaclass=PluginMeta):
    pass

class CSVPlugin(Plugin):
    pass

class JSONPlugin(Plugin):
    pass

print(PluginMeta.registry)
# Automatically populated
```

### Repeating the same wrapper pattern for caching

Each method manually implementing cache logic.

```python
# Before: inline cache
class Fetcher:
    def __init__(self):
        self._cache = {}

    def get_user(self, user_id: int):
        if user_id in self._cache:
            return self._cache[user_id]
        data = self._fetch(user_id)
        self._cache[user_id] = data
        return data

    def get_product(self, product_id: int):
        if product_id in self._cache:
            return self._cache[product_id]
        data = self._fetch(product_id)
        self._cache[product_id] = data
        return data

    def _fetch(self, id_):
        pass

# After: caching decorator
def cache(func):
    cache_store = {}

    @wraps(func)
    def wrapper(self, *args):
        key = (func.__name__, args, tuple(sorted(kwargs.items())))
        if key not in cache_store:
            cache_store[key] = func(self, *args, **kwargs)
        return cache_store[key]
    return wrapper

class Fetcher:
    @cache
    def get_user(self, user_id: int):
        return self._fetch(user_id)

    @cache
    def get_product(self, product_id: int):
        return self._fetch(product_id)
```

## Source anchors

- [PEP 318 — Decorators for Functions and Methods](https://peps.python.org/pep-0318/)
- [PEP 487 — Simpler customisation of class creation](https://peps.python.org/pep-0487/)
- [PEP 681 — Data Class Transforms](https://peps.python.org/pep-0681/)
- [PEP 612 — Parameter Specification Variables](https://peps.python.org/pep-0612/)
- [Python Data Model — Metaclasses](https://docs.python.org/3/reference/datamodel.html#metaclasses)
- [mypy — Decorator factories and ParamSpec](https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators)
