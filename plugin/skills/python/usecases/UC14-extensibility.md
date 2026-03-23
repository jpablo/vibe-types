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

## Source anchors

- [PEP 544 — Protocols: Structural subtyping](https://peps.python.org/pep-0544/)
- [PEP 3119 — Abstract Base Classes](https://peps.python.org/pep-3119/)
- [PEP 484 — Generics](https://peps.python.org/pep-0484/#generics)
- [mypy — Protocols](https://mypy.readthedocs.io/en/stable/protocols.html)
- [Python `abc` module documentation](https://docs.python.org/3/library/abc.html)
