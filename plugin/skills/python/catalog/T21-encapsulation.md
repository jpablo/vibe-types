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
acct.__balance               # error: "__balance" is private and used outside of the class — also AttributeError at runtime (mangled)
acct._owner                  # error: "_owner" is protected and used outside of the class — works at runtime, though
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **NewType** [-> T03](T03-newtypes-opaque.md) | NewType creates a type-level boundary — values cannot cross it without explicit wrapping. This is a stronger encapsulation than `_` convention for type-level distinctions. |
| **Final / immutability** [-> T32](T32-immutability-markers.md) | `Final` prevents reassignment and `@final` prevents override. Combined with `_` convention, `Final` makes internal constants both private and immutable at the checker level. |
| **Protocol** [-> T07](T07-structural-typing.md) | Protocols define the *public* surface of a type. Note that `_`-prefixed members declared in a protocol are **not** ignored — pyright requires implementations to provide them like any other member. Keep protocols free of private members so they describe only the public contract. |
| **Dataclasses** [-> T06](T06-derivation.md) | Dataclass fields are public by default. For encapsulation, combine `@dataclass` with `@property` or use `field(repr=False, init=False)` for internal fields. |
| **ABC** [-> T05](T05-type-classes.md) | Abstract methods define the required public interface. Concrete implementations can keep helper logic in `_`-prefixed methods. |

## Gotchas and limitations

1. **`_` convention is not access control.** Any code can access `obj._private`. pyright flags it, mypy does not (by default). Relying solely on convention means external code can break encapsulation silently.

2. **Name mangling is not security.** `__name` becomes `_ClassName__name`, but this is a deterministic transformation. External code can still access it through the mangled name at runtime — pyright flags the attempt, but nothing stops it from running:

```python
class BankAccount:
    def __init__(self) -> None:
        self.__balance: float = 0.0

acct = BankAccount()
acct._BankAccount__balance    # error: Cannot access attribute "_BankAccount__balance" — but it works at runtime
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
c.items.append("x")     # Mutates the internal list! The property does not prevent this.
c.items = ["y"]         # error: Cannot assign to attribute "items" — no setter (AttributeError at runtime)
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
        self._celsius = 0.0
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

t.celsius = -300       # passes the checker — ValueError at runtime: below absolute zero
t.fahrenheit = 0       # error: Cannot assign to attribute "fahrenheit" — property has no setter
t._celsius = -999      # error: "_celsius" is protected and used outside of the class — works at runtime, though
```

## When to use it

- **`_` prefix for internal state** — marking helpers as "do not rely on this API".
- **`__name` mangling** — preventing accidental override or name collisions in subclass hierarchies and mixins.
- **Module-level `__all__`** — a clear public API surface for star imports and documentation generation.
- **Read-only or validating properties** — when invariants must hold, or when values are derived.
- **Encapsulation around mutable backing data** — returning defensive copies or read-only views prevents external corruption.

```python
# When to use: validated domain type with invariants
class Email:
    def __init__(self, address: str) -> None:
        self._address = ""
        self.address = address  # goes through the setter

    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, value: str) -> None:
        if "@" not in value:
            raise ValueError(f"Invalid email: {value}")
        self._address = value


e = Email("user@example.com")
# e.address = "invalid"  # ValueError at runtime


# When to use: _ for internal helper methods
class Report:
    def generate(self) -> str:
        return self._format(self._collect_data())

    def _collect_data(self) -> dict[str, int]:
        # internal implementation detail
        return {"rows": 42}

    def _format(self, data: dict[str, int]) -> str:
        # subject to change without notice
        return f"Report: {data}"


# When to use: __name for subclass-safe internals
class Logger:
    def __init__(self) -> None:
        self.__handlers: list[object] = []  # mangling prevents subclass collision

    def add_handler(self, h: object) -> None:
        self.__handlers.append(h)
```

## When NOT to use it

- **`__name` for simple privacy** — use `_` instead; mangling adds noise and complicates introspection.
- **Overhead for simple data classes** — if there are no invariants, a plain `@dataclass` with public fields is clearer.
- **`@property` without validation** — getters/setters add complexity without payoff for simple attributes.
- **Security-sensitive data** — Python's encapsulation is not security; use encryption or separate processes.
- **`__all__` without star imports** — only matters when consumers use `from module import *`.

```python
# Don't: unnecessary encapsulation for plain data
class Point:
    def __init__(self, x: float, y: float) -> None:
        self._x = x
        self._y = y

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y
```

```python
# Prefer: a dataclass for simple data
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float
```

```python
# Don't: __mangling when `_` suffices
class Service:
    def __internal(self) -> None: ...  # overkill

    def run(self) -> None:
        self.__internal()


# Prefer: _ for "internal"
class ServicePlain:
    def _internal(self) -> None: ...  # pyright flags external access

    def run(self) -> None:
        self._internal()
```

## Antipatterns when using it

### Returning mutable backing data from a property

```python
from collections.abc import Mapping


# Bad: mutable backing data returned directly
class Cache:
    def __init__(self) -> None:
        self._items: dict[str, str] = {}

    @property
    def items(self) -> dict[str, str]:
        return self._items  # caller can mutate!


cache = Cache()
cache.items["key"] = "value"  # corrupts internal state
cache.items.clear()           # catastrophic


# Good: return a defensive copy
class CacheCopy:
    def __init__(self) -> None:
        self._items: dict[str, str] = {}

    @property
    def items(self) -> dict[str, str]:
        return self._items.copy()  # safe snapshot


# Good: return a read-only view
class CacheReadOnly:
    def __init__(self) -> None:
        self._items: dict[str, str] = {}

    @property
    def items(self) -> Mapping[str, str]:
        return self._items  # Mapping exposes no mutation methods
```

### Leaking implementation details through public attributes

```python
class DatabaseConnection:
    def execute(self, query: str) -> None: ...


def create_db() -> DatabaseConnection: ...


# Bad: public attribute leaks the persistence layer
class ShoppingCartBad:
    def __init__(self) -> None:
        self.db_connection = create_db()  # leaky abstraction
        self.cart_items: list[str] = []


# Good: internal details hidden behind a small public API
class ShoppingCart:
    def __init__(self) -> None:
        self._db = create_db()  # convention-private
        self._cart_items: list[str] = []

    def add_item(self, item: str) -> None:
        self._cart_items.append(item)
        self._save_to_db()

    def _save_to_db(self) -> None:
        self._db.execute("INSERT INTO cart_items VALUES (...)")  # internal
```

### Treating `_` as compiler-enforced "protected"

```python
# Bad: assuming `_helper` is unreachable from outside
class Base:
    def _helper(self) -> int:
        return 42


class Child(Base):
    def compute(self) -> int:
        return self._helper()  # OK — subclasses may use protected members


class Unrelated:
    def abuse(self, base: Base) -> int:
        return base._helper()  # error: "_helper" is protected and used outside of the class — works at runtime
```

```python
# Prefer: document the contract explicitly and keep helpers inside it
class Base:
    """
    Public API: compute()
    Protected (for subclasses only): _base_calc()
    """

    def _base_calc(self) -> int:
        """Internal — subject to change without notice."""
        return 42

    def compute(self) -> int:
        return self._base_calc()
```

### Read-only property handing out a mutable list

```python
# Bad: the property is read-only, but the list it returns is not
class Config:
    def __init__(self) -> None:
        self._features: list[str] = ["a", "b"]

    @property
    def features(self) -> list[str]:
        return self._features  # caller can mutate!


cfg = Config()
cfg.features.clear()  # silently corrupts state


# Good: return a tuple snapshot
class ConfigSafe:
    def __init__(self) -> None:
        self._features: list[str] = ["a", "b"]

    @property
    def features(self) -> tuple[str, ...]:
        return tuple(self._features)  # immutable snapshot
```

## Antipatterns fixed by encapsulation

### Module-level mutable state

```python
# Bad: module-level mutable state
count = 0


def increment() -> None:
    global count
    count += 1


count = 0  # anyone can reset it


# Good: encapsulated counter
class Counter:
    def __init__(self) -> None:
        self._value = 0

    def increment(self) -> None:
        self._value += 1

    @property
    def value(self) -> int:
        return self._value


counter = Counter()
# counter._value = 999  # works at runtime, but pyright flags the private access
```

### Stringly-typed values without validation

```python
# Bad: plain string used as an email, no validation anywhere
def send_email_raw(address: str) -> None: ...


send_email_raw("not-valid")  # type-checks; fails much later at runtime


# Good: encapsulated, validated at construction
class Email:
    def __init__(self, address: str) -> None:
        self._address = ""
        self.address = address  # validated via the setter

    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, value: str) -> None:
        if "@" not in value:
            raise ValueError(f"Invalid email: {value}")
        self._address = value


def send_email(email: Email) -> None: ...  # guaranteed valid by construction


send_email(Email("user@example.com"))  # OK
# Email("invalid")  # ValueError at construction
```

### Brittle inheritance with unprotected state

```python
# Bad: public, reassignable state allows corruption
class Node:
    def __init__(self) -> None:
        self.children: list[Node] = []

    def add_child(self, child: Node) -> None:
        self.children.append(child)


class Malicious(Node):
    def corrupt(self) -> None:
        self.children = None  # error: "None" is not assignable to "list[Node]"


node = Node()
node.children.clear()  # no error — anyone can wreck internal state in place
```

```python
# Good: private state with controlled access
class Node:
    def __init__(self) -> None:
        self._children: list[Node] = []

    def add_child(self, child: Node) -> None:
        self._children.append(child)

    @property
    def children(self) -> tuple[Node, ...]:
        return tuple(self._children)  # read-only view
```

## Use-case cross-references

- [-> UC02](../usecases/UC02-domain-modeling.md) — Encapsulated domain types expose a controlled public surface via properties.
- [-> UC06](../usecases/UC06-immutability.md) — Read-only properties combined with Final attributes enforce immutability conventions.
- [-> UC09](../usecases/UC09-builder-config.md) — Builder patterns use private state with public chainable methods.

## Source anchors

- [PEP 8 — Naming Conventions (single and double underscore)](https://peps.python.org/pep-0008/#naming-conventions)
- [Python Tutorial — Private Variables](https://docs.python.org/3/tutorial/classes.html#private-variables)
- [Python Data Model — Name mangling](https://docs.python.org/3/reference/expressions.html#atom-identifiers)
- [Built-in Functions — property()](https://docs.python.org/3/library/functions.html#property)
- [pyright — reportPrivateUsage](https://microsoft.github.io/pyright/#/configuration?id=reportprivateusage)
