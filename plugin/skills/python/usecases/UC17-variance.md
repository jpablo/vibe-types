# Variance

## The constraint

Variance determines whether `Container[Sub]` can be used where `Container[Super]` is expected. Python's type system supports covariant, contravariant, and invariant type parameters through `TypeVar` declarations. Python 3.12+ infers variance automatically from usage in the new generic syntax.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Variance / subtyping | Covariant, contravariant, and invariant type parameters | [-> catalog/08](../catalog/T08-variance-subtyping.md) |
| Generics / TypeVar | Parameterize classes and functions over types with variance control | [-> catalog/04](../catalog/T04-generics-bounds.md) |

## Patterns

### A — Covariant type parameter (read-only container)

A read-only container can be covariant: `Box[Dog]` is usable where `Box[Animal]` is expected.

```python
from typing import TypeVar, Generic

class Animal: ...
class Dog(Animal): ...

T_co = TypeVar("T_co", covariant=True)

class FrozenBox(Generic[T_co]):
    def __init__(self, value: T_co) -> None:
        self._value = value

    def get(self) -> T_co:
        return self._value

def show_animal(box: FrozenBox[Animal]) -> None:
    print(box.get())

dog_box: FrozenBox[Dog] = FrozenBox(Dog())
show_animal(dog_box)   # OK — covariant: FrozenBox[Dog] <: FrozenBox[Animal]
```

### B — Contravariant type parameter (write-only / consumer)

A consumer that only accepts values can be contravariant: `Handler[Animal]` is usable where `Handler[Dog]` is expected.

```python
from typing import TypeVar, Generic

T_contra = TypeVar("T_contra", contravariant=True)

class Handler(Generic[T_contra]):
    def handle(self, item: T_contra) -> None:
        print(f"Handling {item}")

def process_dog(handler: Handler[Dog]) -> None:
    handler.handle(Dog())

animal_handler: Handler[Animal] = Handler()
process_dog(animal_handler)  # OK — contravariant: Handler[Animal] <: Handler[Dog]
```

### C — Invariant type parameter (mutable container)

A mutable container must be invariant: neither `list[Dog]` nor `list[Animal]` substitutes for the other.

```python
def append_animal(animals: list[Animal]) -> None:
    animals.append(Animal())

dogs: list[Dog] = [Dog()]
# append_animal(dogs)  # error: list[Dog] not assignable to list[Animal]
# Correct: list is invariant over its element type
```

### D — Python 3.12+ automatic variance inference

The new `type` parameter syntax infers variance from usage, removing the need for explicit `covariant=True`.

```python
# Python 3.12+ syntax
class ReadOnlyBox[T]:
    def __init__(self, value: T) -> None:
        self._value = value

    def get(self) -> T:
        return self._value

# T is inferred as covariant because it only appears in return position.
# No need for TypeVar("T_co", covariant=True).
```

### Untyped Python comparison

Without type annotations, variance violations are invisible.

```python
# No types — checker sees nothing
def append_animal(animals):
    animals.append(Animal())

dogs = [Dog()]
append_animal(dogs)  # silently adds Animal to a list expected to contain only Dogs
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| **Explicit TypeVar variance** | Clear intent; works in all Python 3.x with typing | Verbose; easy to declare wrong variance |
| **3.12+ inferred variance** | Zero boilerplate; compiler-derived from usage | Requires Python 3.12+; inference may surprise if usage changes |
| **Invariant (default)** | Safest; prevents unsound substitution | May be too restrictive for read-only or write-only containers |

## When to use which feature

- **Default to invariant** — mutable containers, most generic classes.
- **Use covariant** for read-only containers, iterators, and producers — types where `T` only appears in return positions.
- **Use contravariant** for consumers, handlers, and callbacks — types where `T` only appears in parameter positions.
- **Use 3.12+ syntax** in new codebases to let the checker infer variance automatically.

## Source anchors

- [PEP 484 — Covariance and contravariance](https://peps.python.org/pep-0484/#covariance-and-contravariance)
- [PEP 695 — Type parameter syntax (3.12+)](https://peps.python.org/pep-0695/)
- [mypy — Variance](https://mypy.readthedocs.io/en/stable/generics.html#variance-of-generic-types)
- [typing spec — Variance](https://typing.readthedocs.io/en/latest/spec/generics.html#variance)
