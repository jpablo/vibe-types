# Abstract Base Classes

> **Since:** Python 3.0 (PEP 3119) | **Typing integration:** Python 3.5+ (PEP 484)

## What it is

An Abstract Base Class (ABC) defines a nominal interface — a contract that subclasses must fulfill by implementing all declared abstract methods and properties. Unlike Protocols (which use structural subtyping), ABCs require explicit inheritance: a class must declare `class MyImpl(MyABC):` to be considered a subtype.

The `abc` module provides the `ABC` convenience base class and the `@abstractmethod` decorator. Marking a method as `@abstractmethod` means two things: (1) the class cannot be instantiated directly — attempting `MyABC()` raises `TypeError` at runtime, and (2) the type checker flags any concrete subclass that fails to implement the abstract method.

ABCs can also define concrete (non-abstract) methods that subclasses inherit, making them useful as partial implementations — unlike Protocols, which are purely structural contracts. The `collections.abc` module provides a rich library of pre-built ABCs (`Iterable`, `Mapping`, `Sequence`, etc.) that the type checker understands.

## What constraint it enforces

**Subclasses must implement all abstract methods and properties before they can be instantiated. The type checker rejects both direct instantiation of an ABC and subclasses with missing implementations.**

Specifically:

- A class with any unimplemented abstract methods cannot be instantiated — both the type checker and the runtime reject it.
- The type checker verifies that overriding methods have compatible signatures (parameter types, return type).
- `@abstractmethod` can be combined with `@property`, `@classmethod`, and `@staticmethod`.
- ABCMeta's `register()` can declare a "virtual subclass" that satisfies `isinstance()` at runtime but is *not* checked by the type checker for method completeness.

## Minimal snippet

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def perimeter(self) -> float: ...

class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return 3.14159 * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * 3.14159 * self.radius

Shape()                     # error: Cannot instantiate abstract class "Shape"
Circle(5.0)                 # OK

class BadShape(Shape):
    def area(self) -> float:
        return 0.0
    # perimeter() is missing

BadShape()                  # error: Cannot instantiate abstract class "BadShape"
                            #   with abstract method "perimeter"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Protocol** [-> catalog/09](T07-structural-typing.md) | Protocols check structure; ABCs check inheritance. A class can satisfy a Protocol *and* inherit from an ABC. Use Protocol when you want decoupling; use ABC when you want a shared implementation base. |
| **Generics / TypeVar** [-> catalog/07](T04-generics-bounds.md) | ABCs can be generic: `class Repository(ABC, Generic[T])`. The TypeVar tracks the entity type across abstract methods. |
| **Dataclasses** [-> catalog/06](T06-derivation.md) | A dataclass can inherit from an ABC and provide concrete implementations of abstract methods. The dataclass machinery generates `__init__` and friends; the ABC enforces the method contract. |
| **Final / ClassVar** [-> catalog/12](T32-immutability-markers.md) | An ABC method can be `@final` to prevent further overriding in deeper subclasses. `ClassVar` attributes in an ABC are shared class-level state. |
| **Self type** [-> catalog/16](T33-self-type.md) | Abstract methods returning `Self` ensure subclass methods return the correct subtype. |

## Gotchas and limitations

1. **`register()` bypasses type checking.** ABCMeta's `register()` makes a class a virtual subclass for `isinstance()` at runtime, but the type checker does not verify that the registered class implements the abstract methods.

   ```python
   from abc import ABC, abstractmethod

   class Printable(ABC):
       @abstractmethod
       def to_string(self) -> str: ...

   class Widget:
       pass                                # no to_string() method

   Printable.register(Widget)
   isinstance(Widget(), Printable)          # True at runtime
   # But type checker does NOT treat Widget as Printable
   ```

2. **`@abstractmethod` must be the innermost decorator.** When combining with `@property`, `@classmethod`, or `@staticmethod`, `@abstractmethod` must come last (closest to the `def`).

   ```python
   class Config(ABC):
       @property
       @abstractmethod
       def name(self) -> str: ...          # OK: @property wraps @abstractmethod

       @abstractmethod
       @property                           # error: wrong order
       def value(self) -> int: ...
   ```

3. **ABCs with all concrete methods can still be abstract.** An ABC subclass of another ABC inherits abstract methods. If it does not override them, it remains abstract even if it adds new concrete methods.

4. **No structural checking at all.** Unlike Protocol, an ABC does not accept classes that happen to have the right methods but do not inherit. This means you cannot pass an `io.BytesIO` where an ABC-based `ReadableStream` is expected unless `BytesIO` actually inherits from it.

5. **Multiple inheritance diamond with ABCs.** When multiple ABCs define the same abstract method, the concrete class must implement it once, but the MRO (Method Resolution Order) must be consistent. Conflicting MROs cause `TypeError` at class definition time.

6. **Abstract `__init__` is unusual.** While you *can* mark `__init__` as `@abstractmethod`, it is rarely useful — subclasses almost always define their own `__init__`, and the signatures typically differ.

## Beginner mental model

Think of an ABC as a contract with blanks. The ABC says "any subclass must fill in these blanks" — the blanks are the abstract methods. You cannot use the contract (instantiate the class) until all blanks are filled. The type checker enforces the contract at check time, and Python enforces it again at runtime when you try to call the constructor.

The key difference from Protocol is that ABC requires *signing the contract* (inheriting from the ABC). Protocol just checks whether you happen to have all the right methods, without caring whether you signed anything.

## Example A — Repository interface with required CRUD methods

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar("T")
ID = TypeVar("ID")

class Repository(ABC, Generic[T, ID]):
    """Abstract repository — subclasses must implement all CRUD operations."""

    @abstractmethod
    def get(self, id: ID) -> T | None: ...

    @abstractmethod
    def list_all(self) -> list[T]: ...

    @abstractmethod
    def save(self, entity: T) -> None: ...

    @abstractmethod
    def delete(self, id: ID) -> bool: ...

    # Concrete method — shared by all implementations
    def exists(self, id: ID) -> bool:
        return self.get(id) is not None

# Concrete implementation
class InMemoryUserRepo(Repository[dict[str, object], str]):
    def __init__(self) -> None:
        self._store: dict[str, dict[str, object]] = {}

    def get(self, id: str) -> dict[str, object] | None:
        return self._store.get(id)

    def list_all(self) -> list[dict[str, object]]:
        return list(self._store.values())

    def save(self, entity: dict[str, object]) -> None:
        self._store[str(entity["id"])] = entity

    def delete(self, id: str) -> bool:
        return self._store.pop(id, None) is not None

repo: Repository[dict[str, object], str] = InMemoryUserRepo()  # OK
repo.save({"id": "1", "name": "Alice"})                        # OK
repo.exists("1")                                                # OK — uses concrete method

# Incomplete implementation
class BrokenRepo(Repository[str, int]):
    def get(self, id: int) -> str | None:
        return None
    # list_all, save, delete are missing

BrokenRepo()                # error: Cannot instantiate abstract class "BrokenRepo"
                            #   with abstract methods "delete", "list_all", "save"
```

## Example B — Abstract property enforcing subclass provides configuration

```python
from abc import ABC, abstractmethod
from typing import ClassVar

class BaseService(ABC):
    """Services must declare their name and timeout via abstract properties."""

    max_instances: ClassVar[int] = 10           # shared, not abstract

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Each subclass must provide its service name."""
        ...

    @property
    @abstractmethod
    def timeout_seconds(self) -> float:
        """Each subclass must declare its timeout."""
        ...

    def describe(self) -> str:
        return f"{self.service_name} (timeout={self.timeout_seconds}s)"

class AuthService(BaseService):
    @property
    def service_name(self) -> str:
        return "auth"

    @property
    def timeout_seconds(self) -> float:
        return 5.0

class IncompleteService(BaseService):
    @property
    def service_name(self) -> str:
        return "incomplete"
    # timeout_seconds is missing

AuthService()                # OK
AuthService().describe()     # OK — returns "auth (timeout=5.0s)"
IncompleteService()          # error: Cannot instantiate abstract class
                             #   "IncompleteService" with abstract method "timeout_seconds"

# Abstract classmethod
class Deserializable(ABC):
    @classmethod
    @abstractmethod
    def from_json(cls, data: str) -> "Deserializable": ...

class User(Deserializable):
    def __init__(self, name: str) -> None:
        self.name = name

    @classmethod
    def from_json(cls, data: str) -> "User":
        import json
        return cls(json.loads(data)["name"])

User.from_json('{"name": "Alice"}')             # OK
Deserializable.from_json('{}')                   # error: Cannot instantiate abstract class
```

## Common type-checker errors and how to read them

### mypy: `Cannot instantiate abstract class "X" with abstract method "Y"`

Trying to create an instance of a class that has unimplemented abstract methods.

```
error: Cannot instantiate abstract class "BadShape" with abstract method "perimeter"
```

**Fix:** Implement all abstract methods listed in the error, or if the class is meant to be abstract itself, do not instantiate it directly.

### pyright: `"X" cannot be instantiated — it is abstract`

Pyright's equivalent message, sometimes with a list of missing methods.

```
error: Cannot instantiate abstract class "BrokenRepo"
  "BrokenRepo" is abstract because it does not implement "list_all", "save", "delete"
```

**Fix:** Same — implement the listed methods.

### mypy: `Return type "X" of "method" incompatible with return type "Y" in supertype "ABC"`

The overriding method's return type is not compatible with the abstract method's declared return type.

```
error: Return type "str" of "area" incompatible with return type "float"
       in supertype "Shape"
```

**Fix:** Ensure the override's return type is the same or a subtype of the abstract method's return type.

### mypy: `Signature of "method" incompatible with supertype "ABC"`

The overriding method changes the parameter types in an incompatible way.

```
error: Signature of "get" incompatible with supertype "Repository"
  Superclass:   def get(self, id: ID) -> T | None
  Subclass:     def get(self, id: str, default: str = ...) -> str
```

**Fix:** The override must accept at least the same parameter types as the abstract declaration. Adding required parameters that the base does not have breaks the contract.

## Use-case cross-references

- [-> UC-04](../usecases/UC04-generic-constraints.md) — ABCs define plug-in interfaces where all implementations must provide a complete method set.
- [-> UC-05](../usecases/UC05-structural-contracts.md) — Abstract properties enforce that subclasses declare configuration values at the type level.

## Source anchors

- [PEP 3119 — Introducing Abstract Base Classes](https://peps.python.org/pep-3119/)
- [`abc` module docs](https://docs.python.org/3/library/abc.html)
- [`collections.abc` module docs](https://docs.python.org/3/library/collections.abc.html)
- [typing spec: Abstract methods](https://typing.readthedocs.io/en/latest/spec/class-compat.html)
- [mypy docs: Abstract base classes](https://mypy.readthedocs.io/en/stable/class_basics.html#abstract-base-classes-and-multiple-inheritance)
