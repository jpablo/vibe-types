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
    color: str

    def set_color(self, color: str) -> Self:
        self.color = color
        return self              # OK

class Circle(Shape):
    radius: float

    def set_radius(self, r: float) -> Self:
        self.radius = r
        return self              # OK

reveal_type(Circle().set_color("red"))  # Circle, not Shape

# Without Self, a hardcoded return type breaks subclasses:
class BadShape:
    color: str

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
| **TypeVar (bound)** [-> catalog/07](T04-generics-bounds.md) | `Self` replaces the `T = TypeVar("T", bound="Base")` pattern for return-type polymorphism. TypeVar is still needed for unrelated generic parameters. |
| **Callable** [-> catalog/11](T22-callable-typing.md) | A `Callable[..., Self]` parameter type describes a factory callback that must produce an instance of the current class. |
| **dataclass** [-> catalog/06](T06-derivation.md) | `Self` can appear in `@dataclass` methods and `__post_init__` return annotations, though the constructor itself is generated. |
| **Protocol** [-> catalog/09](T07-structural-typing.md) | `Self` in a Protocol method means each implementor must return its own concrete type, not the Protocol. |

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

- [-> UC-07](../usecases/UC07-callable-contracts.md) — Fluent interfaces and builder patterns that preserve subclass types through method chains.
- [-> UC-09](../usecases/UC09-builder-config.md) — Factory classmethods in inheritance hierarchies.

## When to use it

Use `Self` when:

- **Implementing fluent/builder APIs with inheritance**: Methods should return the concrete subclass type to maintain chainability.
  ```python
  class Builder:
      def add(self, x: int) -> Self:
          return self
  class Derived(Builder):
      def custom(self) -> Self:
          return self
  # Derived().add(1).custom() works only with Self return type
  ```

- **Defining clone/copy methods in base classes**: Subclasses must return their own type.
  ```python
  class Entity:
from typing import Self


class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def copy(self) -> Self:
from typing import Any, Self


class Model:
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        return cls(**d)
        new.x = x
        return new
  ```python
  class Point:
      def with_x(self, x: int) -> Self:
from typing_extensions import Self

# ❌ Unnecessary
class Leaf:
    def process(self) -> Self:
        return self
# ✅ Clearer
class Leaf:
    def process(self) -> "Leaf":
        return self
      @classmethod
      def from_dict(cls, d: dict) -> Self:
from typing import Self


class Result:
    def __init__(self, value: int) -> None:
        self._value = value


# ❌ Wrong
class BuilderWrong:
    def __init__(self) -> None:
        self._value: int = 0

    def build(self) -> Self:
        return Result(self._value)  # error


# ✅ Correct
class BuilderCorrect:
    def __init__(self) -> None:
        self._value: int = 0

    def build(self) -> Result:
        return Result(self._value)
  ```python
  # ❌ Unnecessary
  class Leaf:
from typing import Self

# ❌ Misleading — returns hardcoded Base instead of self
class Base:
    def modify(self) -> Self:
        self._dirty = True
        return Base()  # error: Returns Base, not Self

class Derived(Base):
    pass

d = Derived()
result = d.modify()
# result is Base at runtime but typed as Derived — runtime type mismatch

# ✅ Correct — returns self, preserving the actual subclass type
class BaseCorrect:
    _dirty: bool
from typing import Self
from typing import override

class Base:
    def clone(self) -> Self:
        return self

class BadDerived(Base):
    @override
    def clone(self) -> Base:  # ❌ Too wide — loses Derived type
        return Base()

class GoodDerived(Base):
    @override
    def clone(self) -> Self:  # ✅ Preserves polymorphic return
        return self
from typing import Self, override

class Person:
    def __init__(self, name: str):
        self.name = name

    def get_family(self) -> Self:  # ❌ Misleading
        return Person(f"{self.name} Family")

class Employee(Person):
    def __init__(self, name: str, company: str):
        super().__init__(name)
        self.company = name
class Family:
    def __init__(self, person: "Person") -> None:
        self.person = person


class Person:
    def get_family(self) -> "Family":
        return Family(self)
class Base:
    @staticmethod
    def create() -> Self:  # ❌ Self not valid in static context
        return Base()
  ```

- **Returning wrapped/proxy instances**: If you return a different object (proxy, wrapper, view), `Self` is misleading.
  ```python
  # expect-error
  # ❌ Misleading
  class Resource:
      def as_readonly(self) -> Self:
          return ReadOnlyProxy(self)  # error: Proxy ≠ Self
  # ✅ Correct
  class Resource:
      def as_readonly(self) -> "ReadOnlyResource":
          return ReadOnlyProxy(self)
  ```

## Antipatterns when using Self

### Returning hardcoded base type instead of `self`

# ❌ Old pattern — verbose, error-prone
from typing import TypeVar

T = TypeVar("T", bound="Builder")

class Builder:
    def __init__(self) -> None:
        self._name: str = ""

    def name(self, n: str) -> T:  # T is ambiguous here
        self._name = n
        return self# checker can't verify

class SpecialBuilder(Builder):
    def special(self) -> "SpecialBuilder":
        return self

### Overriding with incompatible concrete type

```python
class Base:
    def clone(self) -> Self:
        return self

class BadDerived(Base):
    def clone(self) -> Base:  # ❌ Too wide — loses Derived type
        return Base()

class GoodDerived(Base):
    def clone(self) -> Self:  # ✅ Preserves polymorphic return
        return self
```

### Overusing `Self` in methods that return aggregates

```python
class Person:
    def get_family(self) -> Self:  # ❌ Misleading
        return Person(f"{self.name} Family")

class Employee(Person):
    def get_family(self) -> Self:
# ❌ Without Self
class Base:
    def set_a(self, a: str) -> "Base":
        self._a = a
        return self

class Derived(Base):
    def set_d(self, d: str) -> "Derived":
        self._d = d
        return self

d = Derived()
d.set_d("x").set_a("y").set_d("z")  # error: set_a returns Base

```python
class Base:
    @staticmethod
    def create() -> Self:  # ❌ Self not valid in static context
# ✅ With Self
from typing import Self

class Base:
    _a: str

    def __init__(self) -> None:
        self._a = ""

    def set_a(self, a: str) -> Self:
        self._a = a
        return self

class Derived(Base):
    _d: str

    def __init__(self) -> None:
        super().__init__()
        self._d = ""

    def set_d(self, d: str) -> Self:
        self._d = d
# ❌ Protocol returns base type
from abc import ABC, abstractmethod
from typing import override

class Cloneable(ABC):
    @abstractmethod
    def clone(self) -> "Cloneable":
        pass

class User(Cloneable):
    @override
    def clone(self) -> Cloneable:
        return User()

class AdminUser(User):
    @override
    def clone(self) -> Cloneable:
        return AdminUser()

admin = AdminUser()
copy = admin.clone()
# copy is typed as Cloneable, not AdminUser
        return self# checker can't verify

class SpecialBuilder(Builder):
    def special(self) -> "SpecialBuilder":
        return self
```

**Fixed with Self:**

```python
# ✅ Clean, type-safe
from typing import Self

class Builder:
    def __init__(self) -> None:
        self._name: str = ""

    def name(self, n: str) -> Self:
        self._name = n
        return self

class SpecialBuilder(Builder):
    def special(self) -> Self:
        return self
```

### Losing subclass type in method chains

**Antipattern:** Base class methods return base type, breaking subclass chains.

```python
# expect-error
# ❌ Without Self
class Base:
    def set_a(self, a: str) -> "Base":
        self._a = a
        return self

class Derived(Base):
    def set_d(self, d: str) -> "Derived":
        self._d = d
        return self

d = Derived()
d.set_d("x").set_a("y").set_d("z")  # error: set_a returns Base
```
# ✅ Self-typed factory
from typing import Self
from typing_extensions import override

class Model:
    def __init__(self, value: int) -> None:
        self.value = value

    @classmethod
    def specialized(cls, value: int, extra: str) -> Self:
        obj = cls(value)
        if cls == Model:
            raise TypeError("Must be called on subclass")
        return obj  # typed as Self

class SpecializedModel(Model):
    @override
    @classmethod
    def specialized(cls, value: int, extra: str) -> Self:
        obj = cls(value)
        obj.extra = extra
        return obj

model = SpecializedModel.specialized(1, "x")
# model is typed as SpecializedModel, method knows its own type
**Antipattern:** Clone/merge protocols return protocol type instead of concrete type.

```python
# ❌ Protocol returns base type
from abc import ABC, abstractmethod

class Cloneable(ABC):
    @abstractmethod
    def clone(self) -> "Cloneable":
        pass

class User(Cloneable):
    def clone(self) -> Cloneable:
        return User()

class AdminUser(User):
    def clone(self) -> Cloneable:
        return AdminUser()

admin = AdminUser()
copy = admin.clone()
# copy is typed as Cloneable, not AdminUser
```

**Fixed with Self:**

```python
# ✅ Self-typed protocol
from typing import Self, Protocol

class Cloneable(Protocol):
    def clone(self) -> Self: ...

class User:
    def clone(self) -> Self:
        return self.__class__()

class AdminUser(User):
    pass

admin = AdminUser()
copy = admin.clone()
# copy is typed as AdminUser
```

### Manual type guards instead of `Self`

**Antipattern:** Extra factory functions with manual type guards outside the class.

```python
# ❌ External factory + guard
class Model:
    def __init__(self, value: int) -> None:
        self.value = value

class SpecializedModel(Model):
    def __init__(self, value: int, extra: str) -> None:
        super().__init__(value)
        self.extra = extra

def make_specialized(value: int, extra: str) -> SpecializedModel:
    return SpecializedModel(value, extra)

model = make_specialized(1, "x")
# Works, but factory is separate from class
```

**Fixed with Self:**

```python
# ✅ Self-typed factory
from typing import Self

class Model:
    def __init__(self, value: int) -> None:
        self.value = value

    @classmethod
    def specialized(cls, value: int, extra: str) -> Self:
        obj = cls(value)
        if cls == Model:
            raise TypeError("Must be called on subclass")
        return obj  # typed as Self

class SpecializedModel(Model):
    @classmethod
    def specialized(cls, value: int, extra: str) -> Self:
        obj = cls(value)
        obj.extra = extra
        return obj

model = SpecializedModel.specialized(1, "x")
# model is typed as SpecializedModel, method knows its own type
```

## Source anchors

- [PEP 673 — Self Type](https://peps.python.org/pep-0673/)
- [typing module — Self](https://docs.python.org/3/library/typing.html#typing.Self)
- [typing_extensions backport](https://typing-extensions.readthedocs.io/en/latest/#Self)
- [mypy docs — Self type](https://mypy.readthedocs.io/en/stable/generics.html#self-type)
