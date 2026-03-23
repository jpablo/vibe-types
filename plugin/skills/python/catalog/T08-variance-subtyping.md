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

## Source anchors

- [PEP 484 — Type Hints (variance)](https://peps.python.org/pep-0484/#covariance-and-contravariance)
- [PEP 695 — Type Parameter Syntax](https://peps.python.org/pep-0695/)
- [typing module — TypeVar](https://docs.python.org/3/library/typing.html#typing.TypeVar)
- [mypy docs — Variance](https://mypy.readthedocs.io/en/stable/generics.html#variance-of-generic-types)
- [pyright docs — Variance](https://microsoft.github.io/pyright/#/configuration?id=type-checking-settings)
