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

## When to use it

**Use variance** when designing generic classes that will be used polymorphically across subtype hierarchies:

```python
# ✅ Use covariant for read-only producers
from typing import TypeVar, Generic

T_co = TypeVar("T_co", covariant=True)

class Iterator(Generic[T_co]):
    def __iter__(self) -> "Iterator[T_co]": ...
    def __next__(self) -> T_co: ...

cat_iter: Iterator[Dog] = ...
animal_iter: Iterator[Animal] = cat_iter  # OK — covariant
```

```python
# ✅ Use contravariant for consumers/handlers
T_contra = TypeVar("T_contra", contravariant=True)

class Logger(Generic[T_contra]):
    def log(self, value: T_contra) -> None: ...

animal_logger: Logger[Animal] = ...
dog_logger: Logger[Dog] = animal_logger  # OK — contravariant
```

```python
# ✅ Use variance for phantom type tagging
T_co = TypeVar("T_co", covariant=True)

class Quantity(Generic[T_co]):
    def __init__(self, value: float, unit: T_co) -> None:
        self.value = value
```

## When not to use it

**Avoid explicit variance** when:

```python
# ❌ No need for variance on concrete types
class User:
    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age
# No type parameters → variance is irrelevant
```

```python
# ❌ Don't use when types are homogeneous
class Service(Generic[T]):
    def init(self, c: T) -> None: ...
    def get_config(self) -> T: ...
# T always same type at call site → invariant works fine
```

```python
# ❌ Skip for internal-only types with no polymorphism
class InternalCache(Generic[T]):
    def __init__(self) -> None:
        self._entries: dict[str, T] = {}

    def get(self, k: str) -> T | None: ...
    def set(self, k: str, v: T) -> None: ...
# Never passed as different type → invariant is fine
```

## Antipatterns when using it

**Overly broad variance**:

```python
# ❌ Declaring covariant but using type in input position
T_co = TypeVar("T_co", covariant=True)

class Container(Generic[T_co]):
    def get_data(self) -> T_co: ...
    def set_data(self, v: T_co) -> None: ...
# mypy: error: Variable "Container[T_co]" is invariant
# T in input position — not safely covariant
```

**Wrong variance direction**:

```python
# ❌ Declaring contravariant but using type in output position
T_contra = TypeVar("T_contra", contravariant=True)

class Producer(Generic[T_contra]):
    def produce(self) -> T_contra: ...
# mypy: error: Variable "Producer[T_contra]" is covariant
# T in output position — not safely contravariant
```

**Ignoring invariant containers**:

```python
# ❌ Mutable container declared covariant
T_co = TypeVar("T_co", covariant=True)

class Box(Generic[T_co]):
    def __init__(self, value: T_co) -> None:
        self.value = value

    def set(self, v: T_co) -> None:
        self.value = v

box: Box[Dog] = Box(Dog())
animal_box: Box[Animal] = box  # mypy error: incompatible variance
# runtime: write Cat into Box[Dog], read as Dog → crash
```

## Antipatterns with other techniques

**Using runtime type guards instead of variance**:

```python
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
T_co = TypeVar("T_co", covariant=True)

class Producer(Generic[T_co]):
    def get(self) -> T_co: ...

def use_dog_producer(p: Producer[Dog]) -> None:
    dog: Dog = p.get()  # ✅ mypy knows it's Dog
    dog.bark()  # no runtime check needed
```

**Using union types instead of contravariance**:

```python
# ❌ Antipattern: union workaround
class Handler:
    def handle(self, v: Dog | Cat | Animal) -> None:
        ...

# ❌ No polymorphism — can't substitute Handler[Animal] for Handler[Dog]
```

```python
# ✅ Better: contravariant handler
T_contra = TypeVar("T_contra", contravariant=True)

class Handler(Generic[T_contra]):
    def handle(self, v: T_contra) -> None:
        ...

animal_handler: Handler[Animal] = ...
dog_handler: Handler[Dog] = animal_handler  # ✅ contravariant substitution
```

**Using mutable list instead of tuple/Sequence for covariance**:

```python
# ❌ Antipattern: mutable list covariance
def process_animals(animals: list[Animal]) -> None:
    animals.append(Cat())  # modifies caller's list

dogs: list[Dog] = [Dog()]
process_animals(dogs)  # mypy error: list[Dog] not list[Animal]
# Workaround forces runtime error:
dogs: list[Animal] = [Dog()]  # cast, then runtime crash on dog.bark()
```

```python
# ✅ Better: Sequence (covariant) for read-only access
def process_animals(animals: Sequence[Animal]) -> list[str]:
    return [a.species for a in animals]  # no mutation

dogs: Sequence[Dog] = [Dog()]
species: list[str] = process_animals(dogs)  # ✅ Sequence[Dog] <: Sequence[Animal]
```

**Over-using TypeVar with wrong variance**:

```python
# ❌ Antipattern: explicit invariant when covariant would work
T = TypeVar("T")  # default invariant

class ReadOnlyBox(Generic[T]):
    def get(self) -> T: ...

box: ReadOnlyBox[Dog] = ...
# animal_box: ReadOnlyBox[Animal] = box  # mypy error — but should be allowed!
```

```python
# ✅ Better: covariance for read-only containers
T_co = TypeVar("T_co", covariant=True)

class ReadOnlyBox(Generic[T_co]):
    def get(self) -> T_co: ...

box: ReadOnlyBox[Dog] = ...
animal_box: ReadOnlyBox[Animal] = box  # ✅ covariant substitution
```

## Source anchors

- [PEP 484 — Covariance and contravariance](https://peps.python.org/pep-0484/#covariance-and-contravariance)
- [PEP 695 — Type parameter syntax (3.12+)](https://peps.python.org/pep-0695/)
- [mypy — Variance](https://mypy.readthedocs.io/en/stable/generics.html#variance-of-generic-types)
- [typing spec — Variance](https://typing.readthedocs.io/en/latest/spec/generics.html#variance)
