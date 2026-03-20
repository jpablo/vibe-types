# Generic Constraints

## The constraint

Generic functions and classes accept only types satisfying declared bounds. A `TypeVar` with a bound or constraint limits which types may be substituted, preventing misuse while preserving type information through the call.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Generics / TypeVar | Parameterize functions and classes over types | [-> catalog/07](../catalog/07-generics-typevar.md) |
| Protocol | Define structural bounds that generics can require | [-> catalog/09](../catalog/09-protocol-structural-subtyping.md) |
| ABC | Define nominal bounds through abstract base classes | [-> catalog/10](../catalog/10-abc-abstract-classes.md) |
| Variance | Control subtype relationships for generic containers | [-> catalog/18](../catalog/18-generic-classes-variance.md) |

## Patterns

### A — TypeVar with bound

Restrict the type variable to a specific class hierarchy. The bound is an upper limit.

```python
from typing import TypeVar

class Animal:
    def speak(self) -> str:
        return "..."

class Dog(Animal):
    def speak(self) -> str:
        return "Woof"

class Cat(Animal):
    def speak(self) -> str:
        return "Meow"

T = TypeVar("T", bound=Animal)

def loudest(a: T, b: T) -> T:
    return a if len(a.speak()) >= len(b.speak()) else b  # OK — .speak() available

loudest(Dog(), Cat())        # OK — both are Animal subtypes
loudest(Dog(), "not animal") # error: "str" is not compatible with bound "Animal"
```

### B — TypeVar with constraints

Restrict the type variable to an exact set of allowed types (not their subtypes).

```python
from typing import TypeVar

T = TypeVar("T", int, float)

def add(a: T, b: T) -> T:
    return a + b             # OK — both int and float support +

add(1, 2)                   # OK — T is int
add(1.0, 2.5)               # OK — T is float
add("a", "b")               # error: Value of type variable "T" cannot be "str"
```

### C — Protocol-bounded generics

Use a `Protocol` as the bound to require structural capabilities without nominal inheritance.

```python
from typing import TypeVar, Protocol

class Measurable(Protocol):
    def size(self) -> int: ...

M = TypeVar("M", bound=Measurable)

def largest(items: list[M]) -> M:
    return max(items, key=lambda x: x.size())  # OK — .size() guaranteed

class File:
    def __init__(self, name: str, bytes: int) -> None:
        self.name = name
        self.bytes = bytes
    def size(self) -> int:
        return self.bytes

class Folder:
    def __init__(self, count: int) -> None:
        self.count = count
    def size(self) -> int:
        return self.count

largest([File("a.txt", 100), File("b.txt", 200)])  # OK
largest([1, 2, 3])                                   # error: "int" has no "size" method
```

### D — ABC-bounded generics

Use an abstract base class as the bound to require nominal membership.

```python
from typing import TypeVar
from abc import ABC, abstractmethod

class Serializable(ABC):
    @abstractmethod
    def to_json(self) -> str: ...

S = TypeVar("S", bound=Serializable)

def save_all(items: list[S]) -> list[str]:
    return [item.to_json() for item in items]  # OK — to_json() guaranteed

class User(Serializable):
    def __init__(self, name: str) -> None:
        self.name = name
    def to_json(self) -> str:
        return f'{{"name": "{self.name}"}}'

class PlainDict:
    def to_json(self) -> str:
        return "{}"

save_all([User("Alice")])     # OK — User extends Serializable
save_all([PlainDict()])       # error: "PlainDict" is not a subtype of "Serializable"
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **TypeVar + bound** | Preserves the specific subtype through the call; flexible hierarchy | Requires an inheritance relationship or Protocol |
| **TypeVar + constraints** | Restricts to an exact set of types; simple to reason about | Does not accept subtypes of the listed types; list must be enumerated |
| **Protocol-bounded** | Structural: any type with matching methods qualifies; no inheritance needed | More complex to define; error messages can be harder to read |
| **ABC-bounded** | Nominal: only explicit subclasses qualify; intent is clear | Requires inheritance; less flexible than Protocol for third-party types |

## When to use which feature

- **TypeVar with bound** for the common case where you have a class hierarchy and want to preserve the specific subtype through a generic function.
- **TypeVar with constraints** when only a small, fixed set of types should be accepted (e.g., `int` and `float` but nothing else).
- **Protocol-bounded generics** when the constraint is behavioral ("has a `.size()` method") and you want to accept types you do not control without requiring them to inherit from your base.
- **ABC-bounded generics** when the constraint is organizational and you want to enforce that types explicitly opt in to a contract via inheritance.

## Source anchors

- [PEP 484 — TypeVar](https://peps.python.org/pep-0484/#generics)
- [PEP 544 — Protocols: Structural subtyping](https://peps.python.org/pep-0544/)
- [PEP 695 — Type Parameter Syntax](https://peps.python.org/pep-0695/)
- [mypy — Generics](https://mypy.readthedocs.io/en/stable/generics.html)
- [mypy — Protocols and structural subtyping](https://mypy.readthedocs.io/en/stable/protocols.html)
