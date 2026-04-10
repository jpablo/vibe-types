# Immutability and Finality

## The constraint

Values, attributes, and hierarchies cannot be modified after declaration. The type checker rejects reassignment to `Final` variables, mutation of frozen dataclass fields, overriding of `Final` methods, and subclassing of `@final` classes.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Dataclasses (frozen) | Immutable record types where field assignment is a type error | [-> catalog/06](../catalog/T06-derivation.md) |
| Final / ClassVar | Mark variables, methods, or classes as non-overridable / non-reassignable | [-> catalog/12](../catalog/T32-immutability-markers.md) |

## Patterns

### A — Frozen dataclass

Declare a dataclass with `frozen=True` so that field reassignment is flagged by the checker.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: float
    y: float

p = Point(1.0, 2.0)
print(p.x)              # OK
p.x = 3.0               # error: Property "x" defined in "Point" is read-only
```

Frozen dataclasses also get a `__hash__` implementation, making them usable as dict keys and set members.

```python
points = {Point(0, 0): "origin", Point(1, 1): "diagonal"}  # OK — hashable
```

### B — Final variables

Prevent reassignment of module-level constants and instance attributes.

```python
from typing import Final

MAX_RETRIES: Final = 3
MAX_RETRIES = 5          # error: Cannot assign to final name "MAX_RETRIES"

API_URL: Final[str] = "https://api.example.com"
API_URL = "http://localhost"  # error: Cannot assign to final name "API_URL"

class Config:
    timeout: Final[int]

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout    # OK — first assignment

    def update(self) -> None:
        self.timeout = 99         # error: Cannot assign to final attribute "timeout"
```

### C — Final methods preventing override

Mark a method as `Final` so subclasses cannot override it.

```python
from typing import final

class Base:
    @final
    def validate(self) -> bool:
        # Critical validation logic that must not be changed
        return self._check()

    def _check(self) -> bool:
        return True

class Derived(Base):
    def validate(self) -> bool:   # error: Cannot override final method "validate"
        return True               #        defined in "Base"

    def _check(self) -> bool:     # OK — _check is not final
        return False
```

### D — Final class preventing subclassing

Mark a class as `@final` so no subclass can be created.

```python
from typing import final

@final
class Singleton:
    _instance: "Singleton | None" = None

    def __new__(cls) -> "Singleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

class MySingleton(Singleton):     # error: Cannot inherit from final class "Singleton"
    pass
```

### Untyped Python comparison

Without `Final` and `frozen`, constants and records can be silently mutated.

```python
# No type annotations
MAX_RETRIES = 3

# Somewhere deep in the codebase...
MAX_RETRIES = -1    # silently breaks retry logic — no checker warning

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1.0, 2.0)
p.x = "not a number"   # silently corrupts the point — discovered later as TypeError
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **Frozen dataclass** | True immutability for records; enables hashing; checker and runtime both reject mutation | Cannot partially freeze; all fields are frozen or none; `__post_init__` workarounds needed for derived fields |
| **Final variable** | Prevents reassignment of constants and config values | Only checked statically; runtime can still reassign; no deep freeze of mutable contents (e.g., `Final[list[int]]` prevents rebinding but not `.append()`) |
| **Final method** | Protects critical logic from being overridden in subclasses | Cannot be used with `@abstractmethod`; limits extensibility |
| **Final class** | Prevents entire inheritance trees; simplifies reasoning about behavior | May be too restrictive for library code where users expect to subclass |

## When to use which feature

- **Frozen dataclass** for value objects and records that should never change after creation — coordinates, configuration snapshots, event payloads.
- **Final variables** for module-level constants and configuration values that must not be reassigned — API URLs, retry limits, feature flags.
- **Final methods** for critical methods where correctness depends on the exact implementation — validation logic, security checks, serialization protocols.
- **Final classes** sparingly, for types whose behavior must be exactly as defined — singletons, security-sensitive classes, or types where subclassing would violate invariants.

## Source anchors

- [PEP 591 — Adding a final qualifier to typing](https://peps.python.org/pep-0591/)
- [PEP 557 — Data Classes](https://peps.python.org/pep-0557/)
- [mypy — Final names, methods, and classes](https://mypy.readthedocs.io/en/stable/final_attrs.html)
- [Python dataclasses documentation](https://docs.python.org/3/library/dataclasses.html)
- [typing module — Final](https://docs.python.org/3/library/typing.html#typing.Final)

---

## When to Use It

- **Configuration objects** loaded once at startup
- **Value objects** for domain logic (money, coordinates, IDs)
- **API request/response payloads** that should be treated as read-only after creation
- **Function parameters** when you want to guarantee non-mutation
- **Application state** in immutable pattern (e.g., Redux-like state machines)

```python
# When: Configuration loaded at startup
from dataclasses import dataclass
from typing import Final

@dataclass(frozen=True)
class AppConfig:
    api_url: str
    timeout: int

config = AppConfig("https://api.example.com", 5000)
# config.timeout = 1000  # error: Cannot assign to attribute "timeout"
```

```python
# When: Value objects for domain logic
from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    amount: int
    currency: str

def add(m1: Money, m2: Money) -> Money:
    return Money(m1.amount + m2.amount, m1.currency)
```

```python
# When: Shared state across threads
from dataclasses import dataclass

@dataclass(frozen=True)
class AppState:
    user_id: str
    items: tuple[int, ...]  # tuple, not list
    
# Thread-safe: no mutations possible
```

## When NOT to Use It

- **High-performance numeric loops** where object allocations are expensive
- **Large data structures** that would incur significant copy overhead
- **C extensions / native bindings** that expect mutable Python objects
- **Progressive construction** patterns where objects are incrementally built
- **Database result objects** that may need ORM mutation support

```python
# When NOT: Numerical processing (use numpy arrays instead)
# ❌ Overhead from creating new tuples every iteration
def transform_data(data: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(x * 2 for x in data)  # Creates new tuple

# ✅ Use mutable structures for tight loops
def transform_data_fast(data: list[float]) -> None:
    for i in range(len(data)):
        data[i] *= 2  # In-place mutation
```

```python
# When NOT: Incremental object building
# ❌ Difficult with frozen dataclass
@dataclass(frozen=True)
class Report:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

# Cannot easily incrementally build this

# ✅ Use mutable list/tuple during construction, freeze at end
def build_report() -> Report:
    headers = []
    rows = []
    # ... append to lists ...
    return Report(tuple(headers), tuple(rows))
```

---

## Antipatterns When Using Immutability

### Antipattern 1: Mutable nested containers

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    settings: dict[str, str]  # ❌ dict is still mutable!

cfg = Config(settings={"key": "value"})
cfg.settings["key"] = "new"  # OK! The dict itself can be mutated
```

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    settings: tuple[tuple[str, str], ...]  # ✅ Both tuple and inner tuples are immutable

cfg = Config(settings=(("key", "value"),))
```

### Antipattern 2: Using mutable types in frozen dataclass fields

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    coords: list[float]  # ❌ list is mutable

p = Point([1.0, 2.0])
p.coords.append(3.0)  # OK! list can still be mutated
```

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    coords: tuple[float, ...]  # ✅ tuple is immutable

p = Point((1.0, 2.0))
```

### Antipattern 3: Overusing `@final` preventing legitimate extensions

```python
from typing import final

@final
class BaseRepository:
    def find_one(self, id: int): ...
    def find_all(self): ...

# ❌ Cannot subclass even for legitimate reasons
class CachedRepository(BaseRepository):  # error: Cannot inherit from final class
    def find_one(self, id: int): ...
```

```python
# ✅ Mark only the specific methods that must not change
class BaseRepository:
    @final
    def find_one(self, id: int):  # Critical validation logic
        self._validate_id(id)
        return self._fetch(id)
    
    def _validate_id(self, id: int) -> None:  # Can be overridden
        pass
    
    def _fetch(self, id: int):  # Must be implemented
        raise NotImplementedError

class CachedRepository(BaseRepository):
    def _fetch(self, id: int):  # ✅ Can still override _fetch
        ...
```

### Antipattern 4: Deep immutable structures causing excessive copying

```python
from dataclasses import dataclass, field
from typing import NamedTuple

class Inner(Node):
    x: int
    
@dataclass(frozen=True)
class Outer:
    inner: Inner
    data: tuple[int, ...]

# ❌ Expensive to create new instance for small changes
def update_value(o: Outer) -> Outer:
    return Outer(Inner(o.inner.x + 1), tuple(x + 1 for x in o.data))
    # Creates entirely new nested structure
```

```python
# ✅ Use __slots__ or consider hybrid approach for hot paths
class Point(NamedTuple):
    x: float
    y: float

def translate(p: Point, dx: float, dy: float) -> Point:
    return Point(p.x + dx, p.y + dy)  # NamedTuple is lightweight
```

### Antipattern 5: Forgetting that `Final` is shallow

```python
from typing import Final

CONFIG: Final[dict[str, str]] = {"host": "localhost"}
CONFIG["port"] = "8080"  # OK! dict is still mutable
CONFIG = {"host": "remote"}  # error: Cannot assign to final name "CONFIG"
```

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    host: str
    port: str
    
CONFIG: Final = Config("localhost", "8080")
```

---

## Antipatterns Fixed by Immutability

### Pattern 1: Accidental mutation of shared state

```python
# ❌ Without immutability: accidental modification
def process_user(user: dict) -> dict:
    user["processed"] = True  # Mutates caller's dict!
    return user

original = {"name": "Alice"}
process_user(original)
print(original)  # {"name": "Alice", "processed": True} — side effect!
```

```python
# ✅ With frozen dataclass: mutation is an error
from dataclasses import dataclass, field

@dataclass(frozen=True)
class User:
    name: str
    age: int

def process_user(user: User) -> User:
    user.processed = True  # error: Cannot assign to attribute "processed"
    return user

# Must use replace or create new instance:
from dataclasses import replace

def process_user(user: User) -> User:
    return replace(user, processed=True)  # Creates new immutable instance
```

### Pattern 2: Race conditions in concurrent code

```python
# ❌ Without immutability: race condition
from threading import Thread

cart = {"items": [], "total": 0}

def add_item(cart: dict, item: str) -> None:
    cart["items"].append(item)
    cart["total"] += len(item)

threads = [Thread(target=add_item, args=(cart, f"item{i}")) for i in range(10)]
for t in threads: t.start()
for t in threads: t.join()
# cart state is unpredictable!
```

```python
# ✅ With immutability: each operation creates new state
from dataclasses import dataclass
from threading import Thread
from dataclasses import replace

@dataclass(frozen=True)
class Cart:
    items: tuple[str, ...]
    total: int

def add_item(cart: Cart, item: str) -> Cart:
    return replace(cart, items=(*cart.items, item), total=cart.total + len(item))
    # Each thread gets immutable cart, returns new one
```

### Pattern 3: Debugging state changes in state machines

```python
# ❌ Without immutability: state mutations hard to trace
class StateMachine:
    def __init__(self):
        self.state = {"status": "idle", "errors": []}
    
    def process(self) -> None:
        self.state["status"] = "processing"
        if self.should_fail():
            self.state["errors"].append("failed")  # Which call added this?

# Hard to know which operation mutated the state
```

```python
# ✅ With immutability: state transitions are explicit
from dataclasses import dataclass, replace
from typing import Literal

@dataclass(frozen=True)
class State:
    status: Literal["idle", "processing", "done"]
    errors: tuple[str, ...]

class StateMachine:
    def __init__(self):
        self._state = State("idle", ())
    
    @property
    def state(self) -> State:
        return self._state
    
    def process(self) -> None:
        self._state = replace(self._state, status="processing")
        if self.should_fail():
            self._state = replace(self._state, errors=(*self._state.errors, "failed"))
    # Each transition creates a new state object — traceable via logs
```

### Pattern 4: Unexpected behavior with closures

```python
# ❌ Without immutability: closure captures mutated object
def make_handlers(data: list[int]) -> list[callable]:
    handlers = []
    for i in range(3):
        data.append(i)
        handlers.append(lambda: data)
    return handlers

h = make_handlers([])
for handler in h:
    print(handler())  # All show [0, 1, 2], not [0], [0,1], [0,1,2]
```

```python
# ✅ With immutability: each closure captures its own immutable tuple
def make_handlers() -> list[callable]:
    data: tuple[int, ...] = ()
    handlers = []
    for i in range(3):
        data = (*data, i)
        handlers.append(lambda d=data: d)
    return handlers

h = make_handlers()
for handler in h:
    print(handler())  # (0,), (0, 1), (0, 1, 2)
```

### Pattern 5: Default mutable arguments

```python
# ❌ Classic Python gotcha
def add_item(item, container=list()):
    container.append(item)
    return container

add_item(1)  # [1]
add_item(2)  # [1, 2] — default list is reused!
```

```python
# ✅ With frozen dataclass: no mutable defaults
from dataclasses import dataclass

@dataclass(frozen=True)
class Container:
    items: tuple[int, ...] = ()

def add_item(item: int, container: Container) -> Container:
    return Container(items=(*container.items, item))  # New instance each time
```
