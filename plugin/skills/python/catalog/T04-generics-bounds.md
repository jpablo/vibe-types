# Generics, TypeVar, Bounded Type Variables

> **Since:** Python 3.5 (PEP 484) | **New syntax `[T]`:** Python 3.12 (PEP 695) | **Backport:** `typing_extensions`

## What it is

Generics allow functions, classes, and type aliases to be parameterized over types, so that the same code can operate on different types while preserving type relationships. The mechanism is built on `TypeVar` — a placeholder that the type checker fills in at each call site or instantiation.

A basic `TypeVar("T")` is unconstrained: it can be any type. A **bounded** TypeVar (`TypeVar("T", bound=SomeBase)`) restricts the placeholder to subtypes of a given base. **Constrained** TypeVars (`TypeVar("T", int, str)`) restrict to an explicit set of types — the checker treats each constraint as a separate overload rather than a common supertype.

Python 3.12 introduced a compact declaration syntax: `def f[T](x: T) -> T` and `class C[T]:` replace the older `T = TypeVar("T")` preamble. The new syntax also introduces scoped type parameters — the TypeVar is local to the function or class, eliminating a class of accidental reuse bugs.

## What constraint it enforces

**Generic code preserves type relationships: if a function accepts `T` and returns `T`, the checker guarantees the output type matches the input type. Bounds and constraints restrict which types may be substituted.**

Specifically:

- A function `def first(xs: list[T]) -> T` guarantees the return type matches the element type of the input list.
- `bound=Base` ensures only subtypes of `Base` are accepted, so methods of `Base` are safely callable inside the generic body.
- Constrained TypeVars (`TypeVar("T", int, str)`) act like overloads: the checker verifies the body is valid for *each* constraint independently.

## Minimal snippet

```python
from typing import TypeVar

T = TypeVar("T")

def identity(x: T) -> T:
    return x

reveal_type(identity(42))       # int
reveal_type(identity("hello"))  # str

# Python 3.12+ syntax
def identity_new[T](x: T) -> T:
    return x
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **ParamSpec / TypeVarTuple** [-> catalog/08](T45-paramspec-variadic.md) | ParamSpec captures callable signatures; TypeVarTuple captures variadic type sequences. Both extend generics beyond single-type parameters. |
| **Protocol** [-> catalog/09](T07-structural-typing.md) | Protocols can be generic (`Protocol[T]`), and TypeVars can be bounded by a Protocol, enabling structural constraints on generic code. |
| **Generic classes / Variance** [-> catalog/18](T08-variance-subtyping.md) | Classes inheriting `Generic[T]` become parameterized containers. Variance (`covariant`/`contravariant`) controls subtype relationships of the parameterized class. |
| **Dataclasses** [-> catalog/06](T06-derivation.md) | `@dataclass class Box(Generic[T]): value: T` creates a generic dataclass — the checker tracks the type parameter through construction and access. |
| **Type aliases** [-> catalog/17](T23-type-aliases.md) | `type Pair[T] = tuple[T, T]` (3.12) creates generic type aliases with scoped parameters. |

## Gotchas and limitations

1. **Constrained vs. bounded TypeVars are different.** `TypeVar("T", int, str)` means "T is exactly `int` or exactly `str`" — the checker verifies the body for each separately. `TypeVar("T", bound=int)` means "T is any subtype of `int`" — a single check using the `int` interface. Mixing them up leads to confusing errors.

   ```python
   from typing import TypeVar

   Constrained = TypeVar("Constrained", int, str)
   Bounded = TypeVar("Bounded", bound=int)

   def double_c(x: Constrained) -> Constrained:
       return x + x              # OK — works for both int and str

   def double_b(x: Bounded) -> Bounded:
       return x + x              # OK — int supports +

   double_c(3.14)                # error: float is neither int nor str
   double_b(True)                # OK — bool is a subtype of int
   ```

2. **TypeVar reuse across unrelated signatures.** Before 3.12, a module-level `T = TypeVar("T")` is shared by all functions that reference it. This is fine syntactically but can be confusing — each function gets its own binding of `T`, they do not share. The 3.12 syntax avoids this by scoping `T` to the function or class.

3. **Generic classes require explicit parameterization for full checking.** Using `Box(42)` without annotation may infer `Box[int]`, but in complex cases the checker falls back to `Box[Unknown]`. Explicit annotation (`b: Box[int] = Box(42)`) avoids surprises.

4. **`TypeVar` default (3.13, PEP 696).** Starting in Python 3.13, TypeVars can have defaults: `T = TypeVar("T", default=int)`. Before that, unparameterized generics fall back to the upper bound or `object`.

5. **No higher-kinded types.** Python's type system has no way to abstract over type constructors (e.g., "any `M[T]` where `M` is a monad"). Workarounds exist using Protocol, but they are verbose and limited.

6. **Runtime erasure.** Generic type parameters are erased at runtime. `isinstance(x, list[int])` raises `TypeError`. Use `typing.get_type_hints()` or `typing.get_args()` for runtime introspection.

## Beginner mental model

Think of `TypeVar` as a blank in a mad-libs sentence. When you write `def first(xs: list[___]) -> ___`, the blank gets filled in at each call site: call with `list[int]` and the blank becomes `int`, call with `list[str]` and it becomes `str`. A **bound** is like saying "the blank must be a kind of animal" — you can fill in `Dog` or `Cat` but not `Car`. A **constraint** is like saying "the blank must be exactly `red` or `blue`" — no other color allowed.

## Example A — Generic container preserving element type

```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

    def peek(self) -> T:
        return self._items[-1]

# Usage — checker tracks element type
s: Stack[int] = Stack()
s.push(1)                    # OK
s.push("x")                 # error: Argument 1 has incompatible type "str"; expected "int"
val: int = s.pop()           # OK — return type is int

# Python 3.12 equivalent
class Stack312[T]:
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()
```

## Example B — Bounded TypeVar restricting to Comparable types

```python
from typing import TypeVar, Protocol

class SupportsLessThan(Protocol):
    def __lt__(self, other: object) -> bool: ...

CT = TypeVar("CT", bound=SupportsLessThan)

def min_value(a: CT, b: CT) -> CT:
    return a if a < b else b

# OK — int supports __lt__
reveal_type(min_value(3, 7))           # int

# OK — str supports __lt__
reveal_type(min_value("a", "z"))       # str

# error — complex does not support __lt__
min_value(1+2j, 3+4j)                 # error: complex does not satisfy SupportsLessThan

# Python 3.12 syntax with inline bound
def min_value_new[CT: SupportsLessThan](a: CT, b: CT) -> CT:
    return a if a < b else b
```

## Common type-checker errors and how to read them

### mypy: `TypeVar "T" appears only once in generic function signature`

A TypeVar used in only one place provides no linking — the checker warns it is pointless.

```
error: TypeVar "T" appears only once in generic function signature
```

**Fix:** Either use the TypeVar in both parameter and return type, or replace it with a concrete type or `object`.

### mypy: `Value of type variable "T" cannot be "X"`

The substituted type does not satisfy the bound or constraint.

```
error: Value of type variable "CT" of "min_value" cannot be "complex"
```

**Fix:** Ensure the argument type satisfies the bound. If using a Protocol bound, verify the type implements the required methods.

### pyright: `Type "X" is not assignable to type "T@func"`

Pyright's phrasing for the same constraint violation.

```
error: Type "complex" is not assignable to type "CT@min_value"
  "complex" is not assignable to "SupportsLessThan"
```

**Fix:** Same as above — check that the argument implements the required interface.

### mypy: `Incompatible return value type (got "X", expected "T")`

Returning a value whose type does not match the TypeVar binding.

```
error: Incompatible return value type (got "int", expected "T")
```

**Fix:** Ensure the function body returns a value of type `T`, not a concrete type that happens to be one possible substitution.

## Use-case cross-references

- [-> UC-04](../usecases/UC04-generic-constraints.md) — Generic containers and functions enforce element-type consistency.
- [-> UC-05](../usecases/UC05-structural-contracts.md) — Bounded TypeVars encode capability requirements (e.g., sortable, hashable).
- [-> UC-07](../usecases/UC07-callable-contracts.md) — Generic protocols combine structural subtyping with type parameterization.

## When to Use

### When you need type relationships preserved across parameters and return values

```python
from typing import TypeVar

T = TypeVar("T")

def first(xs: list[T]) -> T:
    """Return first element, preserving exact type."""
    return xs[0]

reveal_type(first([1, 2, 3]))    # int
reveal_type(first(["a", "b"]))   # str
```

### When you need to call methods from a bound

```python
from typing import TypeVar, Protocol

class SupportsAdd(Protocol):
    def __add__(self, other: object) -> object: ...

T = TypeVar("T", bound=SupportsAdd)

def pair_sum(a: T, b: T) -> T:
    return a + a  # type checker knows T has __add__
```

### When you need multiple parameters to share the same type

```python
from typing import TypeVar

T = TypeVar("T")

def swap(pair: tuple[T, T]) -> tuple[T, T]:
    """Swap tuple elements."""
    return (pair[1], pair[0])

swap((1, 2))       # OK — tuple[int, int]
swap((1, "x"))     # error — T cannot be both int and str
```

## When Not to Use

### When you don't need type relationships

```python
from typing import TypeVar

# BAD: unnecessary TypeVar
T = TypeVar("T")

def log_value(x: T) -> None:
    print(x)  # T appears once only — useless

# GOOD: use object or concrete type
def log_value(x: object) -> None:
    print(x)
```

### When a simple union suffices

```python
from typing import TypeVar

# BAD: over-complicated
class SupportsToString(Protocol):
    def __str__(self) -> str: ...

T = TypeVar("T", bound=SupportsToString)

def display(x: T) -> str:
    return str(x)

# GOOD: union is clearer
def display(x: str | int | float) -> str:
    return str(x)
```

### When you need runtime type information

```python
from typing import TypeVar

T = TypeVar("T")

# BAD: TypeVar erased at runtime
def factory(x: T) -> T:
    return x

# At runtime, you cannot inspect T
result = factory(42)
type(result)  # int — works, but T is gone

# GOOD: use isinstance checks or dataclasses
def factory_with_validation(x: int) -> int:
    if not isinstance(x, int):
        raise TypeError
    return x
```

## Antipatterns When Using This Technique

### Unnecessary type variable appearing once

```python
from typing import TypeVar

T = TypeVar("T")

def process_one(x: T) -> None:
    """TypeVar appears only in parameter — mype warns."""
    do_something(x)
    # mypy: TypeVar "T" appears only once in generic function signature

# Fix: remove TypeVar
def process_one(x: object) -> None:
    do_something(x)
```

### Confusing bound with constraint

```python
from typing import TypeVar

# BAD: constraint means "exactly int OR exactly str"
Constrained = TypeVar("Constrained", int, str)

def double(x: Constrained) -> Constrained:
    return x * 2

double(3.14)  # error — float not in constraint list
double(True)  # error — bool not in list even though bool is subclass of int

# GOOD: bound means "any subtype of int"
Bounded = TypeVar("Bounded", bound=int)

def double_bounded(x: Bounded) -> Bounded:
    return x * 2

double_bounded(3)    # OK
double_bounded(True) # OK — bool is subtype of int
```

### Overly restrictive bound that breaks inference

```python
from typing import TypeVar, Protocol

# BAD: too restrictive
class SpecificShape(Protocol):
    x: int
    y: int
    z: int

T = TypeVar("T", bound=SpecificShape)

def normalize(p: T) -> T:
    # Only works for types with x, y, z
    pass

# This fails even though Point2D has similar interface
class Point2D:
    x: int
    y: int

normalize(Point2D(1, 2))  # error — missing z

# GOOD: bound to minimal required interface
class HasMagnitude(Protocol):
    def magnitude(self) -> float: ...

T2 = TypeVar("T2", bound=HasMagnitude)

def normalize2(p: T2) -> T2:
    return p
```

### Module-level TypeVar with accidental reuse

```python
from typing import TypeVar

T = TypeVar("T")  # Module-level

def first(xs: list[T]) -> T:
    return xs[0]

def last(xs: list[T]) -> T:
    return xs[-1]

# BAD: T is the same symbol but means different things
# This is fine in Python but confusing

# GOOD: 3.12+ scoped syntax eliminates confusion
def first_new[T](xs: list[T]) -> T:  # T scoped to this function
    return xs[0]

def last_new[T](xs: list[T]) -> T:  # Different T!
    return xs[-1]
```

## Antipatterns with Other Techniques (Where This Helps)

### Using `object` where generics preserve type

```python
# BAD: loses type information
def identity_bad(x: object) -> object:
    return x

result = identity_bad(42)
# result is object — can't call int-specific methods

# GOOD: generic preserves type
from typing import TypeVar

T = TypeVar("T")

def identity_good(x: T) -> T:
    return x

result = identity_good(42)
# result is int — full type information retained
```

### Repeating type annotations instead of using generics

```python
# BAD: repetitive, error-prone, hard to maintain
def int_add(a: int, b: int) -> int:
    return a + b

def str_join(a: str, b: str) -> str:
    return a + b

def list_concat(a: list[int], b: list[int]) -> list[int]:
    return a + b

# GOOD: generic does all three
from typing import TypeVar, Protocol

class SupportsAdd(Protocol):
    def __add__(self, other: object) -> object: ...

T = TypeVar("T", bound=SupportsAdd)

def combine(a: T, b: T) -> T:
    return a + b
```

### Using `any` in container operations

```python
# BAD: no type safety
def get_item(items: list, index: int):
    return items[index]

result = get_item([1, 2, 3])
result.upper()  # No error at type level, but crashes at runtime

# GOOD: generic container preserves element type
from typing import TypeVar

T = TypeVar("T")

def get_item_safe(items: list[T], index: int) -> T:
    return items[index]

result = get_item_safe([1, 2, 3], 0)
result.upper()  # error: "int" has no attribute "upper"
```

### Union types where coupling is required

```python
# BAD: parameters can be different types
def validate_pair(a: int | str, b: int | str) -> bool:
    return a == b

validate_pair(1, "1")  # type checker OK, but semantically questionable

# GOOD: generic forces coupling
from typing import TypeVar

T = TypeVar("T")

def validate_pair_coupled(a: T, b: T) -> bool:
    return a == b

validate_pair_coupled(1, "1")  # error: T cannot be both int and str
```

## Source anchors

- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
- [PEP 695 — Type Parameter Syntax](https://peps.python.org/pep-0695/)
- [PEP 696 — TypeVar Defaults](https://peps.python.org/pep-0696/)
- [`typing` module docs — TypeVar](https://docs.python.org/3/library/typing.html#typing.TypeVar)
- [typing spec: Generics](https://typing.readthedocs.io/en/latest/spec/generics.html)
- [mypy docs: Generics](https://mypy.readthedocs.io/en/stable/generics.html)
