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

class Animal:
    pass

class Dog(Animal):
    pass

T_contra = TypeVar("T_contra", contravariant=True)

class Handler(Generic[T_contra]):
    def handle(self, item: T_contra) -> None:
        print(f"Handling {item}")

def process_dog(handler: Handler[Dog]) -> None:
    handler.handle(Dog())

animal_handler: Handler[Animal] = Handler()
process_dog(animal_handler)   # OK — contravariant: Handler[Animal] <: Handler[Dog]
```

### C — Invariant type parameter (mutable container)

A mutable container must be invariant: neither `list[Dog]` nor `list[Animal]` substitutes for the other.

```python
# expect-error
class Animal:
    pass

class Dog(Animal):
    pass

def append_animal(animals: list[Animal]) -> None:
    animals.append(Animal())

dogs: list[Dog] = [Dog()]
append_animal(dogs)  # error: list[Dog] not assignable to list[Animal]
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

```python ignore
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
| **Automatic inference (3.12+)** | No boilerplate; cannot mis-declare | Requires Python 3.12+; variance is implicit |
| **Invariant (default)** | Always sound | Blocks substitution even when it would be safe |

### Covariant for read-only producers

```python
# ✅ Use covariant for read-only producers
from typing import TypeVar, Generic

class Animal: ...
class Dog(Animal): ...

T_co = TypeVar("T_co", covariant=True)

class Iterator(Generic[T_co]):
    def __iter__(self) -> "Iterator[T_co]": ...
    def __next__(self) -> T_co: ...

dog_iter: Iterator[Dog] = Iterator()
animal_iter: Iterator[Animal] = dog_iter  # OK — covariant
```

### Contravariant for consumers/handlers

```python
# ✅ Use contravariant for consumers/handlers
from typing import TypeVar, Generic

class Animal: ...
class Dog(Animal): ...

T_contra = TypeVar("T_contra", contravariant=True)

class Logger(Generic[T_contra]):
    def log(self, value: T_contra) -> None: ...

animal_logger: Logger[Animal] = Logger()
dog_logger: Logger[Dog] = animal_logger  # OK — contravariant
```

## When not to use it

**Avoid explicit variance** when:

### Homogeneous types — invariant is fine

```python
from typing import Generic, TypeVar

T = TypeVar("T")

# ❌ Don't bother with variance when types are homogeneous
class Service(Generic[T]):
    def __init__(self, c: T) -> None:
        self._c = c
```

### Internal-only types with no polymorphism

```python
from typing import Generic, TypeVar

T = TypeVar("T")

# ❌ Skip for internal-only types with no polymorphism
class InternalCache(Generic[T]):
    def __init__(self) -> None:
        self._entries: dict[str, T] = {}

    def get(self, k: str) -> T | None: ...
    def set(self, k: str, v: T) -> None: ...
# Never passed as different type → invariant is fine
```

## Antipatterns when using it

**Overly broad variance** — declaring covariant but using the type in input position:

```python
# expect-error
from typing import TypeVar, Generic

T_co = TypeVar("T_co", covariant=True)

class Container(Generic[T_co]):
    def get_data(self) -> T_co: ...
    def set_data(self, v: T_co) -> None: ...  # error: covariant type variable in parameter
# T in input position — not safely covariant
```

**Wrong variance direction** — declaring contravariant but using the type in output position:

```python
# expect-error
from typing import TypeVar, Generic

T_contra = TypeVar("T_contra", contravariant=True)

class Producer(Generic[T_contra]):
    def produce(self) -> T_contra: ...  # error: contravariant type variable in return type
# T in output position — not safely contravariant
```

**Ignoring invariant containers** — declaring a mutable container covariant:

```python
# expect-error
from typing import TypeVar, Generic

class Animal: ...
class Dog(Animal): ...

T_co = TypeVar("T_co", covariant=True)

class Box(Generic[T_co]):
    def __init__(self, value: T_co) -> None:
        self.value = value

    def set(self, v: T_co) -> None:  # error: covariant type variable in parameter
        self.value = v

box: Box[Dog] = Box(Dog())
# runtime: write Cat into Box[Dog], read as Dog → crash
```

## Antipatterns with other techniques

**Runtime checks instead of variance**:

```python ignore
# ❌ Antipattern: runtime checks everywhere
class Producer(Generic[T]):
    def get(self) -> T: ...

def use_dog_producer(p: Producer[Dog]) -> None:
    val = p.get()
    if not isinstance(val, Dog):
        raise TypeError("Expected Dog")  # runtime cost
    val.bark()
```

```python
# ✅ Better: variance guarantees the type statically
from typing import TypeVar, Generic

class Animal: ...
class Dog(Animal):
    def bark(self) -> None: ...

T_co = TypeVar("T_co", covariant=True)

class Producer(Generic[T_co]):
    def get(self) -> T_co: ...

def use_dog_producer(p: Producer[Dog]) -> None:
    dog: Dog = p.get()  # ✅ pyright knows it's Dog
    dog.bark()  # no runtime check needed
```

**Monolithic handler instead of a contravariant generic**:

```python
# ❌ Antipattern: one handler hard-codes every type
class Animal: ...
class Dog(Animal): ...
class Cat(Animal): ...

class Handler:
    def handle(self, v: Dog | Cat | Animal) -> None:
        ...

# ❌ No polymorphism — can't substitute Handler[Animal] for Handler[Dog]
```

```python
# ✅ Better: contravariant handler
from typing import TypeVar, Generic

class Animal: ...
class Dog(Animal): ...

T_contra = TypeVar("T_contra", contravariant=True)

class Handler(Generic[T_contra]):
    def handle(self, v: T_contra) -> None:
        ...

animal_handler: Handler[Animal] = Handler()
dog_handler: Handler[Dog] = animal_handler  # ✅ contravariant substitution
```

**Using mutable list instead of tuple/Sequence for covariance**:

```python
# expect-error
class Animal: ...
class Dog(Animal): ...
class Cat(Animal): ...

# ❌ Antipattern: mutable list covariance
def process_animals(animals: list[Animal]) -> None:
    animals.append(Cat())  # modifies caller's list

dogs: list[Dog] = [Dog()]
process_animals(dogs)  # error: list[Dog] not assignable to list[Animal]
```

```python
# ✅ Better: Sequence (covariant) for read-only access
from collections.abc import Sequence

class Animal:
    @property
    def species(self) -> str:
        return ""

class Dog(Animal): ...

def process_animals(animals: Sequence[Animal]) -> list[str]:
    return [a.species for a in animals]  # no mutation

dogs: Sequence[Dog] = [Dog()]
species: list[str] = process_animals(dogs)  # ✅ Sequence[Dog] <: Sequence[Animal]
```

**Over-using TypeVar with wrong variance**:

```python
from typing import TypeVar, Generic

class Animal: ...
class Dog(Animal): ...

# ❌ Antipattern: explicit invariant when covariant would work
T = TypeVar("T")  # default invariant

class ReadOnlyBox(Generic[T]):
    def get(self) -> T: ...

box: ReadOnlyBox[Dog] = ReadOnlyBox()
# animal_box: ReadOnlyBox[Animal] = box  # error — invariant blocks it, but it should be allowed!
```

```python
# ✅ Better: covariance for read-only containers
from typing import TypeVar, Generic

class Animal: ...
class Dog(Animal): ...

T_co = TypeVar("T_co", covariant=True)

class ReadOnlyBox(Generic[T_co]):
    def get(self) -> T_co: ...

box: ReadOnlyBox[Dog] = ReadOnlyBox()
animal_box: ReadOnlyBox[Animal] = box  # ✅ covariant substitution
```

## Source anchors

- [PEP 484 — Covariance and contravariance](https://peps.python.org/pep-0484/#covariance-and-contravariance)
- [PEP 695 — Type parameter syntax (3.12+)](https://peps.python.org/pep-0695/)
- [mypy — Variance](https://mypy.readthedocs.io/en/stable/generics.html#variance-of-generic-types)
- [typing spec — Variance](https://typing.readthedocs.io/en/latest/spec/generics.html#variance)
