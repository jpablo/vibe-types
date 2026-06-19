# Encapsulation in Python

## The constraint

Internal implementation details must be hidden behind a public interface so that
external code cannot depend on or mutate private state. The type checker should
flag violations of encapsulation boundaries at check time.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| `_private` convention | Signal internal members; pyright reports external access | [-> T21](../catalog/T21-encapsulation.md) |
| `__name_mangling` | Avoid attribute collisions in subclass hierarchies | [-> T21](../catalog/T21-encapsulation.md) |
| `__all__` | Control star-import visibility at the module level | [-> T21](../catalog/T21-encapsulation.md) |
| `@property` | Expose controlled read/write access to private state | [-> T21](../catalog/T21-encapsulation.md) |
| `Protocol` | Define the public surface structurally | [-> T07](../catalog/T07-structural-typing.md) |
| `Final` | Prevent reassignment and subclass override | [-> T32](../catalog/T32-immutability-markers.md) |

## Patterns

### A — Single-underscore convention with pyright enforcement

A leading `_` marks a member as internal. pyright's `reportPrivateUsage` flags
external access as an error.

```python
class ConnectionPool:
    def __init__(self, max_size: int) -> None:
        self._connections: list[object] = []
        self._max_size = max_size

    def acquire(self) -> object:
        if self._connections:
            return self._connections.pop()
        return object()  # create new

    def release(self, conn: object) -> None:
        if len(self._connections) < self._max_size:
            self._connections.append(conn)

pool = ConnectionPool(10)
pool.acquire()              # OK — public API
pool._connections           # error: "_connections" is protected and used outside of the class
```

### B — `@property` for controlled access

Expose derived or validated values without leaking internal representation.

```python
# expect-error
class Temperature:
    def __init__(self, celsius: float) -> None:
        self._celsius = celsius

    @property
    def celsius(self) -> float:
        return self._celsius

    @property
    def fahrenheit(self) -> float:
        return self._celsius * 9 / 5 + 32

    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < -273.15:
            raise ValueError("Below absolute zero")
        self._celsius = value

t = Temperature(100.0)
t.celsius                  # OK — 100.0
t.fahrenheit               # OK — 212.0 (read-only)
t.fahrenheit = 0           # error: property has no setter
```

### C — Module boundaries with `__all__`

`__all__` controls what `from module import *` exports. Combine with `_`-prefixed
helpers to create a clear public/private boundary at the module level.

```python
# payments.py
__all__ = ["charge", "PaymentResult"]

from dataclasses import dataclass

@dataclass
class PaymentResult:
    success: bool
    transaction_id: str

def charge(amount: int) -> PaymentResult:
    return _process(amount)

def _process(amount: int) -> PaymentResult:
    # internal — not in __all__
    return PaymentResult(success=True, transaction_id="txn-123")

# from payments import *     -> imports charge, PaymentResult
# from payments import _process  -> works but pyright warns
```

### D — Protocol to define the public surface

A `Protocol` declares the public contract. Consumers depend on the protocol,
not the concrete class, making internal details invisible.

```python
from typing import Protocol

class Logger(Protocol):
    def log(self, message: str) -> None: ...
    def flush(self) -> None: ...

class FileLogger:
    def __init__(self, path: str) -> None:
        self._buffer: list[str] = []   # private
        self._path = path              # private

    def log(self, message: str) -> None:
        self._buffer.append(message)

    def flush(self) -> None:
        self._buffer.clear()

def run(logger: Logger) -> None:
    logger.log("started")
    logger.flush()
    # logger._buffer  -> not part of Protocol, invisible to consumer
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **`_` convention** | Simple; idiomatic; pyright enforces | Not enforced at runtime; mypy does not flag by default |
| **`__` mangling** | Prevents subclass attribute collisions | Deterministic — can still be accessed via `_Class__name` |
| **`__all__`** | Controls star-import surface | Only affects `import *`; direct imports still work |
| **`@property`** | Read-only or validated access; Pythonic | Does not prevent deep mutation of mutable fields |
| **Protocol** | Structural public contract; decouples consumers | Extra type; no runtime enforcement without `@runtime_checkable` |

## When to use which feature

- **Start with `_` convention** for class-level encapsulation. pyright catches violations.
- **Use `@property`** when you need read-only access, validation, or computed attributes.
- **Use `__all__`** to define the public API of a module or package `__init__.py`.
- **Use `__` mangling** sparingly, only to avoid name collisions in deep inheritance.
- **Use `Protocol`** when consumers should depend on an interface, not a concrete class.

## When to Use

### When protecting invariants

```python
class BankAccount:
    def __init__(self, initial_balance: float) -> None:
        if initial_balance < 0:
            raise ValueError("Balance cannot be negative")
        self._balance = initial_balance

    def withdraw(self, amount: float) -> None:
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount

    @property
    def balance(self) -> float:
        return self._balance
```

**Why**: The invariant `balance >= 0` is enforced; callers can't bypass validation.

### When hiding implementation details

```python
# cache.py
from typing import Protocol

__all__ = ["Cache", "cache_factory"]


class Cache(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...


class _MemoryCache:
    _store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        self._store[key] = value


def cache_factory() -> Cache:
    return _MemoryCache()
```

**Why**: Consumers depend only on `Cache`; you can swap to a backing store without breaking them.

### When preventing object forgery

```python
from typing import override

class Email:
    def __init__(self, value: str) -> None:
        import re
        if not re.match(r".+@.+\..+", value):
            raise ValueError("Invalid email")
        self._value = value

    @classmethod
    def create(cls, value: str) -> "Email | None":
        try:
            return cls(value)
        except ValueError:
            return None

    @override
    def __str__(self) -> str:
        return self._value


# Email("invalid")  # ValueError raised
Email.create("invalid")  # Returns None
```

**Why**: All instances pass validation; invalid input is rejected at the boundary.

### When swapping implementations

```python
from typing import Any, Protocol


class Database(Protocol):
    def execute(self, query: str) -> list[tuple[Any, ...]]: ...


class Postgres:
    def execute(self, query: str) -> list[tuple[Any, ...]]:
        return []


class SQLite:
    def execute(self, query: str) -> list[tuple[Any, ...]]:
        return []


def query(db: Database) -> list[tuple[Any, ...]]:
    return db.execute("SELECT *")


query(Postgres())  # OK
query(SQLite())    # OK
```

**Why**: Consumers accept any `Database`; concrete implementation is decoupled.

## When NOT to Use

### When there are no invariants to protect

```python
# ❌ Over-engineered
class Config:
    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port
```

```python
# ✅ Simple dataclass
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    host: str
    port: int
```

**Why**: No invariants to protect; adds complexity without benefit.

### When it makes testing harder

```python
# ❌ Hard to test — internal state not observable
class ServiceBad:
    def __init__(self) -> None:
        self._repo: object = None

    def load(self) -> None:
        self._repo = self._create_repo()

    def _create_repo(self) -> object:
        return object()


# ✅ Pass dependencies for testability
class Service:
    def load(self, repo: object) -> None:
        pass  # easily mocked
```

**Why**: Encapsulation makes testing harder when you need to observe or mock internal state.

### For utility functions

```python
# ❌ Unnecessary class
class MathUtils:
    @staticmethod
    def add(a: float, b: float) -> float:
        return a + b


# ✅ Simple function
def add(a: float, b: float) -> float:
    return a + b
```

**Why**: Pure functions have no state to protect.

### When a property exposes mutable internals

```python
# ❌ Exposes mutable internals
class ShoppingCart:
    def __init__(self) -> None:
        self._items: list[str] = []

    @property
    def items(self) -> list[str]:
        return self._items  # consumer can mutate!


cart = ShoppingCart()
cart.items.append("hack")  # mutated internal state


# ✅ Return copy or tuple
class SafeShoppingCart:
    def __init__(self) -> None:
        self._items: list[str] = []

    @property
    def items(self) -> tuple[str, ...]:
        return tuple(self._items)
```

**Why**: A `@property` returning a mutable list lets consumers mutate hidden state.

### When a property leaks internal structure

```python
# ❌ Leaks internal structure
class Document:
    def __init__(self) -> None:
        self._tags: list[str] = []

    @property
    def tags(self) -> list[str]:
        return self._tags  # exposes mutable list


d = Document()
d.tags.append("hack")  # mutated internal state


# ✅ Return immutable view
class GoodDocument:
    def __init__(self) -> None:
        self._tags: list[str] = []

    @property
    def tags(self) -> tuple[str, ...]:
        return tuple(self._tags)
```

**Why**: Return an immutable view so callers cannot reach into the internal list.

### When an external caller keeps a reference

```python
# ❌ External caller mutates after passing
class User:
    def __init__(self, data: dict[str, str]) -> None:
        self._data = data  # stores reference


user_data = {"name": "Alice"}
user = User(user_data)
user_data["name"] = "Bob"  # user._data also changed!


# ✅ Copy on input
class UserSafe:
    def __init__(self, data: dict[str, str]) -> None:
        self._data = data.copy()  # no reference kept
```

**Why**: Copy mutable input so a caller's later edits cannot reach private state.

### When name mangling obscures access

```python
# expect-error
# ❌ Obfuscates; hard to access even in subclasses
class Base:
    def __init__(self) -> None:
        self.__secret = "hidden"

    def show(self) -> str:
        return self.__secret


class Derived(Base):
    def debug(self) -> str:
        return self.__secret  # error: "__secret" is private (name-mangled to _Base__secret)
```

```python
# ✅ Use `_` for internal; `__` only for diamond inheritance conflicts
class Base:
    def __init__(self) -> None:
        self._secret = "internal"


class Derived(Base):
    def debug(self) -> str:
        return self._secret  # OK
```

**Why**: `__name` mangling hides the attribute even from subclasses; prefer `_name`.

### Protocol with too many members

```python
from typing import Protocol


# ❌ Hard to satisfy; couples to too much
class HeavyProtocol(Protocol):
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def execute(self, query: str) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...
    # ... many more — ✅ split into smaller protocols
```

**Why**: A fat protocol couples consumers to capabilities they don't use.

### When a factory adds no validation

```python
# ❌ What's the point?
class Number:
    def __init__(self, value: int) -> None:
        self._value = value

    @classmethod
    def create(cls, value: int) -> "Number":
        return cls(value)  # no validation
```

```python
# ✅ Add actual invariant
class Number:
    def __init__(self, value: int) -> None:
        self._value = value

    @classmethod
    def create(cls, value: int) -> "Number | None":
        if value < 0:
            return None
        return cls(value)
```

**Why**: A factory that skips validation is just a constructor with extra ceremony.

### When unstructured data invites corruption

```python ignore
# ❌ Anyone can corrupt state
account = {"balance": 100, "transactions": []}


def withdraw(account, amount: int) -> None:
    account["balance"] -= amount  # no validation
    account["transactions"].append(f"-${amount}")


withdraw(account, 200)  # negative balance!
```

```python
# ✅ Encapsulation enforces invariants
class Account:
    def __init__(self, balance: int = 0) -> None:
        self._balance = balance

    def withdraw(self, amount: int) -> None:
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount

    @property
    def balance(self) -> int:
        return self._balance
```

**Why**: A bare dict has no place to enforce `balance >= 0`; a class does.

### Partially constructed objects

```python
# ❌ Object exists in invalid state
class User:
    def __init__(self) -> None:
        self.id: str = ""
        self.email: str = ""

    def set(self, id_: str | None = None, email: str | None = None) -> None:
        self.id = id_ or ""
        self.email = email or ""


u = User()
u.set(id_="123")  # no email yet! but object is usable
```

**Why**: A mutable setter lets an object linger in a half-built, invalid state.

### Mixing up ID types

```python
# expect-error
# ❌ Wrong ID types mix silently
from typing import NewType

UserId = NewType("UserId", str)
OrderId = NewType("OrderId", str)


def get_user(id: UserId) -> None:
    pass


def get_order(id: OrderId) -> None:
    pass


get_order(UserId("123"))  # error: UserId is not assignable to OrderId
```

**Why**: `NewType` makes `UserId` and `OrderId` distinct, so a swapped argument is caught.

### Global mutable registry

```python ignore
# ❌ Any code can pollute the registry
plugins: dict[str, object] = {}

plugins["auth"] = auth_plugin
plugins["auth"] = broken_plugin  # overwrites!

# ✅ Module-level encapsulation
__all__ = ["register_plugin", "get_plugin"]

_plugins: dict[str, object] = {}
# register_plugin / get_plugin guard all access to _plugins
```

**Why**: A module-level `_plugins` dict plus `__all__` hides the store behind functions.

### Exposing internal arrays

```python
# ❌ Callers depend on internal array
class Sorter:
    def __init__(self) -> None:
        self.buffer: list[int] = []

    def sort(self, nums: list[int]) -> list[int]:
        self.buffer.extend(nums)
        self.buffer.sort()
        return self.buffer


s = Sorter()
s.buffer = [1000]  # bypassed the sort


# ✅ Internal state hidden
class CleanSorter:
    def sort(self, nums: list[int]) -> list[int]:
        return sorted(nums)  # no mutation, no exposure
```

**Why**: Exposing `buffer` lets callers bypass `sort`; hide it and return a fresh list.

## Summary

| Situation | Use Encapsulation | Use Simpler Alternative |
|---|---|---|
| Invariants must be protected | ✅ `@property` + validation | ❌ Public fields |
| Implementation may change | ✅ `Protocol` + factory | ❌ Export class |
| Object requires validation | ✅ Factory method | ❌ Public constructor |
| You own the module | ✅ `__all__` + `_` prefix | ❌ Export everything |
| IDs need type safety | ✅ `NewType` | ❌ Plain `str` |
| Simple data transfer | ❌ Over-engineering | ✅ `dataclass` |
| Hot path performance | ❌ Extra indirection | ✅ Direct access |
| Need extensive mocking | ❌ Hard to observe | ✅ Function params |

## Source anchors

- [PEP 8 — Naming Conventions](https://peps.python.org/pep-0008/#naming-conventions)
- [Python Tutorial — Private Variables](https://docs.python.org/3/tutorial/classes.html#private-variables)
- [Built-in Functions — property()](https://docs.python.org/3/library/functions.html#property)
- [pyright — reportPrivateUsage](https://microsoft.github.io/pyright/#/configuration?id=reportprivateusage)
- [PEP 544 — Protocols](https://peps.python.org/pep-0544/)
