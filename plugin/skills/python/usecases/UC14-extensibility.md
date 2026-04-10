# Extensibility

## The constraint

Extension points must be typed so the checker verifies that plugins, hooks,
and framework extensions conform to the expected interface — catching
signature mismatches and missing implementations before runtime.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| `Protocol` | Define plugin interfaces structurally; no inheritance required | [-> T07](../catalog/T07-structural-typing.md) |
| `ABC` + `@abstractmethod` | Define framework extension points with enforced implementation | [-> T05](../catalog/T05-type-classes.md) |
| Generics | Parameterize plugins over data types they handle | [-> T04](../catalog/T04-generics-bounds.md) |
| `@overload` | Provide distinct signatures for polymorphic extension methods | [-> T22](../catalog/T22-callable-typing.md) |
| `dataclass_transform` | Let plugin frameworks generate typed constructors | [-> T17](../catalog/T17-macros-metaprogramming.md) |

## Patterns

### A — Protocol for plugin interfaces

Plugins implement a structural interface. No inheritance needed — any class
with the right shape satisfies the Protocol.

```python
from typing import Protocol

class Exporter(Protocol):
    def export(self, data: dict[str, object]) -> bytes: ...
    def content_type(self) -> str: ...

class JsonExporter:
    def export(self, data: dict[str, object]) -> bytes:
        import json
        return json.dumps(data).encode()

    def content_type(self) -> str:
        return "application/json"

class CsvExporter:
    def export(self, data: dict[str, object]) -> bytes:
        header = ",".join(data.keys())
        values = ",".join(str(v) for v in data.values())
        return f"{header}\n{values}".encode()

    def content_type(self) -> str:
        return "text/csv"

def run_export(exporter: Exporter, data: dict[str, object]) -> bytes:
    return exporter.export(data)

run_export(JsonExporter(), {"a": 1})    # OK
run_export(CsvExporter(), {"a": 1})     # OK

class BrokenExporter:
    def export(self, data: list[str]) -> str:  # wrong signatures
        return ""

run_export(BrokenExporter(), {"a": 1})  # error: incompatible type
```

### B — ABC for framework extension points

Use ABCs when plugins must inherit from a base class to gain shared behavior.
`@abstractmethod` ensures all required methods are implemented.

```python
from abc import ABC, abstractmethod

class Middleware(ABC):
    @abstractmethod
    def process_request(self, request: dict[str, str]) -> dict[str, str]: ...

    @abstractmethod
    def process_response(self, response: bytes) -> bytes: ...

    def log(self, message: str) -> None:
        """Shared behavior — subclasses inherit this."""
        print(f"[{self.__class__.__name__}] {message}")

class AuthMiddleware(Middleware):
    def process_request(self, request: dict[str, str]) -> dict[str, str]:
        self.log("checking auth")
        return {**request, "auth": "verified"}

    def process_response(self, response: bytes) -> bytes:
        return response

class IncompleteMiddleware(Middleware):
    def process_request(self, request: dict[str, str]) -> dict[str, str]:
        return request
    # error: missing implementation of "process_response"

Middleware()                             # error: cannot instantiate abstract class
AuthMiddleware()                         # OK
```

### C — Generic plugins parameterized over data types

Use generics so a plugin framework can handle different data types while
the checker verifies type consistency.

```python
from typing import Protocol, Generic, TypeVar

T = TypeVar("T")

class Serializer(Protocol[T]):
    def serialize(self, obj: T) -> bytes: ...
    def deserialize(self, data: bytes) -> T: ...

class UserSerializer:
    def serialize(self, obj: dict[str, str]) -> bytes:
        import json
        return json.dumps(obj).encode()

    def deserialize(self, data: bytes) -> dict[str, str]:
        import json
        result = json.loads(data)
        assert isinstance(result, dict)
        return result

def round_trip[T](serializer: Serializer[T], obj: T) -> T:
    raw = serializer.serialize(obj)
    return serializer.deserialize(raw)

user = {"name": "Alice"}
result = round_trip(UserSerializer(), user)   # OK — T is dict[str, str]
reveal_type(result)                           # dict[str, str]

round_trip(UserSerializer(), [1, 2, 3])       # error: list[int] vs dict[str, str]
```

### D — Combining Protocol and ABC

Use a Protocol for external plugins (no inheritance needed) and an ABC for
internal framework extensions (shared behavior).

```python
from typing import Protocol
from abc import ABC, abstractmethod

# External plugins — structural interface
class StorageBackend(Protocol):
    def read(self, key: str) -> bytes | None: ...
    def write(self, key: str, value: bytes) -> None: ...

# Internal framework extension — nominal with shared behavior
class BaseHandler(ABC):
    def __init__(self, storage: StorageBackend) -> None:
        self._storage = storage

    @abstractmethod
    def handle(self, event: dict[str, object]) -> None: ...

    def store_result(self, key: str, data: bytes) -> None:
        self._storage.write(key, data)

class AuditHandler(BaseHandler):
    def handle(self, event: dict[str, object]) -> None:
        self.store_result("audit", str(event).encode())
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| **Protocol** | No coupling; third-party classes satisfy it automatically | No shared behavior; implicit satisfaction can break silently |
| **ABC** | Shared base behavior; explicit contract; runtime enforcement | Requires inheritance; harder for third-party integration |
| **Generic Protocol** | Type-safe parameterization over data types | More complex signatures; TypeVar boilerplate |
| **Combined** | Protocol for external, ABC for internal — best of both | Two abstractions to maintain |

## When to use which feature

- **Use Protocol** for plugin interfaces consumed by external or third-party code — exporters, storage backends, serializers.
- **Use ABC** for internal framework extension points where plugins inherit shared behavior — middleware chains, handler bases.
- **Use Generic Protocol** when plugins must be parameterized over the data types they handle, and you want the checker to verify consistency.
- **Combine Protocol + ABC** when your framework has both external integration points and internal extension hierarchies.

## When to Use

Use extensibility patterns when third-party code must integrate without modifying existing code. The type checker enforces the integration contract at static analysis time instead of at runtime.

**Use Protocol (Pattern A)** for plugin systems where consumers cannot or should not inherit from a base class:

```python
from typing import Protocol

class Logger(Protocol):
    def info(self, msg: str) -> None: ...

# Any object with the right shape works:
class ConsoleLogger:
    def info(self, msg: str) -> None:
        print(msg)

def log_it(logger: Logger) -> None:
    logger.info("hello")

log_it(ConsoleLogger())  # OK — structural match
```

**Use ABC (Pattern B)** when the framework needs to share concrete behavior across all implementations:

```python
from abc import ABC, abstractmethod

class Handler(ABC):
    def pre_process(self) -> None:
        print("starting")

    @abstractmethod
    def handle(self, event: dict) -> None: ...

class AuthHandler(Handler):
    def handle(self, event: dict) -> None:
        self.pre_process()
        print("auth")
```

**Use Protocol + ABC combination (Pattern D)** when you have both external integration points and internal extension hierarchies:

```python
from typing import Protocol
from abc import ABC, abstractmethod

class Storage(Protocol):
    def get(self, key: str) -> bytes | None: ...

class BaseRepository(ABC):
    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    @abstractmethod
    def find(self, id: int) -> dict | None: ...
```

## When Not to Use

**Don't use Protocol** when runtime exhaustiveness is required. Protocols are open — you cannot enumerate all implementations:

```python
from typing import Protocol

class Strategy(Protocol):
    def run(self) -> int: ...

# No compile error if you forget a strategy:
strategies = [s1, s2]  # Forgot s3? Runtime surprise.
```

**Don't use ABC** for third-party extensions that cannot inherit from your base class:

```python
from abc import ABC, abstractmethod

class BasePlugin(ABC):
    @abstractmethod
    def run(self) -> None: ...

class ThirdPartyPlugin:
    def run(self) -> None:
        pass

# Cannot use ThirdPartyPlugin without modifying it to inherit BasePlugin
plugins: list[BasePlugin] = [ThirdPartyPlugin()]  # error: incompatible type
```

**Don't use generics (Pattern C)** when the data type is fixed or known upfront:

```python
# Overcomplicated:
class Serializer(Protocol[T]): ...

# Simpler and clearer:
class UserSerializer(Protocol):
    def serialize(self, user: User) -> bytes: ...
```

**Don't use Protocol with `@runtime_checkable`** for performance-critical paths:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Plugin(Protocol): ...

def load(p: object) -> None:
    if isinstance(p, Plugin):  # runtime check has overhead
        ...
```

## Antipatterns When Using Extensibility

**Over-generic protocols** — too much parametrization hides intent:

```python
from typing import Protocol, TypeVar, Generic

T = TypeVar("T")
K = TypeVar("K")
O = TypeVar("O")

class Repository(Protocol[T, K, O]):
    def get(self, id: K) -> T | None: ...
    def save(self, obj: O) -> K: ...

# Hard to understand and reuse

class UserRepository(Protocol):
    def get(self, id: int) -> User | None: ...
    def save(self, user: User) -> None: ...

# Clear and specific
```

**Delegating type safety** — protocols without runtime validation at boundaries:

```python
from typing import Protocol

class UserRecord(Protocol):
    name: str
    age: int

def process_user(data: UserRecord) -> None:
    # type checker says age is int, but what if it came from JSON?
    print(data.age + 1)

# At boundaries:
def load_user(json: dict) -> UserRecord:
    return type("User", (), {
        "name": json["name"],
        "age": int(json["age"]),  # validate and convert
    })()
```

**Unbounded plugin registration** — allowing duplicate or conflicting plugins:

```python
from typing import Protocol

class Plugin(Protocol):
    name: str
    def run(self) -> None: ...

class PluginHost:
    def __init__(self) -> None:
        self._plugins: list[Plugin] = []

    def register(self, p: Plugin) -> None:
        self._plugins.append(p)  # no dedup — sames can register twice

# Better:
class PluginHost:
    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, p: Plugin) -> None:
        if p.name in self._plugins:
            raise ValueError(f"plugin {p.name} already registered")
        self._plugins[p.name] = p
```

**Protocol with mutable default arguments** — shared state across callers:

```python
from typing import Protocol

class Configurable(Protocol):
    def configure(self, options: dict = {}) -> None: ...  # dangerous!

# The empty dict is created once and shared

# Better:
class Configurable(Protocol):
    def configure(self, options: dict | None = None) -> None: ...
```

**ABC with optional abstract methods** — defeats the purpose of enforcement:

```python
from abc import ABC, abstractmethod

class Handler(ABC):
    @abstractmethod
    def handle(self, event: dict) -> None: ...

    @abstractmethod
    def cleanup(self) -> None: ...  # required

    def cleanup(self) -> None: ...  # ERROR: cannot redefine

# If you want optional behavior:
class Handler(ABC):
    @abstractmethod
    def handle(self, event: dict) -> None: ...

    def cleanup(self) -> None: ...  # optional — no decorator
```

## Antipatterns With Other Techniques

**Using dataclasses instead of Protocol** — tight coupling where structural match suffices:

```python
from dataclasses import dataclass

@dataclass
class Event:
    type: str
    payload: dict

def handle(e: Event) -> None:
    print(e.type)

# Third-party code must import Event and create exactly that class

# Better with Protocol:
from typing import Protocol

class Event(Protocol):
    type: str
    payload: dict

def handle(e: Event) -> None:
    print(e.type)

# Any object with type and payload works
```

**Using inheritance trees instead of Protocol** — rigid hierarchy where composition suffices:

```python
class Animal:
    def speak(self) -> str:
        raise NotImplementedError

class Dog(Animal):
    def speak(self) -> str:
        return "woof"

class Cat(Animal):
    def speak(self) -> str:
        return "meow"

def make_speak(a: Animal) -> None:
    print(a.speak())

# Third-party Animal implementations must inherit from Animal

# Better with Protocol:
from typing import Protocol

class Speaks(Protocol):
    def speak(self) -> str: ...

def make_speak(s: Speaks) -> None:
    print(s.speak())

class Dog:
    def speak(self) -> str:
        return "woof"

make_speak(Dog())  # Works without inheritance
```

**Using `isinstance` Protocol checks** — runtime checks defeat static analysis:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Processor(Protocol):
    def process(self, data: bytes) -> bytes: ...

def handle(obj: object) -> None:
    if isinstance(obj, Processor):  # runtime check
        obj.process(b"")
    else:
        pass  # type narrowing — but why not type it upfront?

# Better:
def handle(processor: Processor) -> None:
    processor.process(b"")  # static check — no isinstance needed
```

**Union types without exhaustiveness** — open switch over closed enum:

```python
from enum import Enum

class Status(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"

def label(status: Status) -> str:
    if status == Status.PENDING:
        return "new"
    # Forgot ACTIVE and CLOSED? No compile error

# Better with Protocol + runtime assertion for exhaustiveness:
from typing import NoReturn

StatusStr = "pending" | "active" | "closed"

def label(s: StatusStr) -> str:
    if s == "pending":
        return "new"
    elif s == "active":
        return "running"
    elif s == "closed":
        return "done"
    else:
        _exhaustive: NoReturn = s  # mypy error if union expanded
        return _exhaustive
```

**Using `Any` in plugin contexts** — defeats structural typing entirely:

```python
from typing import Protocol, Any

class Plugin(Protocol):
    def run(self, ctx: Any) -> Any: ...  # no type safety

# Better:
class PluginContext:
    config: dict[str, str]
    def log(self, msg: str) -> None: ...

class Plugin(Protocol):
    def run(self, ctx: PluginContext) -> None: ...
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| **Protocol** | No coupling; third-party classes satisfy it automatically | No shared behavior; implicit satisfaction can break silently |
| **ABC** | Shared base behavior; explicit contract; runtime enforcement | Requires inheritance; harder for third-party integration |
| **Generic Protocol** | Type-safe parameterization over data types | More complex signatures; TypeVar boilerplate |
| **Combined** | Protocol for external, ABC for internal — best of both | Two abstractions to maintain |

## Source anchors

- [PEP 544 — Protocols: Structural subtyping](https://peps.python.org/pep-0544/)
- [PEP 3119 — Abstract Base Classes](https://peps.python.org/pep-3119/)
- [PEP 484 — Generics](https://peps.python.org/pep-0484/#generics)
- [mypy — Protocols](https://mypy.readthedocs.io/en/stable/protocols.html)
- [Python `abc` module documentation](https://docs.python.org/3/library/abc.html)
