# Type Conversions (via Dunder Methods)

> **Since:** Dunder conversion methods — Python 1.x; type annotations — Python 3.5 (PEP 484); `__index__` — Python 2.5 (PEP 357)

## What it is

Python has no implicit type conversions in the type system. Unlike C++ (implicit constructors), Scala (implicit conversions), or Rust (`From`/`Into` with `?`), Python never automatically converts one type to another to satisfy a type annotation. All conversions are **explicit**: you call `int(x)`, `str(x)`, `float(x)`, or `bool(x)`. At runtime, these built-in calls dispatch to the corresponding **dunder methods** — `__int__`, `__float__`, `__str__`, `__bool__`, and `__index__` — defined on the object's class.

The type checker treats these calls as opaque function calls. It does **not** infer that a class with `__int__` can be used where `int` is expected. You must call `int()` explicitly; having the dunder method only means the runtime call will succeed.

## What constraint it enforces

**All type conversions must be explicit calls. The type checker does not auto-promote types based on dunder methods — a class with `__int__` is not assignable to `int` without calling `int()`. This prevents silent data loss and makes conversion points visible in the code.**

## Minimal snippet

```python
from typing import override
class Meters:
    def __init__(self, value: float) -> None:
        self._value = value

    def __float__(self) -> float:
        return self._value

    def __int__(self) -> int:
        return int(self._value)

    @override
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
| **NewType** [-> T03](T03-newtypes-opaque.md) | `NewType` creates a distinct type at check time. There is no auto-conversion between the newtype and its base — you must explicitly wrap and unwrap. |
| **ABC / Protocols** [-> T05](T05-type-classes.md) | `typing.SupportsInt`, `SupportsFloat`, `SupportsIndex` are Protocols that match classes with the corresponding dunder. Use these to accept "anything convertible to int" without requiring `int` itself. |
| **Protocol** [-> T07](T07-structural-typing.md) | Custom conversion protocols (`class SupportsSerialize(Protocol): def to_json(self) -> str: ...`) formalize domain-specific conversions. |
| **Union types** [-> T02](T02-union-intersection.md) | Rather than converting, you can accept `int | float` to allow multiple numeric types directly. |
| **Generics** [-> T04](T04-generics-bounds.md) | A generic function bounded by `SupportsFloat` can accept any type with `__float__`, then convert inside the body. |

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

2. **Every object has a truthiness value, even without `__bool__`.** If a class defines neither `__bool__` nor `__len__`, its instances are always truthy. Defining `__bool__` customizes truthiness directly; absent that, `__len__` acts as a fallback (length 0 means falsy). The type checker allows `if obj:` for any type, so nothing warns you when truthiness does not mean what the reader thinks it means.

3. **`__index__` vs `__int__`.** `__index__` provides lossless conversion to `int` (used for slicing, indexing, `bin()`, `hex()`). `__int__` may be lossy (e.g., `int(3.7)` truncates). Not all types with `__int__` have `__index__`.

4. **Numeric tower is not enforced by type checkers.** The `numbers` module defines `Number > Complex > Real > Rational > Integral`, but type checkers do not use this hierarchy. `int` is a subtype of `float` in practice (special-cased by checkers), but `Decimal` and `Fraction` are not subtypes of `float`.

5. **String conversion is universal but untyped.** Every object has `__repr__` and most have `__str__`. The f-string `f"{obj}"` calls `__format__`, which defaults to `__str__`. These are always available, so the type checker never flags them, even when the result is meaningless.

6. **No chain conversions.** Python does not chain conversions. If `A` has `__int__` and you need a `float`, you must write `float(int(a))` — Python will not find the `A -> int -> float` path automatically.

## Beginner mental model

Think of Python types as different currencies. You cannot pay in euros where dollars are expected, even if you know the exchange rate. You must visit the exchange counter (`int()`, `float()`, `str()`) to convert explicitly. Dunder methods like `__int__` are your wallet's ability to be exchanged — they make the conversion *possible* at the counter but do not make the currency *accepted* directly. The type checker is the cashier who only accepts the exact currency listed on the price tag.

## Example A — SupportsFloat protocol for generic numeric processing

```python
# expect-error
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
# expect-error
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

- [-> UC02](../usecases/UC02-domain-modeling.md) — Explicit conversions at domain boundaries prevent mixing raw and domain types.
- [-> UC01](../usecases/UC01-invalid-states.md) — NewType conversions ensure values pass through validation before entering the domain.
- [-> UC05](../usecases/UC05-structural-contracts.md) — SupportsFloat/SupportsInt protocols define convertibility contracts structurally.

## When to use it

- **Dunder conversion methods** — when your custom type has a natural, well-defined conversion to a built-in type.
- **`SupportsInt` / `SupportsFloat` / `SupportsIndex`** — when writing generic functions that accept any convertible type and perform the conversion themselves.
- **Explicit `int()` / `float()` / `str()` calls** — at domain boundaries where external data must be converted and validated.

```python
# ✅ Dunder methods: natural representation of your type
from typing import override


class Temperature:
    def __init__(self, celsius: float) -> None:
        self._celsius = celsius

    def __float__(self) -> float:
        return self._celsius

    @override
    def __str__(self) -> str:
        return f"{self._celsius}°C"


temp = Temperature(25.0)
print(float(temp))  # OK — calls __float__
print(str(temp))    # OK — calls __str__
```

```python
# ✅ SupportsFloat: accept any float-compatible type
from decimal import Decimal
from typing import SupportsFloat


def normalize(values: list[SupportsFloat]) -> list[float]:
    floats = [float(v) for v in values]
    lo, hi = min(floats), max(floats)
    span = hi - lo
    if span == 0:
        return [0.0] * len(floats)
    return [(f - lo) / span for f in floats]


normalize([1, 2.5, 3])                       # OK
normalize([Decimal("1.5"), Decimal("3.0")])  # OK — Decimal has __float__
```

```python
# ✅ Explicit conversion: clear boundary between external and domain data
import json


class UserId:
    def __init__(self, raw: str) -> None:
        if not raw.startswith("u_"):
            raise ValueError("User IDs must start with 'u_'")
        self.raw = raw


data: dict[str, str] = json.loads('{"user_id": "u_123"}')
user_id = UserId(data["user_id"])  # explicit validation at the boundary
```

## When NOT to use it

- **Conversions that silently lose data** — an `__int__` that truncates hides precision loss at every call site.
- **Conversions that can fail at runtime** — `SupportsFloat` only promises the *signature*; it cannot promise the conversion succeeds.
- **Truthiness that conflates emptiness with validity** — do not define `__bool__` when an empty container is a perfectly valid state.
- **`__index__` on inexact values** — `__index__` must be lossless; truncating inside it violates its contract.

```python
# ❌ Dunder method hides data loss
class Score:
    def __init__(self, value: float) -> None:
        self._raw = value

    def __int__(self) -> int:
        return int(self._raw)  # truncation is silent


score = Score(3.9)
total = int(score) + 1  # OK for the checker, but 3.9 -> 3 silently


# ✅ Keep the lossless conversion, make the lossy one explicit and opt-in
class HighResScore:
    def __init__(self, value: float) -> None:
        self._value = value

    def __float__(self) -> float:
        return self._value  # lossless

    def to_int_rounded(self) -> int:
        """Explicitly round instead of truncating."""
        return round(self._value)
```

```python
# ❌ SupportsFloat accepts types whose conversion can fail at runtime
from typing import SupportsFloat


class UserInput:
    def __init__(self, raw: str) -> None:
        self.raw = raw

    def __float__(self) -> float:
        return float(self.raw)  # raises ValueError for non-numeric input


def average(items: list[SupportsFloat]) -> float:
    return sum(float(x) for x in items) / len(items)


average([UserInput("1"), UserInput("abc")])  # type-checks; ValueError at runtime
# The checker only sees __float__'s signature, not whether the conversion can fail
```

```python
# ❌ Implicit bool on a container where empty is a valid state
class MessageQueue:
    def __init__(self, messages: list[str]) -> None:
        self.messages = messages

    def __bool__(self) -> bool:
        return len(self.messages) > 0


def reload(q: MessageQueue) -> None: ...


queue = MessageQueue([])
if not queue:                     # reads as "no queue", actually means "empty queue"
    reload(queue)

# ✅ Explicit check makes the intent visible
if len(queue.messages) == 0:
    reload(queue)
```

```python
# ❌ __bool__ conflates validity with truthiness
class Form:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def __bool__(self) -> bool:
        return len(self.errors) == 0  # "truthy" now means "valid" — surprising


def submit(form: Form) -> None: ...


form = Form()
form.errors.append("Required field missing")
if form:          # reads as "if form exists", actually means "if form is valid"
    submit(form)


# ✅ Explicit validation method
class FormExplicit:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def is_valid(self) -> bool:
        return len(self.errors) == 0


form2 = FormExplicit()
if form2.is_valid():
    print("submitting")
```

```python
# ❌ __index__ must return an exact int, not a truncated one
class BadIndex:
    def __init__(self, value: float) -> None:
        self._value = value

    def __index__(self) -> int:
        return int(self._value)  # truncates — violates the __index__ contract


idx = BadIndex(3.9)
x = [1, 2, 3, 4]
print(x[idx])  # uses 3 — the .9 silently vanished (same for slicing, bin(), hex())


# ✅ Only implement __index__ for exact integers
class SafeIndex:
    def __init__(self, value: int) -> None:
        self._value = value

    def __index__(self) -> int:
        return self._value
```

## Antipatterns this technique fixes

- **`isinstance` chains instead of `SupportsFloat`**

```python
from decimal import Decimal
from typing import SupportsFloat


# ❌ Too restrictive: a plain `int` parameter rejects custom int-like types
def process_id(id: int) -> str:
    return f"ID#{id}"


# ❌ Verbose union + isinstance chain, doesn't scale across libraries
def to_float_verbose(x: int | float | Decimal) -> float:
    if isinstance(x, int):
        return float(x)
    if isinstance(x, float):
        return x
    return float(x)


# ✅ SupportsFloat captures the contract structurally
def to_float(x: SupportsFloat) -> float:
    return float(x)


to_float(1)          # OK
to_float(1.0)        # OK
to_float(Decimal())  # OK
to_float(str())      # error: "str" is incompatible with protocol "SupportsFloat"
```

- **Raw `object` boundaries instead of `NewType`**

```python
# ❌ No type safety at all
def set_username_unsafe(name: object) -> None:
    _name = name


set_username_unsafe(123)  # type-checks, any value sneaks through


# ✅ NewType enforces explicit conversion
from typing import NewType

Username = NewType("Username", str)


def set_username(name: Username) -> None:
    _name = name


raw = "alice"
set_username(raw)            # error: "str" is not assignable to "Username"
set_username(Username(raw))  # OK — explicit conversion
```

- **Magic numbers instead of unit-wrapper types**

```python
# ❌ Magic numbers are unclear
_timeout_ms = 0


def set_timeout_raw(sec: int) -> None:
    global _timeout_ms
    _timeout_ms = sec * 1000


set_timeout_raw(5)  # what unit is this?


# ✅ Conversion wrapper with a named type
class Seconds:
    def __init__(self, value: int) -> None:
        self._seconds = value

    def __int__(self) -> int:
        return self._seconds


class Milliseconds:
    def __init__(self, value: int) -> None:
        self._ms = value

    def to_seconds(self) -> float:
        return self._ms / 1000


def set_timeout(secs: Seconds) -> None:
    global _timeout_ms
    _timeout_ms = int(secs) * 1000


set_timeout(Seconds(5))                       # clear: 5 seconds
set_timeout(Seconds(round(Milliseconds(5000).to_seconds())))  # explicit unit conversion
```

## Source anchors

- [PEP 357 — Allowing Any Object to be Used for Slicing (__index__)](https://peps.python.org/pep-0357/)
- [Python Data Model — Emulating numeric types](https://docs.python.org/3/reference/datamodel.html#emulating-numeric-types)
- [typing — SupportsInt, SupportsFloat, SupportsIndex](https://docs.python.org/3/library/typing.html#typing.SupportsInt)
- [mypy — Duck typing and Supports protocols](https://mypy.readthedocs.io/en/stable/protocols.html#predefined-protocols)
- [numbers — Numeric abstract base classes](https://docs.python.org/3/library/numbers.html)
