# Final and ClassVar

> **Since:** `Final` Python 3.8 (PEP 591); `ClassVar` Python 3.6 (PEP 526) | **Backport:** `typing_extensions`

## What it is

`Final` marks a name as unreassignable: a variable declared `Final` cannot be rebound after initialization, a method decorated `@final` cannot be overridden in subclasses, and a class decorated `@final` cannot be subclassed. `ClassVar` marks an attribute as belonging to the class itself rather than to instances, preventing assignment through `self` and excluding the attribute from `__init__` parameters in dataclasses. Together, they give the type checker enough information to enforce immutability and class-versus-instance ownership at the annotation level.

## What constraint it enforces

**`Final` prevents reassignment, override, or subclassing after initial definition. `ClassVar` prevents instance-level assignment and excludes the attribute from dataclass-generated `__init__` signatures.**

## Minimal snippet

```python
from typing import ClassVar, Final, override

MAX_RETRIES: Final = 3
MAX_RETRIES = 5          # error: "MAX_RETRIES" is declared as Final and cannot be reassigned

class Base:
    class_name: ClassVar[str] = "Base"
    instance_val: int = 0

    def greet(self) -> str:
        return "hello"

class Child(Base):
    class_name = "Child"         # OK — ClassVar can be redefined on a subclass
    @override
    def greet(self) -> str:      # OK — not marked @final
        return "hi"

b = Base()
b.class_name = "nope"            # error: "class_name" cannot be assigned through a class instance because it is a ClassVar
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dataclasses** [-> T06](T06-derivation.md) | `ClassVar` fields are excluded from the generated `__init__`, `__repr__`, and comparison methods. `Final` fields are ordinary instance fields (no default required): they are set once via `__init__` and protected from reassignment afterwards. |
| **Protocol** [-> T07](T07-structural-typing.md) | A Protocol can declare `ClassVar` members to require class-level attributes. `Final` is not meaningful in Protocol definitions since Protocols describe structural shape, not implementation. |
| **Enum** [-> T01](T01-algebraic-data-types.md) | Enum members are implicitly final. Adding explicit `Final` annotations to enum members is redundant but harmless. |
| **Annotated** [-> T26](T26-refinement-types.md) | `Final` must wrap `Annotated`, not the other way around: `Final[Annotated[int, Meta()]]` is valid, while `Annotated[Final[int], Meta()]` is rejected by the typing spec. |

## Gotchas and limitations

1. **`Final` does not mean deeply immutable.** A `Final` list can still be mutated in place — only the binding is protected, not the object's contents.

   ```python
   from typing import Final

   ITEMS: Final = [1, 2, 3]
   ITEMS.append(4)     # OK at runtime and to the checker — the list is mutable
   ITEMS = [5, 6]      # error: "ITEMS" is declared as Final and cannot be reassigned
   ```

2. **`Final` must be initialized at declaration or in `__init__`.** You cannot declare a `Final` and assign it later in a different method.

   ```python
   from typing import Final

   class Config:
       name: Final[str]        # OK if assigned in __init__
       def __init__(self) -> None:
           self.name = "app"   # OK — first assignment in __init__
       def reset(self) -> None:
           self.name = "new"   # error: "name" is declared as Final and cannot be reassigned
   ```

3. **`@final` on methods vs `Final` on variables.** These are different mechanisms. `@final` (the decorator) prevents override; `Final` (the type qualifier) prevents reassignment. Do not confuse them.

4. **`ClassVar` is not allowed in `NamedTuple`.** Since named tuples are purely instance-level, `ClassVar` fields are rejected.

5. **`Final` without an explicit type infers a `Literal`.** Both mypy and pyright infer `X: Final = 3` as `Literal[3]`, not `int` — a final name is implicitly narrowed to its literal initializer. This is usually what you want; write `X: Final[int] = 3` if downstream code should see plain `int`.

6. **`ClassVar` fields cannot have default values via dataclass `field()` with `init=True`.** Since `ClassVar` is excluded from `__init__`, setting `init=True` on a `ClassVar` field is contradictory.

## Beginner mental model

`Final` is a **padlock on a name**: once you snap it shut at initialization, nobody can rebind that name to a different value. `ClassVar` is a **sign on the door** saying "this attribute lives on the class, not on individual instances." Dataclasses read these signs and skip `ClassVar` fields when building the constructor.

## Example A — Application constants with Final preventing reassignment

```python
from typing import Final, final

# Module-level constants
API_BASE: Final = "https://api.example.com"
TIMEOUT_S: Final[float] = 30.0

API_BASE = "https://other.com"   # error: "API_BASE" is declared as Final and cannot be reassigned

# Final method — cannot be overridden
class Repository:
    @final
    def connect(self) -> None:
        """Establish a database connection. Subclasses must not override."""
        print("connecting...")

class CachedRepository(Repository):
    def connect(self) -> None:    # error: Method "connect" cannot override final method defined in class "Repository"
        print("cached connect")

# Final class — cannot be subclassed
@final
class Singleton:
    _instance: "Singleton | None" = None

class ExtendedSingleton(Singleton):  # error: Base class "Singleton" is marked final and cannot be subclassed
    pass
```

**Why this matters:** `Final` constants let the checker inline known values, and `@final` methods/classes let frameworks guarantee their internal invariants are not broken by subclasses.

## Example B — ClassVar separating class-level config from instance data

```python
from dataclasses import dataclass
from typing import ClassVar, Final

@dataclass
class HttpClient:
    base_url: str
    timeout: float = 30.0
    # ClassVar — shared across all instances, excluded from __init__
    max_connections: ClassVar[int] = 100
    _registry: ClassVar[list["HttpClient"]] = []

    def __post_init__(self) -> None:
        HttpClient._registry.append(self)

# The generated __init__ signature is:
#   def __init__(self, base_url: str, timeout: float = 30.0) -> None
# max_connections and _registry are NOT parameters.

client = HttpClient("https://api.example.com")
client.max_connections = 50      # error: "max_connections" cannot be assigned through a class instance because it is a ClassVar
HttpClient.max_connections = 50  # OK — assigned on the class itself

# Combining Final and ClassVar
@dataclass
class AppConfig:
    name: str
    VERSION: ClassVar[Final[str]] = "1.0.0"   # class-level, unreassignable

AppConfig.VERSION = "2.0.0"     # error: "VERSION" is declared as Final and cannot be reassigned
```

**Pattern:** Use `ClassVar` for shared configuration, counters, and registries that should not appear in the constructor or differ per instance. Combine with `Final` when the class-level value should never change.

## Common type-checker errors and how to read them

### `error: Cannot assign to final name "X"` (mypy)

You tried to reassign a `Final` variable. The fix is to not reassign, or remove the `Final` qualifier if mutability is intended.

### `error: Cannot override final attribute "method"` (mypy)

A subclass tried to override a method or attribute decorated with `@final`. Either remove the override or remove `@final` from the parent.

### `error: Cannot inherit from final class "ClassName"` (mypy)

A class tried to subclass a `@final` class. Use composition instead of inheritance.

### `Cannot assign member "x" for type "Cls"` / `Cannot assign to class variable "x" via instance` (pyright)

You tried to assign a `ClassVar` attribute through `self.x = ...`. Assign through the class name instead: `Cls.x = ...`.

### `error: ClassVar can only be used for assignments in class body` (mypy)

`ClassVar` annotations are only valid at class scope, not inside functions or as local variables.

## When to Use

- **Module-level constants**: When values are set once and should never be reassigned

  ```python
  from typing import Final

  API_KEY: Final[str] = "sk-xxx"
  MAX_RETRIES: Final[int] = 3
  ```

- **Class-level shared state**: When an attribute belongs to the class, not instances

  ```python
  from typing import ClassVar

  class Logger:
      _instance_count: ClassVar[int] = 0
  ```

- **Stable method contracts**: When a method should not be overridden by subclasses

  ```python
  from typing import final

  class Base:
      @final
      def authenticate(self) -> None:
          pass
  ```

- **Sealed classes**: When subclassing should be explicitly prohibited

  ```python
  from typing import final

  @final
  class Singleton:
      pass
  ```

- **Configuration objects**: When config values are fixed for the object's lifetime

  ```python
  from dataclasses import dataclass
  from typing import Final

  @dataclass
  class Config:
      host: Final[str]
      port: Final[int]
  ```

## When NOT to Use

- **Counters and other runtime-modified state**: When attribute values change based on runtime logic

  ```python
  from typing import Final

  # ❌ Don't use Final for values that must change
  class Counter:
      count: Final[int] = 0  # Can't increment later
      def increment(self) -> None:
          self.count += 1    # error: "count" is declared as Final and cannot be reassigned
  ```

- **Attributes that are refreshed later**: `Final` permits exactly one assignment (in `__init__`)

  ```python
  from typing import Final

  # ❌ Final on an attribute the class itself needs to refresh
  class Service:
      api_key: Final[str]
      def __init__(self) -> None:
          self.api_key = "xxx"              # OK — first assignment
      def _fetch_key(self) -> str:
          return "new-key"
      def refresh_key(self) -> None:
          self.api_key = self._fetch_key()  # error: "api_key" is declared as Final and cannot be reassigned
  ```

- **Dynamic configuration**: When the value is computed per environment, `Final` only documents that it won't be rebound afterwards — don't reach for it if the value is meant to change at runtime

  ```python
  from os import environ
  from typing import Final

  # OK only because DEBUG is read once at startup and never changes
  DEBUG: Final[bool] = environ.get("DEBUG", "false") == "true"
  ```

- **Deep immutability of mutable objects**: `Final` only protects the reference, not the contents

  ```python
  from dataclasses import dataclass
  from typing import Final

  CONFIG: Final[dict[str, str]] = {"host": "localhost"}
  CONFIG["host"] = "other.com"  # Allowed! Final only prevents rebinding

  # ✅ Use a frozen dataclass or frozenset for true immutability
  @dataclass(frozen=True)
  class Config:
      host: str

  ALLOWED_HOSTS: Final[frozenset[str]] = frozenset({"localhost"})
  ```

## Antipatterns

### ❌ ClassVar on instance-specific data

```python
from typing import ClassVar

class User:
    name: ClassVar[str] = "Alice"  # ❌ shared across ALL instances
    def greet(self) -> str:
        return f"Hello, {self.name}"

User.name = "Bob"  # changes the name for every User
```

Instance-specific data belongs in instance attributes (or dataclass fields) — `ClassVar` makes every instance share one value.

### ❌ Overusing @final on implementation details

```python
from typing import final

class Repository:
    @final
    def _connect(self) -> None:  # ❌ underscore methods are already private by convention
        pass
```

Reserve `@final` for public contract methods where an override would break invariants; locking down every private helper adds noise without adding safety.

## When This Technique Improves Other Patterns

### ❌ Without Final (nothing stops rebinding)

```python
max_connections = 100   # intended as a constant…
max_connections = 200   # …but rebinding is silently allowed
```

### ✅ With Final (reassignment blocked)

```python
from typing import Final

MAX_CONNECTIONS: Final[int] = 100
MAX_CONNECTIONS = 200   # error: "MAX_CONNECTIONS" is declared as Final and cannot be reassigned
```

### ❌ Without ClassVar (shared state is implicit and untyped)

```python
class Handler:
    registry = []  # inferred as list[Unknown]; nothing marks it as class-level
```

### ✅ With ClassVar (shared state explicit and typed)

```python
from typing import ClassVar

class Handler:
    registry: ClassVar[list[str]] = []

Handler.registry.append("x")  # shared across all instances, fully typed
```

### ❌ Without @final (critical hook can be overridden)

```python
from typing import override

class BaseModel:
    def save(self) -> None:
        self._hook()

    def _hook(self) -> None:
        pass

class FragileModel(BaseModel):
    @override
    def _hook(self) -> None:   # nothing stops this override
        raise RuntimeError("save is now broken")
```

### ✅ With @final (override rejected at check time)

```python
from typing import final

class BaseModel:
    def save(self) -> None:
        self._hook()

    @final
    def _hook(self) -> None:
        pass

class SafeModel(BaseModel):
    def _hook(self) -> None:  # error: Method "_hook" cannot override final method defined in class "BaseModel"
        pass
```

## Use-case cross-references

- [-> UC06](../usecases/UC06-immutability.md) — Configuration objects where `Final` ensures immutable settings and `ClassVar` manages shared defaults.

## Source anchors

- [PEP 591 — Adding a final qualifier to typing](https://peps.python.org/pep-0591/) — `Final` and `@final`
- [PEP 526 — Syntax for Variable Annotations](https://peps.python.org/pep-0526/) — `ClassVar`
- [typing spec — Final](https://typing.readthedocs.io/en/latest/spec/qualifiers.html#final)
- [typing spec — ClassVar](https://typing.readthedocs.io/en/latest/spec/class-compat.html#classvar)
- [mypy docs — Final names, methods and classes](https://mypy.readthedocs.io/en/stable/final_attrs.html)
