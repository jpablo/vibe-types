# Final and ClassVar

> **Since:** `Final` Python 3.8 (PEP 591); `ClassVar` Python 3.5.3 (PEP 526) | **Backport:** `typing_extensions`

## What it is

`Final` marks a name as unreassignable: a variable declared `Final` cannot be rebound after initialization, a method decorated `@final` cannot be overridden in subclasses, and a class decorated `@final` cannot be subclassed. `ClassVar` marks an attribute as belonging to the class itself rather than to instances, preventing assignment through `self` and excluding the attribute from `__init__` parameters in dataclasses. Together, they give the type checker enough information to enforce immutability and class-versus-instance ownership at the annotation level.

## What constraint it enforces

**`Final` prevents reassignment, override, or subclassing after initial definition. `ClassVar` prevents instance-level assignment and excludes the attribute from dataclass-generated `__init__` signatures.**

## Minimal snippet

```python
from typing import Final, ClassVar

MAX_RETRIES: Final = 3
MAX_RETRIES = 5          # error — cannot assign to Final variable

class Base:
    class_name: ClassVar[str] = "Base"
    instance_val: int

    def greet(self) -> str:
        return "hello"

class Child(Base):
    class_name = "Child"         # OK — ClassVar can be reassigned on the class
    def greet(self) -> str:      # OK — not marked @final
        return "hi"

b = Base()
b.class_name = "nope"            # error — cannot assign ClassVar through instance
```

## Interaction with other features

| Feature | How it composes |
|-----|----|
| **Dataclasses** [-> catalog/06](T06-derivation.md) | `ClassVar` fields are excluded from the generated `__init__`, `__repr__`, and comparison methods. `Final` fields work but require `default` or `default_factory` since they cannot be reassigned. |
| **Protocol** [-> catalog/09](T07-structural-typing.md) | A Protocol can declare `ClassVar` members to require class-level attributes. `Final` is not meaningful in Protocol definitions since Protocols describe structural shape, not implementation. |
| **Enum** [-> catalog/05](T01-algebraic-data-types.md) | Enum members are implicitly final. Adding explicit `Final` annotations to enum members is redundant but harmless. |
| **Annotated** [-> catalog/15](T26-refinement-types.md) | `Final` and `ClassVar` can appear inside `Annotated` as the base type: `Annotated[Final[int], ...]` is valid in some contexts, though checker support varies. |

## Gotchas and limitations

1. **`Final` does not mean deeply immutable.** A `Final` list can still be mutated in place — only the binding is protected, not the object's contents.

   ```python
   ITEMS: Final = [1, 2, 3]
   ITEMS.append(4)     # OK at runtime and to the checker — the list is mutable
   ITEMS = [5, 6]      # error — cannot reassign Final
   ```

2. **`Final` must be initialized at declaration or in `__init__`.** You cannot declare a `Final` and assign it later in a different method.

   ```python
   class Config:
       name: Final[str]        # OK if assigned in __init__
       def __init__(self) -> None:
           self.name = "app"   # OK — first assignment in __init__
       def reset(self) -> None:
           self.name = "new"   # error — reassignment to Final
   ```

3. **`@final` on methods vs `Final` on variables.** These are different mechanisms. `@final` (the decorator) prevents override; `Final` (the type qualifier) prevents reassignment. Do not confuse them.

4. **`ClassVar` is not allowed in `NamedTuple`.** Since named tuples are purely instance-level, `ClassVar` fields are rejected.

5. **mypy and pyright disagree on some `Final` inference.** When you write `X: Final = 3`, mypy infers `int` while pyright infers `Literal[3]`. This matters if downstream code expects `Literal[3]` specifically.

6. **`ClassVar` fields cannot have default values via dataclass `field()` with `init=True`.** Since `ClassVar` is excluded from `__init__`, setting `init=True` on a `ClassVar` field is contradictory.

## Beginner mental model

`Final` is a **padlock on a name**: once you snap it shut at initialization, nobody can rebind that name to a different value. `ClassVar` is a **sign on the door** saying "this attribute lives on the class, not on individual instances." Dataclasses read these signs and skip `ClassVar` fields when building the constructor.

## Example A — Application constants with Final preventing reassignment

```python
from typing import Final, final

# Module-level constants
API_BASE: Final = "https://api.example.com"
TIMEOUT_S: Final[float] = 30.0

API_BASE = "https://other.com"   # error — cannot assign to Final

# Final method — cannot be overridden
class Repository:
    @final
    def connect(self) -> None:
        """Establish a database connection. Subclasses must not override."""
        print("connecting...")

class CachedRepository(Repository):
    def connect(self) -> None:    # error — cannot override final method
        print("cached connect")

# Final class — cannot be subclassed
@final
class Singleton:
    _instance: "Singleton | None" = None

class ExtendedSingleton(Singleton):  # error — cannot subclass final class
    pass
```

**Why this matters:** `Final` constants let the checker inline known values, and `@final` methods/classes let frameworks guarantee their internal invariants are not broken by subclasses.

## Example B — ClassVar separating class-level config from instance data

```python
from dataclasses import dataclass, field
from typing import ClassVar

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
client.max_connections = 50      # error — cannot assign ClassVar through instance
HttpClient.max_connections = 50  # OK — assigned on the class itself

# Combining Final and ClassVar
@dataclass
class AppConfig:
    name: str
    VERSION: ClassVar[Final[str]] = "1.0.0"   # class-level, unreassignable

AppConfig.VERSION = "2.0.0"     # error — Final prevents reassignment
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
  @final
  class Singleton:
      pass
  ```

- **Configuration objects**: When config values are fixed at runtime
  ```python
  from dataclasses import dataclass
  from typing import Final

  @dataclass
  class Config:
      host: Final[str]
      port: Final[int]
  ```

## When NOT to Use

- **Mutable collections**: When you need to modify the contents
  ```python
  # ❌ Don't use Final here if you need append()
  buffer: Final[list[int]] = []
  buffer.append(1)  # OK but misleading — Final only prevents reassignment
  ```

- **Runtime-modified state**: When attribute values change based on runtime logic
  ```python
  # ❌ Don't use Final for counters
  class Counter:
      count: Final[int] = 0  # Can't increment later
      def increment(self) -> None:
          self.count += 1    # error — cannot reassign Final
  ```

- **Dynamic configuration**: When config values may vary per environment
  ```python
  # ❌ Use without Final if values vary by environment
  from os import environ
  DEBUG: Final[bool] = environ.get("DEBUG", "false") == "true"
  ```

- **Instance attributes with mutable objects**: When you only want to protect the reference
  ```python
  class Cache:
      data: Final[dict[str, int]] = {}
      # ❌ data.clear() still works — only data = {} is blocked
  ```

## Antipatterns

### ❌ Shallow Final on mutable objects
```python
from typing import Final

CONFIG: Final[dict] = {"host": "localhost"}
CONFIG["host"] = "other.com"  # ✅ Allowed! Final only prevents rebinding

# ✅ Use a frozen dataclass or tuple for true immutability
from dataclasses import dataclass, field
from typing import FrozenSet

@dataclass(frozen=True)
class Config:
    host: str
```

### ❌ Final combined with late initialization
```python
from typing import Final

class Service:
    api_key: Final[str]
    def __init__(self) -> None:
        self.api_key = "xxx"  # OK
    def refresh_key(self) -> None:
        self.api_key = self._fetch_key()  # error — reassigning Final
```

### ❌ ClassVar on instance-specific data
```python
from typing import ClassVar

class User:
    name: ClassVar[str] = "Alice"  # ❌ Shared across all instances!
    def greet(self) -> str:
        return f"Hello, {self.name}"

u1 = User()
u2 = User()
User.name = "Bob"  # Changes name for all users
```

### ❌ Overusing @final on implementation details
```python
from typing import final

class Repository:
    @final
    def _connect(self) -> None:  # ❌ _method already private
        pass

    @final
    def authenticate(self) -> None:  # ❌ Over-constraining public API
        pass
```

## When This Technique Improves Other Patterns

### ❌ Without Final (reassignment possible)
```python
MAX_CONNECTIONS = 100

def initialize():
    MAX_CONNECTIONS = 200  # ❌ Silently shadows the constant
```

### ✅ With Final (reassignment blocked)
```python
from typing import Final

MAX_CONNECTIONS: Final[int] = 100

def initialize():
    MAX_CONNECTIONS = 200  # error — cannot assign to final name
```

### ❌ Without ClassVar (instance vs class confusion)
```python
class Handler:
    registry = []  # ❌ Each instance gets its own list via __init__

h1 = Handler()
h2 = Handler()
Handler.registry.append("x")  # Does not update instances
```

### ✅ With ClassVar (shared state explicit)
```python
from typing import ClassVar

class Handler:
    registry: ClassVar[list] = []

Handler.registry.append("x")  # Shared across all instances
```

### ❌ Without @final (unintended override)
```python
class BaseModel:
    def save(self) -> None:
        self._hook()

    def _hook(self) -> None:
        pass

class MaliciousModel(BaseModel):
    @property
    def _hook(self):  # ❌ Can accidentally break parent behavior
        raise Exception()
```

### ✅ With @final (override prevention)
```python
from typing import final

class BaseModel:
    def save(self) -> None:
        self._hook()

    @final
    def _hook(self) -> None:
        pass

class SafeModel(BaseModel):
    def _hook(self) -> None:  # error — cannot override final method
        pass
```

## Use-case cross-references

- [-> UC-06](../usecases/UC06-immutability.md) — Configuration objects where `Final` ensures immutable settings and `ClassVar` manages shared defaults.
- [-> UC-06](../usecases/UC06-immutability.md) Use `Final` and `ClassVar` to encode immutability constraints in data structures and class boundaries

## Source anchors

- [PEP 591 — Adding a final qualifier to typing](https://peps.python.org/pep-0591/) — `Final` and `@final`
- [PEP 526 — Syntax for Variable Annotations](https://peps.python.org/pep-0526/) — `ClassVar`
- [typing spec — Final](https://typing.readthedocs.io/en/latest/spec/qualifiers.html#final)
- [typing spec — ClassVar](https://typing.readthedocs.io/en/latest/spec/class-compat.html#classvar)
- [mypy docs — Final names, methods and classes](https://mypy.readthedocs.io/en/stable/final_attrs.html)
