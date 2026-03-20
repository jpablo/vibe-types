# Configuration and Builder Patterns

## The constraint

Required fields must be provided and optional fields must have correct types,
so that configuration objects have validated shapes at check time — preventing
missing-key errors and type mismatches that surface only at runtime.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| `TypedDict` (Required/NotRequired) | Dict-shaped config with per-key optionality | [-> catalog/03](../catalog/03-typeddict.md) |
| Dataclasses with defaults | Struct-like config with default values and `KW_ONLY` | [-> catalog/06](../catalog/06-dataclasses-typing.md) |
| `@overload` | Multiple constructor signatures for config factories | [-> catalog/11](../catalog/11-callable-types-overload.md) |
| `Annotated` | Carry validation metadata alongside types | [-> catalog/15](../catalog/15-annotated-metadata.md) |
| `Self` | Fluent builder methods that return the same type | [-> catalog/16](../catalog/16-self-type.md) |
| `Unpack` | Typed `**kwargs` for config-passing functions | [-> catalog/19](../catalog/19-unpack-kwargs-typing.md) |

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

## Source anchors

- [PEP 589 — TypedDict](https://peps.python.org/pep-0589/)
- [PEP 655 — Required and NotRequired](https://peps.python.org/pep-0655/)
- [PEP 557 — Data Classes](https://peps.python.org/pep-0557/)
- [PEP 673 — Self type](https://peps.python.org/pep-0673/)
- [PEP 692 — Unpack for **kwargs](https://peps.python.org/pep-0692/)
- [mypy docs: TypedDict](https://mypy.readthedocs.io/en/stable/typed_dict.html)
