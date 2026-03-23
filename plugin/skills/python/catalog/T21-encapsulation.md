# Encapsulation (Convention-Based)

> **Since:** `_private` convention — Python 1.x; `__name_mangling` — Python 1.x; `__all__` — Python 1.5; `@property` — Python 2.2; pyright `_` access warnings — pyright 1.1+

## What it is

Python has no access modifiers (`private`, `protected`, `public`). Encapsulation is achieved through **conventions** and **tooling**, not language enforcement. A single leading underscore (`_name`) signals "internal — do not use from outside." Double leading underscores (`__name`) trigger **name mangling**, rewriting the attribute to `_ClassName__name` to avoid accidental collisions in subclasses. `__all__` controls what `from module import *` exports. `@property` provides controlled attribute access with getter/setter/deleter methods.

None of these mechanisms are enforced by the Python runtime — you can always access `obj._private` or even `obj._ClassName__mangled`. However, **pyright** respects the leading underscore convention and reports access to `_`-prefixed members from outside the owning class or module as errors (with `reportPrivateUsage`). This makes the convention a soft type-system boundary.

## What constraint it enforces

**The single-underscore convention marks members as internal. pyright reports external access to `_`-prefixed names as errors. `__all__` controls star-import visibility. `@property` prevents direct attribute mutation. None of these are enforced at runtime — they are social contracts backed by optional tooling.**

## Minimal snippet

```python
class BankAccount:
    def __init__(self, owner: str, balance: float) -> None:
        self._owner = owner        # convention-private
        self.__balance = balance   # name-mangled to _BankAccount__balance

    @property
    def balance(self) -> float:
        """Read-only access to balance."""
        return self.__balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.__balance += amount

acct = BankAccount("Alice", 100.0)
print(acct.balance)          # OK — read via property
acct.deposit(50.0)           # OK — controlled mutation
acct.__balance               # AttributeError at runtime (mangled)
acct._owner                  # Works at runtime, but pyright flags: access to private member
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **NewType** [-> catalog/T03](T03-newtypes-opaque.md) | NewType creates a type-level boundary — values cannot cross it without explicit wrapping. This is a stronger encapsulation than `_` convention for type-level distinctions. |
| **Final / immutability** [-> catalog/T32](T32-immutability-markers.md) | `Final` prevents reassignment and `@final` prevents override. Combined with `_` convention, `Final` makes internal constants both private and immutable at the checker level. |
| **Protocol** [-> catalog/T07](T07-structural-typing.md) | Protocols define the *public* surface of a type. Private members (`_`-prefixed) are excluded from protocol satisfaction checks, reinforcing the public/private boundary. |
| **Dataclasses** [-> catalog/T06](T06-derivation.md) | Dataclass fields are public by default. For encapsulation, combine `@dataclass` with `@property` or use `field(repr=False, init=False)` for internal fields. |
| **ABC** [-> catalog/T05](T05-type-classes.md) | Abstract methods define the required public interface. Concrete implementations can keep helper logic in `_`-prefixed methods. |

## Gotchas and limitations

1. **`_` convention is not access control.** Any code can access `obj._private`. pyright flags it, mypy does not (by default). Relying solely on convention means external code can break encapsulation silently.

2. **Name mangling is not security.** `__name` becomes `_ClassName__name`, but this is a deterministic transformation. External code can still access it via the mangled name:

   ```python
   acct._BankAccount__balance    # Works — mangling is transparent
   ```

3. **`__all__` only affects `from module import *`.** It does not prevent `import module; module._internal()`. It is a star-import filter, not an access control list.

4. **`@property` without a setter is read-only but not immutable.** If the underlying data is mutable (e.g., a list), the property prevents reassignment but not in-place mutation:

   ```python
   class Config:
       def __init__(self) -> None:
           self._items: list[str] = []

       @property
       def items(self) -> list[str]:
           return self._items

   c = Config()
   c.items.append("x")     # Mutates the internal list! Property does not prevent this.
   c.items = ["y"]          # AttributeError — no setter
   ```

5. **pyright and mypy differ on `_` enforcement.** pyright reports `reportPrivateUsage` by default in strict mode. mypy has no equivalent built-in check. This means the enforcement level depends on which checker your project uses.

6. **Module-level `_` functions are importable.** `from module import _helper` works even though `_helper` starts with `_`. Only `__all__` (or not listing it) prevents star-import exposure.

## Beginner mental model

Think of Python encapsulation as **office etiquette**, not locked doors. A single underscore (`_name`) is a "do not disturb" sign on a door — colleagues respect it, but the door is not locked. Double underscores (`__name`) is like writing your name on your lunch in the fridge — it gets relabeled with your name to avoid mix-ups, but anyone who reads the label can still take it. `@property` is a reception desk — you can ask for information (getter) but cannot walk behind the counter (no setter). The type checker (pyright) is the office manager who sends a polite email if someone ignores the signs.

## Example A — Module-level encapsulation with __all__

```python
# geometry.py

__all__ = ["Circle", "area"]   # only these are public

import math

class Circle:
    def __init__(self, radius: float) -> None:
        self._radius = radius    # convention-private

    @property
    def radius(self) -> float:
        return self._radius

    def scale(self, factor: float) -> "Circle":
        return Circle(self._radius * factor)

def area(c: Circle) -> float:
    """Public API."""
    return _area_impl(c.radius)

def _area_impl(r: float) -> float:
    """Internal helper — not in __all__."""
    return math.pi * r * r

# From another module:
# from geometry import *       -> imports Circle, area
# from geometry import _area_impl   -> works but pyright warns
```

## Example B — Property-based encapsulation with validation

```python
class Temperature:
    """Temperature in Celsius with validated bounds."""

    def __init__(self, celsius: float) -> None:
        self.celsius = celsius   # goes through the setter

    @property
    def celsius(self) -> float:
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < -273.15:
            raise ValueError(f"Temperature {value} is below absolute zero")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:
        """Read-only derived property."""
        return self._celsius * 9 / 5 + 32

t = Temperature(100.0)
print(t.celsius)       # 100.0
print(t.fahrenheit)    # 212.0

t.celsius = -300       # ValueError: below absolute zero
t.fahrenheit = 0       # AttributeError: property has no setter
t._celsius = -999      # Works at runtime (no enforcement), but pyright warns
```

## Use-case cross-references

- [-> UC-02](../usecases/UC02-domain-modeling.md) — Encapsulated domain types expose a controlled public surface via properties.
- [-> UC-06](../usecases/UC06-immutability.md) — Read-only properties combined with Final attributes enforce immutability conventions.
- [-> UC-09](../usecases/UC09-builder-config.md) — Builder patterns use private state with public chainable methods.

## Source anchors

- [PEP 8 — Naming Conventions (single and double underscore)](https://peps.python.org/pep-0008/#naming-conventions)
- [Python Tutorial — Private Variables](https://docs.python.org/3/tutorial/classes.html#private-variables)
- [Python Data Model — Name mangling](https://docs.python.org/3/reference/expressions.html#atom-identifiers)
- [Built-in Functions — property()](https://docs.python.org/3/library/functions.html#property)
- [pyright — reportPrivateUsage](https://microsoft.github.io/pyright/#/configuration?id=reportprivateusage)
