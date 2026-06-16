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
| **ParamSpec / TypeVarTuple** [-> T45](T45-paramspec-variadic.md) | ParamSpec captures callable signatures; TypeVarTuple captures variadic type sequences. Both extend generics beyond single-type parameters. |
| **Protocol** [-> T07](T07-structural-typing.md) | Protocols can be generic (`Protocol[T]`), and TypeVars can be bounded by a Protocol, enabling structural constraints on generic code. |
| **Generic classes / Variance** [-> T08](T08-variance-subtyping.md) | Classes inheriting `Generic[T]` become parameterized containers. Variance (`covariant`/`contravariant`) controls subtype relationships of the parameterized class. |
| **Dataclasses** [-> T06](T06-derivation.md) | `@dataclass class Box(Generic[T]): value: T` creates a generic dataclass — the checker tracks the type parameter through construction and access. |
| **Type aliases** [-> T23](T23-type-aliases.md) | `type Pair[T] = tuple[T, T]` (3.12) creates generic type aliases with scoped parameters. |

## Gotchas and limitations

1. **Constrained vs. bounded TypeVars are different.** `TypeVar("T", int, str)` means "T is exactly `int` or exactly `str`" — the checker verifies the body for each separately. `TypeVar("T", bound=int)` means "T is any subtype of `int`" — a single check using the `int` interface. Mixing them up leads to confusing errors.

   ```python
from typing import TypeVar

Constrained = TypeVar("Constrained", int, str)
Bounded = TypeVar("Bounded", bound=int)

def double_c(x: Constrained) -> Constrained:
    return x + x              # OK — checked separately for int and for str

def double_b(x: Bounded) -> Bounded:
    return x + x              # error: Type "int" is not assignable to return type "Bounded@double_b"

double_c(3.14)                # error: Type "float" is not assignable to constrained type variable "Constrained"
double_b(True)                # OK — bool is a subtype of int
   ```

2. **TypeVar reuse across unrelated signatures.** Before 3.12, a module-level `T = TypeVar("T")` is shared by all functions that reference it. This is fine syntactically but can be confusing — each function gets its own binding of `T`, they do not share. The 3.12 syntax avoids this by scoping `T` to the function or class.

3. **Generic classes require explicit parameterization for full checking.** Using `Box(42)` without annotation may infer `Box[int]`, but in complex cases the checker falls back to `Box[Unknown]`. Explicit annotation (`b: Box[int] = Box(42)`) avoids surprises.

4. **`TypeVar` default (3.13, PEP 696).** Starting in Python 3.13, TypeVars can have defaults: `T = TypeVar("T", default=int)`. Without a default, a bare generic reference like `Box` leaves the parameter as `Unknown` (pyright) / `Any` (mypy) — it does **not** fall back to the bound.

5. **No higher-kinded types.** Python's type system has no way to abstract over type constructors (e.g., "any `M[T]` where `M` is a monad"). Workarounds exist using Protocol, but they are verbose and limited.

6. **Runtime erasure.** Generic type parameters are erased at runtime. `isinstance(x, list[int])` raises `TypeError`. Use `typing.get_type_hints()` or `typing.get_args()` for runtime introspection.

## Beginner mental model

Think of `TypeVar` as a blank in a mad-libs sentence. When you write `def first(xs: list[___]) -> ___`, the blank gets filled in at each call site: call with `list[int]` and the blank becomes `int`, call with `list[str]` and it becomes `str`. A **bound** is like saying "the blank must be a kind of animal" — you can fill in `Dog` or `Cat` but not `Car`. A **constraint** is like saying "the blank must be exactly `red` or `blue`" — no other color allowed.

## Example A — Generic container preserving element type

```python
# expect-error
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
from typing import TypeVar, Protocol, Any

class SupportsLessThan(Protocol):
    def __lt__(self, other: Any, /) -> bool: ...

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

### pyright: `TypeVar "T" appears only once in generic function signature`

A TypeVar used in only one place provides no linking — pyright flags it as pointless via `reportInvalidTypeVarUse`. mypy has no equivalent diagnostic.

```text
error: TypeVar "T" appears only once in generic function signature
  Use "object" instead (reportInvalidTypeVarUse)
```

**Fix:** Either use the TypeVar in both parameter and return type, or replace it with a concrete type or `object`.

### mypy: `Value of type variable "T" cannot be "X"`

The substituted type does not satisfy the bound or constraint.

```text
error: Value of type variable "CT" of "min_value" cannot be "complex"
```

**Fix:** Ensure the argument type satisfies the bound. If using a Protocol bound, verify the type implements the required methods.

### pyright: `Type "X" is not assignable to type "T@func"`

Pyright's phrasing for the same constraint violation.

```text
error: Type "complex" is not assignable to type "CT@min_value"
  "complex" is not assignable to "SupportsLessThan"
```

**Fix:** Same as above — check that the argument implements the required interface.

### mypy: `Incompatible return value type (got "X", expected "T")`

Returning a value whose type does not match the TypeVar binding.

```text
error: Incompatible return value type (got "int", expected "T")
```

**Fix:** Ensure the function body returns a value of type `T`, not a concrete type that happens to be one possible substitution.

## Use-case cross-references

- [-> UC04](../usecases/UC04-generic-constraints.md) — Generic containers and functions enforce element-type consistency.
- [-> UC05](../usecases/UC05-structural-contracts.md) — Bounded TypeVars encode capability requirements (e.g., sortable, hashable).
- [-> UC07](../usecases/UC07-callable-contracts.md) — Generic protocols combine structural subtyping with type parameterization.

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
from typing import Any, Protocol, Self, TypeVar

class SupportsAdd(Protocol):
    def __add__(self, other: Any, /) -> Self: ...

T = TypeVar("T", bound=SupportsAdd)

def pair_sum(a: T, b: T) -> T:
    return a + b  # the bound guarantees T has __add__

reveal_type(pair_sum(1, 2))        # int
reveal_type(pair_sum("a", "b"))    # str
```

Why `other: Any` with a positional-only `/`? Parameters are checked contravariantly: `int.__add__` accepts only `int`, so a protocol declaring `other: object` would *not* be satisfied by `int`, `str`, or `list`. `Any` is compatible in both directions, and the `/` matches the positional-only signatures of the built-in dunders.

### When you need multiple parameters to share the same type

```python
from typing import TypeVar

T = TypeVar("T")

def swap(pair: tuple[T, T]) -> tuple[T, T]:
    """Swap tuple elements."""
    return (pair[1], pair[0])

reveal_type(swap((1, 2)))      # tuple[int, int]

# Careful: a mixed pair is NOT rejected — T widens to the union
reveal_type(swap((1, "x")))    # tuple[int | str, int | str]

# To genuinely reject mixed pairs, constrain T to exact types
S = TypeVar("S", int, str)

def swap_strict(pair: tuple[S, S]) -> tuple[S, S]:
    return (pair[1], pair[0])

swap_strict((1, 2))     # OK — S solves to int
swap_strict((1, "x"))   # error: "Literal['x']" is not assignable to "int"
```

## When Not to Use

### When you don't need type relationships

```python
from typing import TypeVar

T = TypeVar("T")

# BAD: unnecessary TypeVar — pyright flags it
def log_value(x: T) -> None:  # error: TypeVar "T" appears only once in generic function signature
    print(x)

# GOOD: use object or a concrete type
def log_value_ok(x: object) -> None:
    print(x)
```

### When a simple union suffices

```python
from typing import TypeVar, Protocol

# BAD: over-complicated — and the TypeVar links nothing
class SupportsToString(Protocol):
    def __str__(self) -> str: ...

T = TypeVar("T", bound=SupportsToString)

def display(x: T) -> str:  # error: TypeVar "T" appears only once in generic function signature
    return str(x)

# GOOD: union is clearer
def display_simple(x: str | int | float) -> str:
    return str(x)
```

### When you need runtime type information

```python
from typing import TypeVar

T = TypeVar("T")

# BAD: TypeVar erased at runtime — you cannot inspect T
def factory(x: T) -> T:
    return x

result = factory(42)
type(result)  # <class 'int'> — works, but T itself is gone at runtime

# GOOD: use isinstance checks for runtime validation
def factory_with_validation(x: object) -> int:
    if not isinstance(x, int):
        raise TypeError
    return x
```

## Antipatterns When Using This Technique

### Unnecessary type variable appearing once

```python
from typing import TypeVar

T = TypeVar("T")

def do_something(x: object) -> None:
    pass

def process_one(x: T) -> None:  # error: TypeVar "T" appears only once in generic function signature
    """TypeVar appears only in the parameter — pyright flags it as useless."""
    do_something(x)

# Fix: remove the TypeVar
def process_one_fixed(x: object) -> None:
    do_something(x)
```

### Misunderstanding constrained TypeVars

```python
from typing import TypeVar

# Constraints mean "exactly int or exactly str" — but a subtype of a
# constraint BINDS to that constraint, it is not rejected.
Constrained = TypeVar("Constrained", int, str)

def double(x: Constrained) -> Constrained:
    return x * 2

double(3.14)               # error: Type "float" is not assignable to constrained type variable "Constrained"
reveal_type(double(True))  # int — bool binds to the int constraint; the result widens to int

# bound= means "any subtype of int", and the precise subtype is preserved
Bounded = TypeVar("Bounded", bound=int)

def identity_bounded(x: Bounded) -> Bounded:
    return x

reveal_type(identity_bounded(True))  # bool — exact subtype flows through
```

### Overly restrictive bound

```python
from typing import TypeVar, Protocol

# BAD: the bound demands more than the function needs
class SpecificShape(Protocol):
    x: int
    y: int
    z: int

T = TypeVar("T", bound=SpecificShape)

def normalize(p: T) -> T:
    # Only works for types with x, y, AND z
    return p

# This fails even though Point2D has a similar interface
class Point2D:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

normalize(Point2D(1, 2))  # error: "Point2D" is incompatible with protocol "SpecificShape" — "z" is not present

# GOOD: bound on the minimal required interface
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
from typing import TypeVar

# BAD: loses type information
def identity_bad(x: object) -> object:
    return x

result = identity_bad(42)
# result is object — can't call int-specific methods on it

# GOOD: generic preserves type
T = TypeVar("T")

def identity(x: T) -> T:
    return x

reveal_type(identity(42))  # int
```

### One function per type instead of a generic

```python
from typing import Any, Protocol, Self, TypeVar

# BAD: repetitive, error-prone, hard to maintain
def int_add(a: int, b: int) -> int:
    return a + b

def str_join(a: str, b: str) -> str:
    return a + b

def list_concat(a: list[int], b: list[int]) -> list[int]:
    return a + b

# GOOD: one generic does all three
class SupportsAdd(Protocol):
    def __add__(self, other: Any, /) -> Self: ...

T = TypeVar("T", bound=SupportsAdd)

def combine(a: T, b: T) -> T:
    return a + b

reveal_type(combine(1, 2))        # int
reveal_type(combine("a", "b"))    # str
reveal_type(combine([1], [2]))    # list[int]
```

### `Any` containers losing element types

```python
from typing import Any, TypeVar

# BAD: Any erases the element type
def get_item(items: list[Any], index: int) -> Any:
    return items[index]

result = get_item([1, 2, 3], 0)
result.upper()  # no static error — crashes at runtime with AttributeError

# GOOD: generic container preserves element type
T = TypeVar("T")

def get_item_safe(items: list[T], index: int) -> T:
    return items[index]

result2 = get_item_safe([1, 2, 3], 0)
result2.upper()  # error: Cannot access attribute "upper" for class "int"
```

### Union types where coupling is required

```python
from typing import TypeVar

# BAD: parameters can be different types
def validate_pair(a: int | str, b: int | str) -> bool:
    return a == b

validate_pair(1, "1")  # accepted — nothing links a and b

# An unconstrained TypeVar does NOT reject mixed calls either:
T = TypeVar("T")

def validate_pair_weak(a: T, b: T) -> bool:
    return a == b

validate_pair_weak(1, "1")  # also accepted — T just widens to int | str

# GOOD: a constrained TypeVar genuinely forces both to match
S = TypeVar("S", int, str)

def validate_pair_coupled(a: S, b: S) -> bool:
    return a == b

validate_pair_coupled(1, 2)    # OK — S solves to int
validate_pair_coupled(1, "1")  # error: "Literal['1']" is not assignable to "int"
```

## Source anchors

- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
- [PEP 695 — Type Parameter Syntax](https://peps.python.org/pep-0695/)
- [PEP 696 — TypeVar Defaults](https://peps.python.org/pep-0696/)
- [`typing` module docs — TypeVar](https://docs.python.org/3/library/typing.html#typing.TypeVar)
- [typing spec: Generics](https://typing.readthedocs.io/en/latest/spec/generics.html)
- [mypy docs: Generics](https://mypy.readthedocs.io/en/stable/generics.html)
