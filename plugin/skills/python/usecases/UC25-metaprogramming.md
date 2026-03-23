# Metaprogramming (via Decorators and Metaclasses)

## The constraint

Dynamically generated or transformed classes and methods must be visible to the type checker. Decorator patterns, metaclass `__init_subclass__`, and `dataclass_transform` allow metaprogramming while preserving static type information.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Macros / metaprogramming | Decorators and metaclasses that generate code at class definition time | [-> catalog/17](../catalog/T17-macros-metaprogramming.md) |
| Derivation | `dataclass_transform` tells checkers how a decorator generates fields | [-> catalog/06](../catalog/T06-derivation.md) |
| Callable typing | Type decorators that transform function signatures | [-> catalog/11](../catalog/T22-callable-typing.md) |

## Patterns

### A — __init_subclass__ for subclass registration

Hook into subclass creation without a custom metaclass.

```python
class Plugin:
    _registry: dict[str, type["Plugin"]] = {}

    def __init_subclass__(cls, *, name: str = "", **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        key = name or cls.__name__.lower()
        Plugin._registry[key] = cls

    @classmethod
    def get(cls, name: str) -> type["Plugin"]:
        return cls._registry[name]

class AuthPlugin(Plugin, name="auth"):
    pass

class CachePlugin(Plugin, name="cache"):
    pass

Plugin.get("auth")    # AuthPlugin
Plugin.get("cache")   # CachePlugin
```

### B — dataclass_transform for custom class decorators

Tell the type checker that a decorator generates `__init__`, `__eq__`, etc., just like `@dataclass`.

```python
from typing import dataclass_transform

@dataclass_transform()
def my_model(cls: type) -> type:
    """Custom decorator that generates __init__ from annotations."""
    import dataclasses
    return dataclasses.dataclass(cls)

@my_model
class User:
    name: str
    email: str
    age: int

user = User(name="Alice", email="alice@example.com", age=30)  # OK — checker sees __init__
# User(name="Alice")  # error: missing arguments "email" and "age"
```

### C — Metaclass for automatic validation

Use a metaclass to inject validation logic into every subclass.

```python
from typing import Any

class ValidatedMeta(type):
    def __new__(
        mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any]
    ) -> "ValidatedMeta":
        cls = super().__new__(mcs, name, bases, namespace)
        for attr, annotation in getattr(cls, "__annotations__", {}).items():
            if annotation is str:
                original = namespace.get(attr)
                if isinstance(original, str) and not original.strip():
                    raise ValueError(f"{name}.{attr} cannot be empty")
        return cls

class Config(metaclass=ValidatedMeta):
    app_name: str = "myapp"

# class BadConfig(metaclass=ValidatedMeta):
#     app_name: str = ""   # ValueError at class definition time
```

### D — Decorator that adds methods

A decorator can add typed methods to a class using `Protocol` or `TYPE_CHECKING` for visibility.

```python
from typing import TypeVar, TYPE_CHECKING

T = TypeVar("T")

def add_serialize(cls: type[T]) -> type[T]:
    def to_dict(self: T) -> dict[str, object]:
        return {k: getattr(self, k) for k in self.__annotations__}
    cls.to_dict = to_dict  # type: ignore[attr-defined]
    return cls

@add_serialize
class Event:
    name: str
    timestamp: float

    def __init__(self, name: str, timestamp: float) -> None:
        self.name = name
        self.timestamp = timestamp

if TYPE_CHECKING:
    # Help the checker see the added method
    class Event(Event):  # type: ignore[no-redef]
        def to_dict(self) -> dict[str, object]: ...

e = Event("click", 1.0)
e.to_dict()  # {"name": "click", "timestamp": 1.0}
```

### Untyped Python comparison

Without type checker integration, metaprogramming is invisible to static analysis.

```python
# No types — checker sees nothing
def my_model(cls):
    import dataclasses
    return dataclasses.dataclass(cls)

@my_model
class User:
    name: str
    age: int

User(name="Alice", age=30)  # checker cannot verify arguments
User(bad_field=True)         # error only at runtime
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| **__init_subclass__** | No metaclass needed; simple hook for registration/validation | Limited to subclass creation events; cannot modify the class namespace deeply |
| **dataclass_transform** | Checker understands generated `__init__`, `__eq__`, etc. | Must match dataclass semantics; custom field behavior may not be expressible |
| **Metaclass** | Full control over class creation; can inject any behavior | Invisible to type checkers; complex inheritance; only one metaclass per hierarchy |
| **Decorator + TYPE_CHECKING** | Works with existing checkers; explicit type overlay | Fragile; duplicate declarations; `type: ignore` needed |

## When to use which feature

- **Use `__init_subclass__`** for plugin registration, automatic validation hooks, and subclass tracking — it is the simplest and most checker-friendly metaprogramming tool.
- **Use `dataclass_transform`** when building a custom model decorator (ORM, config parser, schema library) that should behave like `@dataclass` to the checker.
- **Use metaclasses** only when `__init_subclass__` is insufficient — class namespace manipulation, descriptor injection, or framework-level class factories.
- **Use `TYPE_CHECKING` overlays** as a last resort when a decorator adds methods that the checker cannot see through normal means.

## Source anchors

- [PEP 487 — __init_subclass__](https://peps.python.org/pep-0487/)
- [PEP 681 — dataclass_transform](https://peps.python.org/pep-0681/)
- [Python data model — Metaclasses](https://docs.python.org/3/reference/datamodel.html#metaclasses)
- [mypy — dataclass_transform](https://mypy.readthedocs.io/en/stable/additional_features.html#dataclass-transform)
- [typing spec — dataclass_transform](https://typing.readthedocs.io/en/latest/spec/dataclasses.html#dataclass-transform)
