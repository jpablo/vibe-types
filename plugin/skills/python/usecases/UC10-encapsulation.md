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
pool._connections           # pyright: error — access to private member
```

### B — `@property` for controlled access

Expose derived or validated values without leaking internal representation.

```python
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
__all__ = ["Cache", "cache_factory"]


class Cache:
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...


class _MemoryCache:
    _store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        self._store[key] = value


def cache_factory() -> Cache:
    return _MemoryCache()  # type: ignore[return-value]
```

**Why**: Consumers depend only on `Cache`; you can swap to a backing store without breaking them.

### When preventing object forgery

```python
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

    def __str__(self) -> str:
        return self._value


# Email("invalid")  # Value raised
Email.create("invalid")  # Returns None
```

**Why**: All instances pass validation; invalid input is rejected at the boundary.

### When decoupling via Protocol

```python
from typing import Protocol


class Database(Protocol):
    def execute(self, query: str) -> list[tuple]: ...


class Postgres:
    def execute(self, query: str) -> list[tuple]:
        return []


class SQLite:
    def execute(self, query: str) -> list[tuple]:
        return []


def query(db: Database) -> list[tuple]:
    return db.execute("SELECT *")


query(Postgres())  # OK
query(SQLite())    # OK
```

**Why**: Consumers accept any `Database`; concrete implementation is decoupled.

## When NOT to Use

### For simple data carriers

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


# ✅ Simple dataclass
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    host: str
    port: int
```

**Why**: No invariants to protect; adds complexity without benefit.

### When mutating from within

```python
# ❌ Hard to test — internal state not observable
class Service:
    def __init__(self) -> None:
        self._repo: object = None  # type: ignore

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

### When exposing internal state

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
@property
def items(self) -> tuple[str, ...]:
    return tuple(self._items)
```

**Why**: Getters that return mutable objects leak encapsulation; callers can corrupt state.

## Antipatterns When Using

### Public getters that expose mutable internals

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
@property
def tags(self) -> tuple[str, ...]:
    return tuple(self._tags)
```

### Storing mutable arguments

```python
# ❌ External caller mutates after passing
class User:
    def __init__(self, data: dict) -> None:
        self._data = data  # stores reference


user_data = {"name": "Alice"}
user = User(user_data)
user_data["name"] = "Bob"  # user._data also changed!

# ✅ Copy on input
def __init__(self, data: dict) -> None:
    self._data = data.copy()  # no reference kept
```

### Overusing `__` name mangling

```python
# ❌ Obfuscates; hard to access even in subclasses
class Base:
    def __init__(self) -> None:
        self.__secret = "hidden"

    def show(self) -> str:
        return self.__secret


class Derived(Base):
    def debug(self) -> str:
        return self.__secret  # AttributeError: no such attribute


# ✅ Use `_` for internal; `__` only for diamond inheritance conflicts
class Base:
    def __init__(self) -> None:
        self._secret = "internal"


class Derived(Base):
    def debug(self) -> str:
        return self._secret  # OK
```

### Protocol with too many members

```python
# ❌ Hard to satisfy; couples to too much
class HeavyProtocol(Protocol):
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def execute(self, query: str) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...
    # ... many more


# ✅ Split into smaller protocols
class Executor(Protocol):
    def execute(self, query: str) -> None: ...


class Transactional(Protocol):
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
```

### Validation-only factory with no invariant

```python
# ❌ What's the point?
class Number:
    def __init__(self, value: int) -> None:
        self._value = value

    @classmethod
    def create(cls, value: int) -> "Number":
        return cls(value)  # no validation


# ✅ Add actual invariant
@classmethod
def create(cls, value: int) -> "Number | None":
    if value < 0:
        return None
    return cls(value)
```

## Antipatterns Where Encapsulation Helps

### Public state mutation everywhere

```python
# ❌ Anyone can corrupt state
account: dict = {"balance": 100, "transactions": []}


def withdraw(account: dict, amount: int) -> None:
    account["balance"] -= amount  # no validation
    account["transactions"].append(f"-${amount}")


withdraw(account, 200)  # negative balance!

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

# ✅ Factory ensures completeness
class User:
    def __init__(self, id_: str, email: str) -> None:
        self.id = id_
        self.email = email

    @classmethod
    def create(cls, id_: str | None, email: str | None) -> "User | None":
        if not id_ or not email:
            return None
        return cls(id_, email)
```

### Magic strings as IDs

```python
# ❌ Wrong ID types mix silently
def get_user(id: str) -> None:
    pass


def get_order(id: str) -> None:
    pass


get_user("123")
get_order("123")


# get_order("123")  # Oops, passed user ID to get_order

# ✅ Newtypes catch errors
from typing import NewType

UserId = NewType("UserId", str)
OrderId = NewType("OrderId", str)


def get_user(id: UserId) -> None:
    pass


def get_order(id: OrderId) -> None:
    pass


# get_order(UserId("123"))  # type error
```

### Global mutable registry

```python
# ❌ Any code can pollute the registry
plugins: dict[str, object] = {}

plugins["auth"] = auth_plugin
plugins["auth"] = broken_plugin  # overwrites!

# ✅ Module-level encapsulation
__all__ = ["register_plugin", "get_plugin"]

_plugins: dict[str, object] = {}


def register_plugin(name: str, plugin: object) -> None:
    _plugins[name] = plugin


def get_plugin(name: str) -> object:
    return _plugins.get(name)
```

### Exposed algorithm internals

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
class Sorter:
    def sort(self, nums: list[int]) -> list[int]:
        return sorted(nums)  # no mutation, no exposure
```

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
