# Phantom Types (via TYPE_CHECKING and NewType)

> **Since:** `TYPE_CHECKING` Python 3.5.2 (PEP 484); `NewType` Python 3.5.2 (PEP 484); `Generic` Python 3.5 (PEP 484); `TypeVar` Python 3.5 (PEP 484)

## What it is

A phantom type is a type parameter used only for **compile-time discrimination** — it does not appear in the runtime data. Python does not have true type erasure (generics are not erased because they were never reified in the first place), but several patterns achieve the same goal: **distinguishing values at check time without any runtime overhead**.

**`NewType`** creates a zero-cost type-level wrapper. `UserId = NewType("UserId", int)` produces a callable that returns its argument unchanged at runtime but creates a distinct type for the checker. **`TYPE_CHECKING`** guards imports and definitions so they exist only during static analysis, never at runtime. **Generic type parameters** used only as tags (never stored in an attribute or returned by a method) act as phantom parameters — they influence type compatibility without affecting runtime behavior.

Together, these tools let you tag values with extra type-level meaning (units, validation state, permission levels) that the checker enforces but the runtime ignores.

## What constraint it enforces

**Phantom types create distinct types at check time that share identical runtime representations. The type checker prevents mixing values tagged with different phantom types, catching semantic errors (e.g., passing an unchecked user ID where a validated one is required) without any runtime cost.**

## Minimal snippet

```python
from typing import NewType

RawHtml = NewType("RawHtml", str)
SanitizedHtml = NewType("SanitizedHtml", str)

def sanitize(html: RawHtml) -> SanitizedHtml:
    cleaned = html.replace("<script>", "")   # simplified
    return SanitizedHtml(cleaned)

def render(html: SanitizedHtml) -> None:
    print(html)

raw = RawHtml("<b>hi</b><script>alert(1)</script>")
render(raw)             # error: expected SanitizedHtml, got RawHtml
render(sanitize(raw))   # OK — sanitized first
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **NewType** [-> catalog/T03](T03-newtypes-opaque.md) | `NewType` is the primary mechanism for phantom types in Python. It creates a distinct type at zero runtime cost. |
| **Generics / TypeVar** [-> catalog/T04](T04-generics-bounds.md) | A `Generic[Tag]` where `Tag` is never stored acts as a phantom parameter, distinguishing `Container[Validated]` from `Container[Unvalidated]` at check time. |
| **TYPE_CHECKING guard** [-> catalog/T47](T47-gradual-typing.md) | `if TYPE_CHECKING:` blocks let you define phantom tag types that exist only during static analysis, avoiding any runtime import cost. |
| **Union types** [-> catalog/T02](T02-union-intersection.md) | `RawHtml | SanitizedHtml` as a parameter accepts both, while `SanitizedHtml` alone enforces the phantom constraint. |
| **Literal types** [-> catalog/T52](T52-literal-types.md) | `Literal["validated"]` can serve as a phantom tag in a Generic parameter, creating compile-time state markers without runtime tag objects. |

## Gotchas and limitations

1. **NewType is transparent at runtime.** `NewType("X", int)` returns a callable that is the identity function — `X(42) is 42` is `True`. There is no wrapping, no class, and no `isinstance` support. You cannot write `isinstance(val, UserId)`.

2. **No automatic unwrapping.** A `UserId` is not assignable to `int` without a cast. This is intentional (it enforces the phantom boundary), but it means you must call `int(user_id)` or use a cast to cross back.

   ```python
   UserId = NewType("UserId", int)
   uid = UserId(42)
   x: int = uid       # error: expected int, got UserId
   x: int = int(uid)  # OK — explicit unwrap
   ```

3. **Generic phantom parameters have no runtime effect.** If you define `class Token(Generic[S]):` where `S` is a phantom state parameter, `Token[Locked]()` and `Token[Unlocked]()` are identical at runtime. You cannot branch on the phantom parameter.

4. **TYPE_CHECKING imports are unavailable at runtime.** Code inside `if TYPE_CHECKING:` blocks is never executed. If you accidentally reference a TYPE_CHECKING-only name outside of annotations, you get a `NameError` at runtime.

   ```python
   from __future__ import annotations   # makes all annotations strings
   from typing import TYPE_CHECKING

   if TYPE_CHECKING:
       from .models import HeavyModel

   def process(m: HeavyModel) -> None:  # OK — annotation is a string
       print(type(m))                    # OK — m exists at runtime
       print(HeavyModel)                # NameError! Not imported at runtime
   ```

5. **Phantom types do not compose automatically.** You cannot express "SanitizedHtml is a subtype of RawHtml" — they are independent NewTypes. Any subtyping relationship must be encoded manually via overloads or Union types.

6. **mypy and pyright handle NewType differently in some edge cases.** mypy treats NewType as a distinct type with an implicit `__supertype__` attribute; pyright treats it as a callable returning the new type. Behavior generally matches, but edge cases around inheritance and protocol satisfaction can differ.

## Beginner mental model

Think of phantom types as **color-coded wristbands** at an event. Everyone walks through the same doors (same runtime `int` or `str`), but the wristband color (the phantom type tag) determines which areas they can access. `RawHtml` has a red band, `SanitizedHtml` has a green band. The security guard (type checker) checks the band color, but the bands weigh nothing and are invisible to the event staff (runtime). You must visit the sanitization booth (call `sanitize()`) to swap your red band for a green one.

## Example A — Phantom state machine with Generic tags

```python
from __future__ import annotations
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    class Locked: ...
    class Unlocked: ...

S = TypeVar("S")

class Door(Generic[S]):
    def __init__(self, name: str) -> None:
        self._name = name

    @staticmethod
    def create(name: str) -> Door[Locked]:
        return Door(name)

def unlock(door: Door[Locked], key: str) -> Door[Unlocked]:
    print(f"Unlocking {door._name} with {key}")
    return Door(door._name)   # type: ignore[return-value]

def enter(door: Door[Unlocked]) -> None:
    print(f"Entering through {door._name}")

d = Door.create("front")
enter(d)                      # error: expected Door[Unlocked], got Door[Locked]
d2 = unlock(d, "secret")
enter(d2)                     # OK — unlocked
```

## Example B — Validated vs unvalidated IDs

```python
from typing import NewType

UnvalidatedEmail = NewType("UnvalidatedEmail", str)
ValidatedEmail = NewType("ValidatedEmail", str)

def validate_email(email: UnvalidatedEmail) -> ValidatedEmail | None:
    """Returns ValidatedEmail if valid, None otherwise."""
    if "@" in email and "." in email.split("@")[-1]:
        return ValidatedEmail(email)
    return None

def send_welcome(email: ValidatedEmail) -> None:
    print(f"Sending welcome to {email}")

raw = UnvalidatedEmail("alice@example.com")
send_welcome(raw)              # error: expected ValidatedEmail, got UnvalidatedEmail

validated = validate_email(raw)
if validated is not None:
    send_welcome(validated)    # OK — type narrowed to ValidatedEmail
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Phantom types make invalid states unrepresentable by requiring type-level proof of validation.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Domain boundaries use NewType to distinguish semantically different values with the same runtime type.
- [-> UC-04](../usecases/UC04-generic-constraints.md) — Generic phantom parameters encode state machines and capability tracking at the type level.

## Source anchors

- [PEP 484 — Type Hints (NewType, TYPE_CHECKING)](https://peps.python.org/pep-0484/#newtype-helper-function)
- [typing — NewType](https://docs.python.org/3/library/typing.html#typing.NewType)
- [typing — TYPE_CHECKING](https://docs.python.org/3/library/typing.html#typing.TYPE_CHECKING)
- [mypy — NewType](https://mypy.readthedocs.io/en/stable/more_types.html#newtypes)
- [pyright — NewType support](https://microsoft.github.io/pyright/#/mypy-comparison?id=newtype)
