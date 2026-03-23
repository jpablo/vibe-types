# Type Conversions (via Dunder Methods)

> **Since:** Dunder conversion methods — Python 1.x; type annotations — Python 3.5 (PEP 484); `__index__` — Python 2.5 (PEP 357)

## What it is

Python has no implicit type conversions in the type system. Unlike C++ (implicit constructors), Scala (implicit conversions), or Rust (`From`/`Into` with `?`), Python never automatically converts one type to another to satisfy a type annotation. All conversions are **explicit**: you call `int(x)`, `str(x)`, `float(x)`, or `bool(x)`. At runtime, these built-in calls dispatch to the corresponding **dunder methods** — `__int__`, `__float__`, `__str__`, `__bool__`, and `__index__` — defined on the object's class.

The type checker treats these calls as opaque function calls. It does **not** infer that a class with `__int__` can be used where `int` is expected. You must call `int()` explicitly; having the dunder method only means the runtime call will succeed.

## What constraint it enforces

**All type conversions must be explicit calls. The type checker does not auto-promote types based on dunder methods — a class with `__int__` is not assignable to `int` without calling `int()`. This prevents silent data loss and makes conversion points visible in the code.**

## Minimal snippet

```python
class Meters:
    def __init__(self, value: float) -> None:
        self._value = value

    def __float__(self) -> float:
        return self._value

    def __int__(self) -> int:
        return int(self._value)

    def __str__(self) -> str:
        return f"{self._value}m"

    def __bool__(self) -> bool:
        return self._value != 0.0

distance = Meters(3.7)

x: float = float(distance)     # OK — explicit conversion
y: int = int(distance)         # OK — explicit, truncates to 3
z: float = distance             # error: "Meters" is not assignable to "float"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **NewType** [-> catalog/T03](T03-newtypes-opaque.md) | `NewType` creates a distinct type at check time. There is no auto-conversion between the newtype and its base — you must explicitly wrap and unwrap. |
| **ABC / Protocols** [-> catalog/T05](T05-type-classes.md) | `typing.SupportsInt`, `SupportsFloat`, `SupportsIndex` are Protocols that match classes with the corresponding dunder. Use these to accept "anything convertible to int" without requiring `int` itself. |
| **Protocol** [-> catalog/T07](T07-structural-typing.md) | Custom conversion protocols (`class SupportsSerialize(Protocol): def to_json(self) -> str: ...`) formalize domain-specific conversions. |
| **Union types** [-> catalog/T02](T02-union-intersection.md) | Rather than converting, you can accept `int | float` to allow multiple numeric types directly. |
| **Generics** [-> catalog/T04](T04-generics-bounds.md) | A generic function bounded by `SupportsFloat` can accept any type with `__float__`, then convert inside the body. |

## Gotchas and limitations

1. **`SupportsInt` does not mean `int`.** A parameter typed `int` rejects a class with `__int__`. Use `typing.SupportsInt` (or `SupportsFloat`, `SupportsIndex`) if you intend to accept convertible types and call the conversion yourself.

   ```python
   from typing import SupportsInt

   def double(n: SupportsInt) -> int:
       return int(n) * 2          # explicit conversion inside

   class Score:
       def __int__(self) -> int:
           return 42

   double(Score())                # OK — Score satisfies SupportsInt
   ```

2. **`__bool__` is always defined.** Every object in Python has a truthiness value. By default, custom objects are truthy. Defining `__bool__` customizes this, and `__len__` provides a fallback (objects with `__len__` returning 0 are falsy). The type checker allows `if obj:` for any type.

3. **`__index__` vs `__int__`.** `__index__` provides lossless conversion to `int` (used for slicing, indexing, `bin()`, `hex()`). `__int__` may be lossy (e.g., `int(3.7)` truncates). Not all types with `__int__` have `__index__`.

4. **Numeric tower is not enforced by type checkers.** The `numbers` module defines `Number > Complex > Real > Rational > Integral`, but type checkers do not use this hierarchy. `int` is a subtype of `float` in practice (special-cased by checkers), but `Decimal` and `Fraction` are not subtypes of `float`.

5. **String conversion is universal but untyped.** Every object has `__repr__` and most have `__str__`. The f-string `f"{obj}"` calls `__format__`, which defaults to `__str__`. These are always available, so the type checker never flags them, even when the result is meaningless.

6. **No chain conversions.** Python does not chain conversions. If `A` has `__int__` and you need a `float`, you must write `float(int(a))` — Python will not find the `A -> int -> float` path automatically.

## Beginner mental model

Think of Python types as different currencies. You cannot pay in euros where dollars are expected, even if you know the exchange rate. You must visit the exchange counter (`int()`, `float()`, `str()`) to convert explicitly. Dunder methods like `__int__` are your wallet's ability to be exchanged — they make the conversion *possible* at the counter but do not make the currency *accepted* directly. The type checker is the cashier who only accepts the exact currency listed on the price tag.

## Example A — SupportsFloat protocol for generic numeric processing

```python
from typing import SupportsFloat

def normalize(values: list[SupportsFloat]) -> list[float]:
    """Convert any float-compatible values to float and normalize to [0, 1]."""
    floats = [float(v) for v in values]
    lo, hi = min(floats), max(floats)
    span = hi - lo
    if span == 0:
        return [0.0] * len(floats)
    return [(f - lo) / span for f in floats]

from decimal import Decimal
from fractions import Fraction

normalize([1, 2, 3])                          # OK — int has __float__
normalize([Decimal("1.5"), Decimal("3.0")])   # OK — Decimal has __float__
normalize([Fraction(1, 3), Fraction(2, 3)])   # OK — Fraction has __float__
normalize(["a", "b"])                          # error: str has no __float__
```

## Example B — Explicit conversion boundary with NewType

```python
from typing import NewType

UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)

def get_user(uid: UserId) -> str:
    return f"User#{uid}"

raw_id: int = 42
user_id = UserId(raw_id)           # explicit conversion: int -> UserId

get_user(user_id)                  # OK
get_user(raw_id)                   # error: expected UserId, got int
get_user(OrderId(raw_id))          # error: expected UserId, got OrderId

# No auto-conversion — even though both are int at runtime
```

## Use-case cross-references

- [-> UC-02](../usecases/UC02-domain-modeling.md) — Explicit conversions at domain boundaries prevent mixing raw and domain types.
- [-> UC-01](../usecases/UC01-invalid-states.md) — NewType conversions ensure values pass through validation before entering the domain.
- [-> UC-05](../usecases/UC05-structural-contracts.md) — SupportsFloat/SupportsInt protocols define convertibility contracts structurally.

## Source anchors

- [PEP 357 — Allowing Any Object to be Used for Slicing (__index__)](https://peps.python.org/pep-0357/)
- [Python Data Model — Emulating numeric types](https://docs.python.org/3/reference/datamodel.html#emulating-numeric-types)
- [typing — SupportsInt, SupportsFloat, SupportsIndex](https://docs.python.org/3/library/typing.html#typing.SupportsInt)
- [mypy — Duck typing and Supports protocols](https://mypy.readthedocs.io/en/stable/protocols.html#predefined-protocols)
- [numbers — Numeric abstract base classes](https://docs.python.org/3/library/numbers.html)
