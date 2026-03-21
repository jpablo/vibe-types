# Self Type

> **Since:** Python 3.11 (PEP 673) | **Backport:** `typing_extensions`

## What it is

`Self` is a special form that refers to the enclosing class in a type annotation. When used as a return type, it tells the type checker "this method returns an instance of the same class it was called on" — including subclasses. Before `Self`, the idiomatic workaround was a bound `TypeVar` (`T = TypeVar("T", bound="Base")`), which was verbose and error-prone. `Self` replaces that pattern with a single, readable token.

## What constraint it enforces

**A method annotated with `-> Self` must return a value whose type matches the class the method is called on, not just the class where the method is defined.** This means subclass calls preserve the subclass type through the checker, preventing silent up-casts that would lose subclass-specific information.

## Minimal snippet

```python
from typing import Self  # 3.11+; or typing_extensions for 3.9+

class Shape:
    def set_color(self, color: str) -> Self:
        self.color = color
        return self              # OK

class Circle(Shape):
    def set_radius(self, r: float) -> Self:
        self.radius = r
        return self              # OK

reveal_type(Circle().set_color("red"))  # Circle, not Shape

# Without Self, a hardcoded return type breaks subclasses:
class BadShape:
    def set_color(self, color: str) -> "BadShape":
        self.color = color
        return self

class BadCircle(BadShape): ...

reveal_type(BadCircle().set_color("red"))  # BadShape — lost the subclass type
BadCircle().set_color("red").radius        # error — BadShape has no attribute "radius"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **TypeVar (bound)** [-> catalog/07](07-generics-typevar.md) | `Self` replaces the `T = TypeVar("T", bound="Base")` pattern for return-type polymorphism. TypeVar is still needed for unrelated generic parameters. |
| **Callable** [-> catalog/11](11-callable-types-overload.md) | A `Callable[..., Self]` parameter type describes a factory callback that must produce an instance of the current class. |
| **dataclass** [-> catalog/06](06-dataclasses-typing.md) | `Self` can appear in `@dataclass` methods and `__post_init__` return annotations, though the constructor itself is generated. |
| **Protocol** [-> catalog/09](09-protocol-structural-subtyping.md) | `Self` in a Protocol method means each implementor must return its own concrete type, not the Protocol. |

## Gotchas and limitations

1. **Only valid inside a class body.** Using `Self` at module level or in a free function is a type error.

2. **Not a runtime type.** `Self` has no runtime identity. You cannot use it in `isinstance()` checks or as a base class.

3. **Does not constrain `cls` in `__init_subclass__`.** `Self` refers to the class being defined, not to future subclasses in hook methods.

4. **Checker divergence on edge cases.** mypy and pyright may disagree on `Self` inside nested classes or when combined with `@overload`. Always test with your target checker.

5. **Cannot replace all TypeVar uses.** If you need a TypeVar that relates *two different parameters* (not just the return to `self`), you still need an explicit TypeVar.

6. **Mutable attribute pattern.** Returning `Self` from a method that mutates `self` in-place is idiomatic, but the checker does not verify that the return value *is* literally `self` — any instance of the same type satisfies it.

## Beginner mental model

Think of `Self` as a pronoun that means "my own class." When a `Shape` method says `-> Self`, it promises to return a `Shape`. But when `Circle` inherits that method, `Self` automatically means `Circle`. Without `Self`, the checker would only know the method returns `Shape`, losing track of the `Circle`-specific API.

## Example A — Fluent builder that returns Self for method chaining

```python
from typing import Self

class QueryBuilder:
    def __init__(self) -> None:
        self._table: str = ""
        self._conditions: list[str] = []

    def table(self, name: str) -> Self:
        self._table = name
        return self                      # OK

    def where(self, condition: str) -> Self:
        self._conditions.append(condition)
        return self                      # OK

    def build(self) -> str:
        clauses = " AND ".join(self._conditions)
        return f"SELECT * FROM {self._table} WHERE {clauses}"

class PaginatedQueryBuilder(QueryBuilder):
    def __init__(self) -> None:
        super().__init__()
        self._limit: int = 100

    def limit(self, n: int) -> Self:
        self._limit = n
        return self                      # OK

# Method chaining preserves the subclass type throughout:
query = (
    PaginatedQueryBuilder()
    .table("users")                      # OK — returns PaginatedQueryBuilder
    .where("active = true")              # OK — still PaginatedQueryBuilder
    .limit(50)                           # OK — PaginatedQueryBuilder method
    .build()
)
reveal_type(PaginatedQueryBuilder().table("x"))  # PaginatedQueryBuilder
```

Without `Self`, `.table("users")` would return `QueryBuilder`, and the subsequent `.limit(50)` call would be a type error.

## Example B — classmethod factory returning Self in subclasses

```python
from __future__ import annotations
from typing import Self
import json

class Config:
    def __init__(self, data: dict[str, object]) -> None:
        self.data = data

    @classmethod
    def from_json(cls, path: str) -> Self:
        with open(path) as f:
            return cls(json.load(f))     # OK — cls() produces Self

    def get(self, key: str) -> object:
        return self.data[key]

class AppConfig(Config):
    def app_name(self) -> str:
        return str(self.data.get("app_name", "unknown"))

# The classmethod preserves the subclass type:
app = AppConfig.from_json("config.json")
reveal_type(app)                         # AppConfig, not Config
app.app_name()                           # OK — checker knows this is AppConfig

# Returning a hardcoded base type instead of Self is an error:
class BadConfig:
    @classmethod
    def from_json(cls, path: str) -> Self:
        return Config({})                    # error — Config is not Self

# --- Without Self (the old TypeVar pattern): ---
from typing import TypeVar
T = TypeVar("T", bound="ConfigOld")

class ConfigOld:
    def __init__(self, data: dict[str, object]) -> None:
        self.data = data

    @classmethod
    def from_json(cls: type[T], path: str) -> T:   # verbose
        with open(path) as f:
            return cls(json.load(f))
```

The TypeVar pattern achieves the same result but requires an extra top-level binding and a `type[T]` annotation on `cls`. `Self` eliminates this boilerplate.

## Common type-checker errors and how to read them

### mypy: `error: The erased type of self "X" is not a supertype of its class "Y"`

This typically appears when `Self` is used in a method signature but the return expression does not match the enclosing class. Ensure you are returning `self` or an instance constructed via `cls(...)`.

### pyright: `Expression of type "Base" is incompatible with return type "Self@Derived"`

You returned a hardcoded base-class instance instead of using `self` or `cls()`. The checker requires the returned value to be an instance of the caller's class, not a parent.

### mypy: `error: "Self" is not valid in this context`

`Self` was used outside a class body — for example, in a module-level function or a type alias. Move the annotation inside a class.

### pyright: `"Self" is not allowed in this context`

Same cause as the mypy variant. `Self` is only meaningful inside class or instance method signatures.

## Use-case cross-references

- [-> UC-07](../usecases/07-api-contracts-callable.md) — Fluent interfaces and builder patterns that preserve subclass types through method chains.
- [-> UC-09](../usecases/09-configuration-builder.md) — Factory classmethods in inheritance hierarchies.

## Source anchors

- [PEP 673 — Self Type](https://peps.python.org/pep-0673/)
- [typing module — Self](https://docs.python.org/3/library/typing.html#typing.Self)
- [typing_extensions backport](https://typing-extensions.readthedocs.io/en/latest/#Self)
- [mypy docs — Self type](https://mypy.readthedocs.io/en/stable/generics.html#self-type)
