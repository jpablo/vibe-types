# Generic Constraints

## The constraint

Generic functions and classes accept only types satisfying declared bounds. A `TypeVar` with a bound or constraint limits which types may be substituted, preventing misuse while preserving type information through the call.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Generics / TypeVar | Parameterize functions and classes over types | [-> catalog/07](../catalog/T04-generics-bounds.md) |
| Protocol | Define structural bounds that generics can require | [-> catalog/09](../catalog/T07-structural-typing.md) |
| ABC | Define nominal bounds through abstract base classes | [-> catalog/10](../catalog/T05-type-classes.md) |
| Variance | Control subtype relationships for generic containers | [-> catalog/18](../catalog/T08-variance-subtyping.md) |

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

## When to Use

Use generic constraints when:

1. **A function needs to invoke members that not all types have** — require `TypeVar("T", bound=Measurable)` instead of `isinstance` checks.
2. **Type safety should scale with reuse** — constrain once, then any caller gets full type checking without duplication.
3. **You need to preserve the full type through transformations** — `find[T: Animal](items: list[T])` returns `T`, narrowing at the call site.
4. **The constraint captures a real domain concept** — name it (`Comparable`, `Serializable`) when it appears in multiple places.

```python
# Before: runtime check, Any return
def loudest(items: list[any], threshold: int) -> any:
    for x in items:
        if hasattr(x, "speak") and len(x.speak()) >= threshold:
            return x
    return None

# After: compile-time constraint, preserves type
T = TypeVar("T", bound=Animal)
def loudest(items: list[T], threshold: int) -> T | None:
    for x in items:
        if len(x.speak()) >= threshold:
            return x
    return None
```

## When Not to Use

Avoid generic constraints when:

1. **The constraint is too narrow for real use** — `T: User` is less reusable than `T: {name: str}`.
2. **You're constraining only to please the type checker** — if the function never uses the constrained members, drop the constraint.
3. **A simpler type works** — `def first[T](arr: list[T]) -> T` needs no constraint.
4. **You need runtime polymorphism over many unrelated types** — prefer overloads or a union type.

```python
# Over-constrained: only works for exact Dog type
T = TypeVar("T", bound=Dog)
def greet_pet(pet: T) -> str:
    return f"Hello, {pet.name}"

# Better: minimal Protocol
class HasName(Protocol):
    name: str

T = TypeVar("T", bound=HasName)
def greet_pet(pet: T) -> str:
    return f"Hello, {pet.name}"

# Unnecessary constraint
def double(x: int) -> int:
    return x * 2
```

## Antipatterns When Using Constraints

### Antipattern A — Constrained but unused

The constraint adds no value if the generic function does not use the required members.

```python
# Unused constraint
T = TypeVar("T", bound=Serializable)
def log_obj(x: T) -> None:
    print("logged")  # never calls to_json()

# Remove the constraint
T = TypeVar("T")
def log_obj(x: T) -> None:
    print("logged")
```

### Antipattern B — Overly specific type bound

Using a concrete type as the bound reduces reuse and defeats the purpose of generics.

```python
# Overly specific
T = TypeVar("T", bound=UserProfile)
def save_user(u: T) -> None:
    db.insert(u)

# Better: Protocol bound
class HasId(Protocol):
    id: int

T = TypeVar("T", bound=HasId)
def save_user(u: T) -> None:
    db.insert(u)
```

### Antipattern C — ABC when Protocol suffices

Requiring nominal inheritance when a structural bound is sufficient.

```python
# Over-constrained: requires explicit inheritance
class CanSerialize(ABC):
    @abstractmethod
    def to_dict(self) -> dict: ...

T = TypeVar("T", bound=CanSerialize)
def dump_all(items: list[T]) -> list[dict]:
    return [item.to_dict() for item in items]

# Third-party dict cannot be used even though it has to_dict()

# Better: Protocol allows duck typing
class ToDictable(Protocol):
    def to_dict(self) -> dict: ...

T = TypeVar("T", bound=ToDictable)
def dump_all(items: list[T]) -> list[dict]:
    return [item.to_dict() for item in items]
```

### Antipattern D — Complex union for simple cases

Using multi-type constraints when a single Protocol suffices.

```python
# Over-engineered: enumerates types
T = TypeVar("T", int, float, str)
def log_value(v: T) -> None:
    print(v)

# Simpler: no constraint needed for common operations
def log_value(v: any) -> None:
    print(v)
```

## Antipatterns with Other Techniques (Where Constraints Help)

### Antipattern A — Runtime type guards instead of constraints

Using `isinstance` or `hasattr` at runtime when a constraint would enforce the shape at compile time.

```python
# Runtime guards
def process(x: any) -> int:
    if not isinstance(x, (int, float)):
        raise TypeError("must be numeric")
    return int(x * 2)

# Compile-time constraint
def process(x: int | float) -> int:
    return int(x * 2)
```

### Antipattern B — `any` to bypass type errors

Using `any` instead of expressing the required shape with constraints.

```python
# Bad: any
def get_id(obj: dict[str, any]) -> str:
    return obj["id"]  # no type checking

# Better: constrained
class HasId(Protocol):
    id: str

T = TypeVar("T", bound=HasId)
def get_id(obj: T) -> str:
    return obj.id
```

### Antipattern C — Duplicate functions for each type

Writing separate functions instead of one generic with a constraint.

```python
# Duplication
def find_user(users: list[User], uid: str) -> User | None:
    return next((u for u in users if u.id == uid), None)

def find_product(products: list[Product], pid: str) -> Product | None:
    return next((p for p in products if p.id == pid), None)

# Single generic
class HasId(Protocol):
    id: str

T = TypeVar("T", bound=HasId)
def find(items: list[T], key: str) -> T | None:
    return next((x for x in items if x.id == key), None)
```

### Antipattern D — Narrow return types that lose information

Returning a base type instead of preserving the concrete subtype through the generic.

```python
# Loses type information
def clone(obj: Animal) -> Animal:
    return obj.__class__()  # returns Animal, not Dog or Cat

# Preserves type with bound
T = TypeVar("T", bound=Animal)
def clone(obj: T) -> T:
    return obj.__class__()  # returns T (Dog or Cat)

# Even better with default (PEP 695)
def clone[T: Animal](obj: T) -> T:
    return obj
```

## Source anchors

- [PEP 484 — TypeVar](https://peps.python.org/pep-0484/#generics)
- [PEP 544 — Protocols: Structural subtyping](https://peps.python.org/pep-0544/)
- [PEP 695 — Type Parameter Syntax](https://peps.python.org/pep-0695/)
- [mypy — Generics](https://mypy.readthedocs.io/en/stable/generics.html)
- [mypy — Protocols and structural subtyping](https://mypy.readthedocs.io/en/stable/protocols.html)
