# Configuration and Builder Patterns

## The constraint

Required fields must be provided and optional fields must have correct types,
so that configuration objects have validated shapes at check time — preventing
missing-key errors and type mismatches that surface only at runtime.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| `TypedDict` (Required/NotRequired) | Dict-shaped config with per-key optionality | [-> catalog/03](../catalog/T31-record-types.md) |
| Dataclasses with defaults | Struct-like config with default values and `KW_ONLY` | [-> catalog/06](../catalog/T06-derivation.md) |
| `@overload` | Multiple constructor signatures for config factories | [-> catalog/11](../catalog/T22-callable-typing.md) |
| `Annotated` | Carry validation metadata alongside types | [-> catalog/15](../catalog/T26-refinement-types.md) |
| `Self` | Fluent builder methods that return the same type | [-> catalog/16](../catalog/T33-self-type.md) |
| `Unpack` | Typed `**kwargs` for config-passing functions | [-> catalog/19](../catalog/T46-kwargs-typing.md) |

## Patterns

### A — `TypedDict` with `Required` / `NotRequired` for config

`TypedDict` gives dict-shaped data known keys with typed values.
`Required` and `NotRequired` (PEP 655) control which keys must appear.

```python
from typing import Required, NotRequired, TypedDict

class DBConfig(TypedDict):
    host: Required[str]
    port: Required[int]
    username: Required[str]
    password: Required[str]
    pool_size: NotRequired[int]
    ssl: NotRequired[bool]

def connect(cfg: DBConfig) -> None: ...

connect({                                     # OK
    "host": "localhost",
    "port": 5432,
    "username": "admin",
    "password": "secret",
})

connect({                                     # error: missing key "password"
    "host": "localhost",
    "port": 5432,
    "username": "admin",
})

connect({                                     # error: extra key "timeout"
    "host": "localhost",
    "port": 5432,
    "username": "admin",
    "password": "secret",
    "timeout": 30,
})
```

### B — Dataclass with defaults and `KW_ONLY`

Dataclasses provide a struct-like config with typed fields, default values,
and keyword-only enforcement to prevent positional mistakes.

```python
from dataclasses import dataclass, field, KW_ONLY

@dataclass
class ServerConfig:
    host: str
    port: int
    _: KW_ONLY
    workers: int = 4
    debug: bool = False
    allowed_origins: list[str] = field(default_factory=list)

cfg = ServerConfig("0.0.0.0", 8080, workers=8)     # OK
cfg = ServerConfig("0.0.0.0", 8080, True)           # error: too many positional args
cfg = ServerConfig("0.0.0.0")                       # error: missing required arg "port"
cfg.port                                             # OK — int
```

### C — Builder pattern with `Self` return

`Self` (PEP 673) lets fluent builder methods return the correct type even in
subclasses, enabling chained configuration.

```python
from __future__ import annotations
from typing import Self

class QueryBuilder:
    def __init__(self) -> None:
        self._table: str = ""
        self._limit: int | None = None
        self._filters: list[str] = []

    def table(self, name: str) -> Self:
        self._table = name
        return self

    def where(self, condition: str) -> Self:
        self._filters.append(condition)
        return self

    def limit(self, n: int) -> Self:
        self._limit = n
        return self

    def build(self) -> str:
        parts = [f"SELECT * FROM {self._table}"]
        if self._filters:
            parts.append("WHERE " + " AND ".join(self._filters))
        if self._limit is not None:
            parts.append(f"LIMIT {self._limit}")
        return " ".join(parts)

query = (
    QueryBuilder()
    .table("users")
    .where("active = true")
    .limit(10)
    .build()
)                                                    # OK — returns str

# Self ensures subclass chaining works:
class AuditQueryBuilder(QueryBuilder):
    def with_audit(self) -> Self:
        return self.where("audit_log IS NOT NULL")

audit_q = AuditQueryBuilder().table("events").with_audit().limit(5).build()  # OK
```

### D — Typed `**kwargs` with `Unpack`

`Unpack` (PEP 692) lets functions accept `**kwargs` with known keys and types,
bridging `TypedDict` configs to function signatures.

```python
from typing import TypedDict, Unpack

class RetryConfig(TypedDict, total=False):
    max_retries: int
    backoff: float
    timeout: int

def fetch(url: str, **kwargs: Unpack[RetryConfig]) -> str:
    return f"fetched {url}"

fetch("https://api.example.com", max_retries=3, backoff=1.5)   # OK
fetch("https://api.example.com", max_retries="three")          # error: expected int
fetch("https://api.example.com", unknown_key=True)              # error: unexpected kwarg
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| `TypedDict` config | Works with JSON/dict data; per-key optionality | No methods; no default values in the type itself |
| Dataclass config | Rich defaults, `KW_ONLY`, `frozen`; IDE support | Not dict-shaped; awkward for JSON deserialization |
| Builder with `Self` | Fluent API; subclass-safe chaining | More boilerplate; required fields not enforced at type level |
| `Unpack` `**kwargs` | Type-safe kwargs; familiar calling convention | Requires Python 3.12+ or `typing_extensions` |

## When to use which feature

**Use `TypedDict`** when your config comes from JSON, TOML, or external data where
the natural shape is a dictionary. `Required`/`NotRequired` gives per-key control.

**Use dataclasses** when config is constructed in Python code, benefits from
default values and methods, and should feel like a regular class.

**Use the builder pattern with `Self`** when construction is multi-step, optional
in many dimensions, and benefits from a fluent interface — especially when
subclassing is expected.

**Use `Unpack`** when you want to accept a typed set of keyword arguments without
requiring the caller to construct a config object explicitly.

**Combine them**: a `TypedDict` defines the config shape, a dataclass stores the
validated config, and a factory function bridges them using `Unpack`.

## When to use it

Use configuration and builder patterns when **you need type-checked config shapes,
validated required fields, or fluent multi-step construction**.

### Use config builders when:

- **Required vs optional fields must be distinguished**: Type checkers catch missing
  required keys and validate optional field types.
  ```python
  # TypedDict enforces required keys at type-check time
  class APIConfig(TypedDict):
      url: Required[str]
      timeout: NotRequired[int]

  def configure(cfg: APIConfig) -> None: ...

  configure({"url": "https://api.example.com"})              # OK
  configure({"timeout": 30})                                 # error: missing "url"
  ```

- **Default values and keyword-only args prevent positional mistakes**:
  ```python
  @dataclass
  class ServerConfig:
      host: str
      port: int
      _: KW_ONLY
      workers: int = 4

  ServerConfig("localhost", 8080)        # OK
  ServerConfig("localhost")              # error: missing "port"
  ServerConfig("localhost", 8080, 8)     # error: workers must be keyword-only
  ```

- **Fluent chaining improves readability**: Builder methods return `Self` for type-safe
  chaining, especially with subclasses.
  ```python
  class QueryBuilder:
      def select(self, cols: list[str]) -> Self: ...
      def where(self, cond: str) -> Self: ...
      def build(self) -> str: ...

  QueryBuilder().select(["id", "name"]).where("active=1").build()  # type-safe chain
  ```

### Don't use config builders when:

- **Config is trivial or all-optional**: Plain dicts work fine.
  ```python
  # Don't over-engineer simple cases
  def greet(name: str = "world") -> str  # just use this
      return f"Hello, {name}!"

  # Instead of:
  GreetBuilder().name("alice").build()
  ```

- **Config comes from untyped external sources**: JSON, user input, or environment
  variables need runtime validation; type checkers only see static types.
  ```python
  # TypedDict cannot validate runtime JSON
  config = json.load(open("config.json"))  # type: dict, not TypedDict

  # Use pydantic or similar for runtime validation
  from pydantic import BaseModel
  class Config(BaseModel): ...
  Config.model_validate(json_data)  # validates at runtime
  ```

- **APIs need dynamic keys**: `TypedDict` with total=False or dataclasses don't
  support arbitrary keys.
  ```python
  # This won't work with TypedDict:
  config = {"url": "...", "extra_key": "value"}  # error: extra key

  # Use dict[str, Any] or pydantic ConfigDict(arbitrary_types_allowed=True)
  ```

## Antipatterns when using config builders

### ❌ Overusing builders for simple configs

**Bad:** Creating a full builder for a few optional parameters adds boilerplate without
benefit.

```python
# ❌ Antipattern: over-engineered builder
class SimpleConfig:
    def __init__(self):
        self._name = ""
        self._count = 1
    def name(self, v: str) -> Self:
        self._name = v
        return self
    def count(self, v: int) -> Self:
        self._count = v
        return self
    def build(self) -> tuple[str, int]:
        return (self._name, self._count)

# Use this instead:
def make_config(name: str = "", count: int = 1) -> tuple[str, int]:
    return (name, count)
```

### ❌ Skipping validation in factories

**Bad:** Factory functions that validate at runtime but don't express constraints in
the type system.

```python
# ❌ Antipattern: validation not in types
class PortConfig(TypedDict):
    port: int

def validate_port(cfg: PortConfig) -> None:
    if cfg["port"] < 1 or cfg["port"] > 65535:
        raise ValueError("invalid port")

# Port 70000 passes type check, fails at runtime
validate_port({"port": 70000})
```

**✅ Fix with runtime validation library:**

```python
from annotated_types import Gt, Lt
from typing import Annotated

PortNumber = Annotated[int, Gt(0), Lt(65536)]

class PortConfig(TypedDict):
    port: PortNumber

# Still needs pydantic/polyfactory for actual runtime validation
```

### ❌ Using `Any` for config types

**Bad:** Using `dict[str, Any]` or `**kwargs` without types loses all type safety.

```python
# ❌ Antipattern: losing type safety
def connect(**kwargs: Any) -> None: ...

connect(host="localhost", prt=8080)  # typo not caught
connect(host="localhost", port="eighty-eighty")  # wrong type not caught
```

**✅ Fix with `TypedDict` + `Unpack`:**

```python
class ConnectConfig(TypedDict, total=False):
    host: str
    port: int

def connect(**kwargs: Unpack[ConnectConfig]) -> None: ...

connect(host="localhost", prt=8080)           # error: unexpected "prt"
connect(host="localhost", port="8080")        # error: expected int
```

### ❌ Confusing `total=True/False` in `TypedDict`

**Bad:** Mixing `total=True` with `NotRequired` or `total=False` with `Required`.

```python
# ❌ Antipattern: confusing semantics
class Config(TypedDict, total=True):
    url: Required[str]
    timeout: NotRequired[int]  # redundant: already required by total=True

# ✅ Prefer one style:
class Config(TypedDict):  # defaults to total=True
    url: Required[str]
    timeout: NotRequired[int]  # explicit intent

# or:
class Config(TypedDict, total=False):  # all optional
    url: str
    timeout: int
```

## Antipatterns with other techniques where config builders result in better code

### ❌ Magic numbers and strings without type constraints

**Bad:** Using raw literals everywhere; typos and invalid values surface at runtime.

```python
# ❌ Antipattern: magic values
LOG_LEVELS = ["debug", "info", "warn", "error"]

def create_logger(level="info", format="json") -> None:
    if level not in LOG_LEVELS:
        raise ValueError(f"invalid level: {level}")

create_logger(level="verbose")  # runtime error
create_logger(format="xml")     # accepted but unsupported
```

**✅ Fix with `TypedDict` + type narrowing:**

```python
class LoggerConfig(TypedDict, total=False):
    level: Literal["debug", "info", "warn", "error"]
    format: Literal["json", "text"]

def create_logger(**kwargs: Unpack[LoggerConfig]) -> None:
    level = kwargs.get("level", "info")
    format = kwargs.get("format", "json")

create_logger(level="verbose")  # error: not literal type
create_logger(format="xml")     # error: not literal type
```

### ❌ Deeply nested configs with scattered defaults

**Bad:** Config defaults spread across multiple files; hard to see the full picture.

```python
# ❌ Antipattern: scattered defaults
def create_server(config={}):
    host = config.get("host", os.getenv("HOST", "localhost"))
    port = config.get("port", int(os.getenv("PORT", "8080")))
    workers = config.get("workers", int(os.getenv("WORKERS", "4")))
    # ... harder to see all defaults in one place
```

**✅ Fix with dataclass as single source of truth:**

```python
@dataclass
class ServerConfig:
    host: str = field(default_factory=lambda: os.getenv("HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8080")))
    workers: int = field(default_factory=lambda: int(os.getenv("WORKERS", "4")))

# All defaults visible in one place, IDE shows defaults on hover
```

### ❌ Unvalidated `**kwargs` throughout codebase

**Bad:** Passing `**kwargs` everywhere; typos propagate silently.

```python
# ❌ Antipattern: unchecked kwargs
def create_endpoint(
    method: str,
    path: str,
    **kwargs  # anything goes, even invalid keys
):
    pass

def register_handler(
    endpoint,
    **kwargs  # forwards anything, including typos
):
    create_endpoint(**kwargs)

register_handler("GET", "/users", timout=30)  # typo accepted, fails silently
```

**✅ Fix with `TypedDict` + `Unpack`:**

```python
class EndpointConfig(TypedDict, total=False):
    method: Literal["GET", "POST", "PUT", "DELETE"]
    path: str
    timeout: int

class HandlerConfig(TypedDict, total=False):
    endpoint: Unpack[EndpointConfig]

def create_endpoint(**cfg: Unpack[EndpointConfig]) -> None: ...
def register_handler(**cfg: Unpack[HandlerConfig]) -> None: ...

# typos caught at type check time
register_handler(endpoint={"timout": 30})  # error: "timout" not in EndpointConfig
```

### ❌ Mutable default arguments in factories

**Bad:** Using mutable defaults like `[]` or `{}` causes shared state bugs.

```python
# ❌ Antipattern: mutable default
def create_filters(include: list = [], exclude: list = []):
    include.append("default")
    return include, exclude

a = create_filters()
b = create_filters()
# a[0] and b[0] are the same list! — shared mutable state
```

**✅ Fix with dataclass + `default_factory`:**

```python
@dataclass
class FiltersConfig:
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    _: KW_ONLY
    active: bool = True

# Each instance gets fresh lists
```

## Source anchors

- [PEP 589 — TypedDict](https://peps.python.org/pep-0589/)
- [PEP 655 — Required and NotRequired](https://peps.python.org/pep-0655/)
- [PEP 557 — Data Classes](https://peps.python.org/pep-0557/)
- [PEP 673 — Self type](https://peps.python.org/pep-0673/)
- [PEP 692 — Unpack for **kwargs](https://peps.python.org/pep-0692/)
- [mypy docs: TypedDict](https://mypy.readthedocs.io/en/stable/typed_dict.html)
