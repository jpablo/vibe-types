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
    color: str = ""

    def set_color(self, color: str) -> Self:
        self.color = color
        return self              # OK

class Circle(Shape):
    radius: float = 0.0

    def set_radius(self, r: float) -> Self:
        self.radius = r
        return self              # OK

reveal_type(Circle().set_color("red"))  # Circle, not Shape

# Without Self, a hardcoded return type breaks subclasses:
class BadShape:
    color: str = ""

    def set_color(self, color: str) -> "BadShape":
        self.color = color
        return self

class BadCircle(BadShape):
    radius: float = 0.0

reveal_type(BadCircle().set_color("red"))  # BadShape — lost the subclass type
BadCircle().set_color("red").radius  # error: Cannot access attribute "radius" for class "BadShape"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **TypeVar (bound)** [-> T04](T04-generics-bounds.md) | `Self` replaces the `T = TypeVar("T", bound="Base")` pattern for return-type polymorphism. TypeVar is still needed for unrelated generic parameters. |
| **Callable** [-> T22](T22-callable-typing.md) | A `Callable[..., Self]` parameter type describes a factory callback that must produce an instance of the current class. |
| **dataclass** [-> T06](T06-derivation.md) | `Self` can appear in `@dataclass` methods and `__post_init__` return annotations, though the constructor itself is generated. |
| **Protocol** [-> T07](T07-structural-typing.md) | `Self` in a Protocol method means each implementor must return its own concrete type, not the Protocol. |

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
        return Config({})  # error: Type "Config" is not assignable to return type "Self@BadConfig"

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

- [-> UC07](../usecases/UC07-callable-contracts.md) — Fluent interfaces and builder patterns that preserve subclass types through method chains.
- [-> UC09](../usecases/UC09-builder-config.md) — Factory classmethods in inheritance hierarchies.

## When to use it

Use `Self` when:

- **Implementing fluent/builder APIs with inheritance** — methods should return the concrete subclass type to keep chains usable.

  ```python
  from typing import Self

  class Builder:
      def add(self, x: int) -> Self:
          return self

  class Derived(Builder):
      def custom(self) -> Self:
          return self

  d = Derived().add(1).custom()  # works only because add() returns Self
  ```

- **Defining clone/copy methods in base classes** — each subclass must get back its own type.

  ```python
  from typing import Self

  class Point:
      def __init__(self, x: int, y: int) -> None:
          self.x = x
          self.y = y

      def copy(self) -> Self:
          return type(self)(self.x, self.y)
  ```

- **Writing factory classmethods that subclasses inherit** — `cls(...)` already produces the right type; `Self` lets the annotation say so.

  ```python
  from typing import Self

  class Model:
      def __init__(self, value: int) -> None:
          self.value = value

      @classmethod
      def scaled(cls, value: int) -> Self:
          return cls(value * 2)
  ```

## When NOT to use it

- **Final/leaf classes with no subclasses** — `Self` and the class name are equivalent there; either spelling is fine, so don't refactor working code just to use `Self`.

- **Methods that return a wrapper, proxy, or view** — if you return a *different* object, `Self` is wrong and the checker will say so.

  ```python
  from typing import Self

  class ReadOnlyResource:
      def __init__(self, inner: "Resource") -> None:
          self._inner = inner

  class Resource:
      def as_readonly_bad(self) -> Self:
          return ReadOnlyResource(self)  # error: Type "ReadOnlyResource" is not assignable to return type "Self@Resource"

      def as_readonly(self) -> "ReadOnlyResource":
          return ReadOnlyResource(self)  # OK — name the actual return type
  ```

- **Methods that return aggregates** — a `Person` method that builds a `Family` should say so; `Self` would claim it returns another `Person`.

  ```python
  class Family:
      def __init__(self, person: "Person") -> None:
          self.person = person

  class Person:
      def __init__(self, name: str) -> None:
          self.name = name

      def get_family(self) -> "Family":
          return Family(self)
  ```

- **Static methods** — there is no `self` or `cls` to bind to, so `Self` is rejected.

  ```python
  from typing import Self

  class Base:
      @staticmethod
      def create() -> Self:  # error: "Self" is not valid in this context
          return Base()
  ```

## Antipatterns when using Self

### Returning a hardcoded base instance instead of `self`

The checker requires a `-> Self` method to produce an instance of the *caller's* class. Constructing the base class explicitly breaks that promise:

```python
from typing import Self

class Base:
    def __init__(self) -> None:
        self._dirty = False

    def modify(self) -> Self:
        self._dirty = True
        return Base()  # error: Type "Base" is not assignable to return type "Self@Base"
```

```python
# ✅ Correct — return self, preserving the actual subclass type
from typing import Self

class Base:
    def __init__(self) -> None:
        self._dirty = False

    def modify(self) -> Self:
        self._dirty = True
        return self
```

### Overriding `-> Self` with a wider concrete type

Widening the return type in an override is accepted by the checker (the override still returns a `Base`), but callers of the subclass silently lose the subclass type:

```python
from typing import Self, override

class Base:
    def clone(self) -> Self:
        return self

class BadDerived(Base):
    @override
    def clone(self) -> "Base":  # ❌ accepted, but too wide
        return Base()

class GoodDerived(Base):
    @override
    def clone(self) -> Self:    # ✅ preserves the polymorphic return
        return self

reveal_type(BadDerived().clone())   # Base — subclass type lost
reveal_type(GoodDerived().clone())  # GoodDerived
```

## Antipatterns fixed by Self

### Verbose TypeVar boilerplate

**Antipattern:** The pre-3.11 pattern works but needs a module-level TypeVar and an annotated `self`.

```python
# ❌ Old pattern — verbose, easy to get wrong
from typing import TypeVar

T = TypeVar("T", bound="Builder")

class Builder:
    def __init__(self) -> None:
        self._name: str = ""

    def name(self: T, n: str) -> T:
        self._name = n
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

**Antipattern:** Base class methods return the base type, breaking subclass chains.

```python
# ❌ Without Self
class Base:
    def __init__(self) -> None:
        self._a = ""

    def set_a(self, a: str) -> "Base":
        self._a = a
        return self

class Derived(Base):
    def __init__(self) -> None:
        super().__init__()
        self._d = ""

    def set_d(self, d: str) -> "Derived":
        self._d = d
        return self

d = Derived()
d.set_d("x").set_a("y").set_d("z")  # error: Cannot access attribute "set_d" for class "Base"
```

**Fixed with Self:**

```python
# ✅ With Self
from typing import Self

class Base:
    def __init__(self) -> None:
        self._a = ""

    def set_a(self, a: str) -> Self:
        self._a = a
        return self

class Derived(Base):
    def __init__(self) -> None:
        super().__init__()
        self._d = ""

    def set_d(self, d: str) -> Self:
        self._d = d
        return self

d = Derived()
d.set_d("x").set_a("y").set_d("z")  # OK — every step stays Derived
```

### Clone methods that return the base type

**Antipattern:** Clone interfaces return the interface type instead of the concrete type.

```python
# ❌ Interface returns base type
from abc import ABC, abstractmethod
from typing import override

class Cloneable(ABC):
    @abstractmethod
    def clone(self) -> "Cloneable": ...

class User(Cloneable):
    @override
    def clone(self) -> "Cloneable":
        return User()

class AdminUser(User):
    @override
    def clone(self) -> "Cloneable":
        return AdminUser()

admin = AdminUser()
copy = admin.clone()
reveal_type(copy)  # Cloneable, not AdminUser
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
reveal_type(copy)  # AdminUser
```

### External factory functions instead of `Self` classmethods

**Antipattern:** A separate factory function per subclass, detached from the class.

```python
# ❌ External factory per concrete class
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
# Works, but every new subclass needs its own factory function
```

**Fixed with Self:**

```python
# ✅ Self-typed factory classmethod — inherited by every subclass
from typing import Self

class Model:
    def __init__(self, value: int) -> None:
        self.value = value

    @classmethod
    def scaled(cls, value: int) -> Self:
        return cls(value * 2)

class SpecializedModel(Model):
    def describe(self) -> str:
        return f"value={self.value}"

model = SpecializedModel.scaled(1)
reveal_type(model)  # SpecializedModel — the factory follows the subclass
model.describe()    # OK
```

## Source anchors

- [PEP 673 — Self Type](https://peps.python.org/pep-0673/)
- [typing module — Self](https://docs.python.org/3/library/typing.html#typing.Self)
- [typing_extensions backport](https://typing-extensions.readthedocs.io/en/latest/#Self)
- [mypy docs — Self type](https://mypy.readthedocs.io/en/stable/generics.html#self-type)
