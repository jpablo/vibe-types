# Generic Classes and Variance

> **Since:** Python 3.5 (PEP 484); new syntax 3.12 (PEP 695); automatic variance inference 3.12

## What it is

User-defined generic classes parameterize behavior over one or more type variables. Variance — covariant, contravariant, or invariant — controls how subtype relationships between the type parameters translate to subtype relationships between the parameterized types. Before Python 3.12, variance had to be declared manually on each `TypeVar`. Starting with 3.12, the new `class Foo[T]:` syntax infers variance automatically based on how `T` is used in the class body.

## What constraint it enforces

**Variance rules prevent unsound substitutions: you cannot pass a `list[Dog]` where a `list[Animal]` is expected, because inserting a `Cat` through the `list[Animal]` reference would violate the `list[Dog]` invariant.** More broadly, the checker uses variance to decide which generic types are substitutable for which, blocking assignments that would allow type-unsafe operations at runtime.

The three variance modes:

- **Invariant** (default): `Box[Dog]` is *not* a subtype of `Box[Animal]`, and vice versa. Required when the type parameter appears in both input (argument) and output (return) positions.
- **Covariant**: `ReadOnly[Dog]` *is* a subtype of `ReadOnly[Animal]`. Allowed when the type parameter appears only in output (return) positions.
- **Contravariant**: `Handler[Animal]` *is* a subtype of `Handler[Dog]`. Allowed when the type parameter appears only in input (argument) positions.

## Minimal snippet

```python
# Python 3.12+ — variance is inferred automatically
class ReadOnlyBox[T]:       # covariant: T only in return position
    def __init__(self, val: T) -> None:
        self._val = val
    def get(self) -> T:
        return self._val

class MutableBox[T]:        # invariant: T in both positions
    def __init__(self, val: T) -> None:
        self._val = val
    def get(self) -> T:
        return self._val
    def set(self, val: T) -> None:
        self._val = val

class Animal: ...
class Dog(Animal): ...

ro_dog: ReadOnlyBox[Dog] = ReadOnlyBox(Dog())
ro_animal: ReadOnlyBox[Animal] = ro_dog        # OK — covariant

mut_dog: MutableBox[Dog] = MutableBox(Dog())
mut_animal: MutableBox[Animal] = mut_dog        # error — invariant
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **TypeVar** [-> catalog/07](T04-generics-bounds.md) | Pre-3.12, variance is declared on the TypeVar: `T_co = TypeVar("T_co", covariant=True)`. The 3.12 syntax removes this manual step. |
| **ParamSpec / TypeVarTuple** [-> catalog/08](T45-paramspec-variadic.md) | ParamSpec and TypeVarTuple follow their own variance rules. ParamSpec is typically invariant. TypeVarTuple elements are individually covariant in `Unpack` positions for read-only containers. |
| **Protocol** [-> catalog/09](T07-structural-typing.md) | Protocols can be generic and are variance-checked like regular generics. A Protocol with `T` only in return positions is covariant. |
| **Callable** [-> catalog/11](T22-callable-typing.md) | `Callable[[T], R]` is contravariant in `T` (input) and covariant in `R` (output). This is the classic example of mixed variance. |
| **Sequence vs list** | `Sequence[T]` is covariant (read-only interface), while `list[T]` is invariant (mutable). This is why `list[Dog]` is not assignable to `list[Animal]` but `Sequence[Dog]` is assignable to `Sequence[Animal]`. |

## Gotchas and limitations

1. **`list` is invariant, not covariant.** This is the single most surprising variance fact for newcomers. Because `list` has a `.append()` method (input position for `T`), `list[Dog]` cannot be a subtype of `list[Animal]`. Use `Sequence` (read-only, covariant) when you only need to read.

   ```python
   def print_all(animals: list[Animal]) -> None: ...
   dogs: list[Dog] = [Dog()]
   print_all(dogs)   # error — list is invariant

   from collections.abc import Sequence
   def print_all_v2(animals: Sequence[Animal]) -> None: ...
   print_all_v2(dogs)  # OK — Sequence is covariant
   ```

2. **Manual variance can lie.** Pre-3.12, nothing prevents you from declaring `T_co = TypeVar("T_co", covariant=True)` and then using it in an input position. The checker *should* catch this, but historically some edge cases slipped through. The 3.12 inference eliminates this class of bugs.

3. **Automatic inference may surprise.** In 3.12, if a type parameter appears in both positions, it becomes invariant — even if you intended it to be covariant. You can override with explicit `class Foo[T: covariant]:` syntax (PEP 695) if needed.

4. **`dict` is invariant in both key and value.** `dict[str, Dog]` is not a subtype of `dict[str, Animal]`. Use `Mapping[str, Animal]` (covariant in the value type) for read-only access.

5. **Mutable data structures are almost always invariant.** This includes `list`, `dict`, `set`, and any user-defined class with both getters and setters for the parameterized type.

6. **Variance and `__init__`.** Constructor parameters are technically input positions, but the checkers typically exclude `__init__` from variance checking to allow constructing covariant containers. This is a pragmatic compromise.

## Beginner mental model

Variance answers the question: "If `Dog` is a subtype of `Animal`, is `Box[Dog]` a subtype of `Box[Animal]`?"

- If the box is **read-only** (you can only take things out): yes, because every `Dog` you take out is also an `Animal`. This is **covariance** — the container's subtype relationship goes in the *same direction* as the element's.
- If the box is **write-only** (you can only put things in): it flips. A box that accepts any `Animal` also accepts `Dog`s, so `Box[Animal]` is a subtype of `Box[Dog]`. This is **contravariance** — the direction *reverses*.
- If the box is **read-write**: neither direction is safe. You need an exact match. This is **invariance**.

## Example A — Read-only container (covariant) vs mutable container (invariant)

```python
# Pre-3.12 style with explicit TypeVars
from typing import TypeVar, Generic

T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")

class FrozenStack(Generic[T_co]):
    """Immutable stack — T only appears in output positions."""
    def __init__(self, items: tuple[T_co, ...]) -> None:
        self._items = items

    def peek(self) -> T_co:
        return self._items[-1]             # OK

    def items(self) -> tuple[T_co, ...]:
        return self._items                 # OK

class MutableStack(Generic[T]):
    """Mutable stack — T appears in both positions."""
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:       # T in input position
        self._items.append(item)

    def pop(self) -> T:                    # T in output position
        return self._items.pop()

class Animal: ...
class Dog(Animal): ...
class Cat(Animal): ...

# Covariant: FrozenStack[Dog] IS a subtype of FrozenStack[Animal]
frozen_dogs: FrozenStack[Dog] = FrozenStack((Dog(),))
frozen_animals: FrozenStack[Animal] = frozen_dogs      # OK

# Invariant: MutableStack[Dog] is NOT a subtype of MutableStack[Animal]
mut_dogs: MutableStack[Dog] = MutableStack()
mut_animals: MutableStack[Animal] = mut_dogs            # error
# If this were allowed, you could do:
# mut_animals.push(Cat())  — puts a Cat into a MutableStack[Dog]!
```

## Example B — Event handler with contravariant input type

```python
from typing import TypeVar, Generic
from collections.abc import Callable

T_contra = TypeVar("T_contra", contravariant=True)

class EventHandler(Generic[T_contra]):
    """Handler that consumes events — T only in input position."""
    def __init__(self, callback: Callable[[T_contra], None]) -> None:
        self._callback = callback

    def handle(self, event: T_contra) -> None:
        self._callback(event)

class Event: ...
class ClickEvent(Event):
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

# A handler for any Event can handle ClickEvents too
general_handler: EventHandler[Event] = EventHandler(lambda e: print("event"))
click_handler: EventHandler[ClickEvent] = general_handler   # OK — contravariant

# But not the reverse:
specific_handler: EventHandler[ClickEvent] = EventHandler(
    lambda e: print(f"click at {e.x}, {e.y}")
)
general_from_specific: EventHandler[Event] = specific_handler  # error
# The specific handler expects ClickEvent attributes that a generic Event lacks.
```

Contravariance captures the intuition: a handler that can process *any* event is more general than one that only processes clicks, so it can be used wherever a click handler is expected.

## Common type-checker errors and how to read them

### mypy: `error: Incompatible types in assignment (expression has type "X[A]", variable has type "X[B]")`

The most common variance error. You assigned a generic type to a variable with a different type argument, and the generic class is invariant in that parameter. Check whether you really need a mutable container or if a read-only type (`Sequence`, `Mapping`, `Iterable`) would suffice.

### pyright: `"X[Dog]" is not assignable to "X[Animal]"` / `Type parameter "T" is invariant`

Same cause. pyright explicitly names the variance mode in its error, which makes diagnosis easier.

### mypy: `error: Cannot use a covariant type variable as a parameter`

You declared a TypeVar as covariant but used it in an input position (method parameter). Either change the variance or remove the parameter from the method signature.

### pyright: `TypeVar "T_co" is covariant and cannot be used in parameter type`

Same cause as the mypy variant. Consider whether the class truly needs to accept `T` as input, or if a separate method/TypeVar is appropriate.

### mypy: `error: Argument 1 to "f" has incompatible type "list[Dog]"; expected "list[Animal]"`

The classic invariance surprise. Switch the parameter type to `Sequence[Animal]` if the function only reads from the list.

## Use-case cross-references

- [-> UC-04](../usecases/UC04-generic-constraints.md) — Designing generic container APIs with correct variance for type-safe collection hierarchies.

## When to Use It

- **Designing generic producer types**: Use covariance when `T` only appears in return positions (e.g., iterators, factories, read-only containers).
- **Designing generic consumer types**: Use contravariance when `T` only appears in parameter positions (e.g., handlers, callbacks, sinks).
- **Read-only collections**: Prefer `Sequence[T]`, `Mapping[K, V]`, or `Iterable[T]` over `list`, `dict`, or generator expressions for covariant parameters.
- **Event systems / callbacks**: Leverage contravariance for handler hierarchies where a broader handler substitutes for a narrower one.
- **Immutable data structures**: Covariant wrappers for read-only state (e.g., `tuple[T, ...]`, frozensets, immutable records).
- **API boundaries**: Document variance intent when designing public generic classes that will be extended or substituted by consumers.

```python
# ✓ Use covariant TypeVar for pure producers
T_co = TypeVar("T_co", covariant=True)

class Iterator(Generic[T_co]):
    def __next__(self) -> T_co: ...

# ✓ Use contravariant TypeVar for pure consumers
T_contra = TypeVar("T_contra", contravariant=True)

class Sink(Generic[T_contra]):
    def write(self, value: T_contra) -> None: ...

# ✓ Use covariant Sequence for read-only collection parameters
def process_items(items: Sequence[Item]) -> None: ...
```

## When Not to Use It

- **Mutable containers**: Do not declare covariance on types that mutate or accept `T` (e.g., `list`, `dict`, `set`, or classes with setters).
- **Bidirectional access**: When a type both reads and writes `T`, do not use covariant or contravariant (let it be invariant).
- **Internal implementation details**: Variance annotations are for public API contracts, not internal classes hidden from consumers.
- **Python < 3.12 without explicit TypeVar**: Manual variance on TypeVars can introduce inconsistencies if not carefully audited.

```python
# ✗ Don't mark mutable containers as covariant
T_co = TypeVar("T_co", covariant=True)

class BadMutableList(Generic[T_co]):  # error: T_co in parameter position
    def get(self, index: int) -> T_co: ...
    def set(self, index: int, value: T_co) -> None: ...  # type-checker error

# ✓ Correct: invariant for mutable containers
T = TypeVar("T")

class ImmutableList(Generic[T]):
    def get(self, index: int) -> T: ...
    def set(self, index: int, value: T) -> None: ...  # T is invariant
```

## Antipatterns When Using Variance

### Wrong variance marker for actual usage

```python
# error: 'T_co' appears in input position but marked covariant
T_co = TypeVar("T_co", covariant=True)

class Bad(Generic[T_co]):
    def set_value(self, t: T_co) -> None: ...  # type-checker error

# Fix: match variance to usage
T = TypeVar("T")

class Correct(Generic[T]):
    def get_value(self) -> T: ...
    def set_value(self, t: T) -> None: ...  # T is invariant
```

### Over-constraining with invariance

```python
# ❌ Unnecessary invariance blocks safe assignments
T = TypeVar("T")

class UnnecessaryInvariant(Generic[T]):
    def get_value(self) -> T: ...

dog_val = UnnecessaryInvariant(Dog())
animal_val: UnnecessaryInvariant[Animal] = dog_val  # error — but safe!

# ✓ Use covariant when only reading
T_co = TypeVar("T_co", covariant=True)

class Correct(Generic[T_co]):
    def get_value(self) -> T_co: ...

good_animal: Correct[Animal] = Correct(Dog())  # OK!
```

### Misunderstanding contravariance direction

```python
# Confusing variance direction: expecting covariance but getting contravariance
T_contra = TypeVar("T_contra", contravariant=True)

class Handler(Generic[T_contra]):
    def handle(self, t: T_contra) -> None: ...

animal_handler = Handler(lambda a: print(a))
dog_handler: Handler[Dog] = animal_handler  # OK (contravariant)

# Not the other way:
wrong: Handler[Animal] = Handler(lambda d: print(d.breed))  # error
```

### Marking Protocol parameters as covariant when they shouldn't be

```python
# ❌ Protocol with covariant T has both getter and setter
from typing import Protocol, TypeVar

T_co = TypeVar("T_co", covariant=True)

class MutableContainer(Protocol[T_co]):
    def get(self) -> T_co: ...
    def set(self, value: T_co) -> None: ...  # error: T_co in input position

# ✓ Fix with invariant T
T = TypeVar("T")

class MutableContainer(Protocol[T]):
    def get(self) -> T: ...
    def set(self, value: T) -> None: ...
```

## Antipatterns Where Variance Fixes the Code

### Using `list` instead of `Sequence` causing unnecessary copies

```python
# ❌ Function requires list, forcing copy from read-only data
def sum_numbers(numbers: list[int]) -> int:
    return sum(numbers)

readonly_numbers: tuple[int, ...] = (1, 2, 3)
sum_numbers(list(readonly_numbers))  # forced copy

# ✓ Accept Sequence (covariant) — no copy needed
def sum_numbers_correct(numbers: Sequence[int]) -> int:
    return sum(numbers)

sum_numbers_correct(readonly_numbers)  # OK!
```

### Using `Any` to bypass variance errors

```python
# ❌ Using Any loses type safety
from typing import Any

class BadHandler:
    def handle(self, event: Any) -> None: ...

handler = BadHandler()
handle: Callable[[ClickEvent], None] = handler.handle  # no type checking

# ✓ Correct variance captures the real subtype relationship
from collections.abc import Callable

T_contra = TypeVar("T_contra", contravariant=True)

class SafeHandler(Generic[T_contra]):
    def __init__(self, callback: Callable[[T_contra], None]) -> None:
        self._callback = callback
    
    def handle(self, event: T_contra) -> None:
        self._callback(event)

# A generic handler can handle specific events
generic = SafeHandler(lambda e: print(type(e)))
click_handler: SafeHandler[ClickEvent] = generic  # OK! Still type-safe
```

### Wrapping immutable containers in new types instead of using covariance

```python
# ❌ Creating workaround wrappers
class DogStack:
    def __init__(self, dogs: tuple[Dog, ...]) -> None:
        self._dogs = dogs
    def peek(self) -> Dog:
        return self._dogs[-1]

def print_peek(container: AnimalStack) -> None:  # what's AnimalStack?
    # User creates AnimalStack wrapper to "convert" DogStack
    pass

# ✓ Use covariant generic directly
T_co = TypeVar("T_co", covariant=True)

class Stack(Generic[T_co]):
    def __init__(self, items: tuple[T_co, ...]) -> None:
        self._items = items
    def peek(self) -> T_co:
        return self._items[-1]

dog_stack = Stack((Dog(),))
animal_stack: Stack[Animal] = dog_stack  # OK — covariant!
```

### Manual type guards due to invariant containers

```python
# ❌ Invariant container prevents proper subtyping
T = TypeVar("T")

class Box(Generic[T]):
    def __init__(self, value: T) -> None:
        self._value = value
    def get(self) -> T:
        return self._value

def process(box: Box[Animal]) -> None:
    animal = box.get()
    # Cannot assume animal has Dog attributes even if Box is constructed with Dog
    if isinstance(animal, Dog):
        print(animal.breed)  # need guard

# ✓ Covariant producer eliminates guards
T_co = TypeVar("T_co", covariant=True)

class ReadOnlyBox(Generic[T_co]):
    def __init__(self, value: T_co) -> None:
        self._value = value
    def get(self) -> T_co:
        return self._value

def process_dog(box: ReadOnlyBox[Dog]) -> None:
    dog = box.get()  # type is Dog, no guards needed
    print(dog.breed)
```

## Use-case cross-references

- [-> UC-04](../usecases/UC04-generic-constraints.md) — Designing generic container APIs with correct variance for type-safe collection hierarchies.

## Source anchors

- [PEP 484 — Type Hints (variance)](https://peps.python.org/pep-0484/#covariance-and-contravariance)
- [PEP 695 — Type Parameter Syntax](https://peps.python.org/pep-0695/)
- [typing module — TypeVar](https://docs.python.org/3/library/typing.html#typing.TypeVar)
- [mypy docs — Variance](https://mypy.readthedocs.io/en/stable/generics.html#variance-of-generic-types)
- [pyright docs — Variance](https://microsoft.github.io/pyright/#/configuration?id=type-checking-settings)
