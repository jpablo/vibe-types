# Type Inference, Gradual Typing, and Any

> **Since:** Python 3.5+ (PEP 484)

## What it is

Python's type system is **gradual**: you can add type annotations incrementally, and untyped code coexists with typed code without breaking the checker. The type checker infers types for local variables, comprehensions, and expressions wherever possible, reducing annotation burden. The special type `Any` is the bridge between typed and untyped worlds — it is simultaneously compatible with every type (both as a subtype and a supertype), effectively disabling type checking wherever it appears.

Supporting mechanisms include `reveal_type()` for inspecting inferred types during development, `TYPE_CHECKING` for import-time-only annotations, stub files (`.pyi`) for adding types to untyped libraries, and the `py.typed` marker for declaring a package as fully typed.

## What constraint it enforces

**The checker infers types where annotations are absent and catches type mismatches in annotated code; `Any` explicitly opts out of checking, making it a controlled escape hatch rather than an error.** In `--strict` mode, the checker treats implicit `Any` (from missing annotations) as an error, closing the gradual typing loophole and requiring complete annotation coverage.

## Minimal snippet

```python
# Type inference: no annotations needed for locals
x = 42                    # inferred as int
y = [1, 2, 3]             # inferred as list[int]
z = {"a": 1, "b": 2}     # inferred as dict[str, int]

x = "hello"               # error — cannot assign str to int

# Any: the escape hatch
from typing import Any

def process(data: Any) -> Any:
    return data.whatever()   # OK — no checking on Any
    # No error even though .whatever() probably doesn't exist

result: int = process("hello")   # OK — Any is compatible with int
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Basic annotations** [-> catalog/01](T13-null-safety.md) | Annotations are the entry point for the type system. Without them, the checker falls back to inference or `Any`. |
| **TypeAlias** [-> catalog/17](T23-type-aliases.md) | Type aliases interact with inference: a bare `X = int` may be inferred as a variable rather than an alias if `TypeAlias` is not used. |
| **Annotated** [-> catalog/15](T26-refinement-types.md) | `Annotated[T, ...]` carries metadata alongside an inferred or explicit type. The base type `T` participates in inference normally. |
| **Protocol** [-> catalog/09](T07-structural-typing.md) | Protocols enable structural typing, which works with inference: if an object has the right methods, it satisfies the Protocol even without explicit annotation. |

## Gotchas and limitations

1. **Untyped code is `Any`-typed, not "unchecked."** A function without annotations has `Any` parameters and return type. This means it silently accepts and returns anything — no errors, but also no safety.

   ```python
   def add(a, b):          # implicitly: (a: Any, b: Any) -> Any
       return a + b

   result: int = add("hello", [1, 2])   # OK at check time, crash at runtime
   ```

2. **`Any` is contagious.** Once a value is `Any`, operations on it produce `Any` results. A single untyped function in a call chain can suppress errors throughout.

   ```python
   from typing import Any
   def load() -> Any: ...
   data = load()            # Any
   name = data["name"]      # Any — no KeyError checking
   length: int = len(name)  # OK — no type mismatch flagged
   ```

3. **`object` is not `Any`.** `object` is the top of the class hierarchy but is *not* an escape hatch. You can assign anything to `object`, but you cannot call arbitrary methods on it. Use `object` when you want "any type but still checked."

   ```python
   def f(x: object) -> None:
       x.foo()    # error — object has no attribute "foo"

   def g(x: Any) -> None:
       x.foo()    # OK — Any disables checking
   ```

4. **`--strict` mode varies by checker.** mypy's `--strict` enables ~15 flags (including `--disallow-untyped-defs`, `--warn-return-any`). pyright's strict mode uses different thresholds. The exact set of checks differs.

5. **`reveal_type()` is a development tool.** It causes a diagnostic note showing the inferred type. It should not remain in production code. In Python 3.11+, `reveal_type` is a real function in `typing`; before that, it existed only in checker-specific stubs.

6. **Stub files override source.** If a `.pyi` stub exists alongside a `.py` file, the checker uses the stub's types and ignores the source's annotations. This can be surprising when the stub is out of date.

7. **`TYPE_CHECKING` prevents runtime imports.** Code inside `if TYPE_CHECKING:` blocks is only visible to the checker. This avoids circular import issues but means the imported names are not available at runtime.

## Beginner mental model

Think of Python's type system as a **dimmer switch**, not an on/off toggle. At one extreme (no annotations), everything is `Any` and the checker is silent. At the other extreme (`--strict` mode), every function must be annotated and implicit `Any` is forbidden. You can set the dial anywhere in between, gradually increasing type coverage as the codebase matures.

`Any` is like a **hall pass** — it lets a value skip all type checks. This is useful for interacting with untyped libraries, but every `Any` in your code is a hole in the safety net. The goal of gradual adoption is to shrink the `Any`-typed surface over time.

## Example A — Gradual adoption strategy: adding types to a module boundary

```python
# --- Phase 1: Untyped legacy code (all Any) ---

def parse_config(path):          # (str) -> Any  (implicit)
    import json
    with open(path) as f:
        return json.load(f)

def get_db_url(config):          # (Any) -> Any  (implicit)
    return config["database"]["url"]

# No errors, no safety. Any mistake is a runtime crash.


# --- Phase 2: Type the public API boundary ---
from __future__ import annotations
from typing import Any

def parse_config(path: str) -> dict[str, Any]:    # return partially typed
    import json
    with open(path) as f:
        return json.load(f)                        # OK — json.load -> Any

def get_db_url(config: dict[str, Any]) -> str:
    url = config["database"]["url"]                # Any — not fully checked
    assert isinstance(url, str)                    # runtime guard
    return url                                     # OK — narrowed to str


# --- Phase 3: Replace Any with precise types ---
from typing import TypedDict

class DBConfig(TypedDict):
    url: str
    pool_size: int

class AppConfig(TypedDict):
    database: DBConfig
    debug: bool

def parse_config(path: str) -> AppConfig:
    import json
    with open(path) as f:
        return json.load(f)                        # OK — json.load returns Any

def get_db_url(config: AppConfig) -> str:
    return config["database"]["url"]               # OK — fully typed, str

# Now the checker catches mistakes:
def get_db_url_bad(config: AppConfig) -> int:
    return config["database"]["url"]               # error — str is not int
```

Each phase adds more type information without requiring a rewrite. The boundary between typed and untyped code moves inward over time.

## Example B — --strict mode catching implicit Any

```python
# mypy --strict or pyright strict mode

# --- This function has no annotations ---
def add(a, b):          # error (strict): Function is missing type annotations
    return a + b

# --- Fix: add annotations ---
def add_typed(a: int, b: int) -> int:
    return a + b        # OK

# --- Returning Any from a typed function ---
import json

def load_name(path: str) -> str:
    data = json.load(open(path))   # data is Any (json.load returns Any)
    return data["name"]            # error (strict): Returning Any from function
                                   # declared to return "str"

# --- Fix: narrow the type ---
def load_name_safe(path: str) -> str:
    data = json.load(open(path))
    name = data["name"]            # Any
    if not isinstance(name, str):
        raise TypeError(f"Expected str, got {type(name)}")
    return name                    # OK — narrowed to str via isinstance

# --- Using reveal_type for debugging ---
from typing import reveal_type     # Python 3.11+

x = [1, 2, 3]
reveal_type(x)                     # note: Type of "x" is "list[int]"

y = {"a": 1, "b": "two"}
reveal_type(y)                     # note: Type of "y" is "dict[str, int | str]"
```

Strict mode catches the holes that gradual typing leaves open by default. It is the recommended target for new projects and library code.

## Common type-checker errors and how to read them

### mypy (strict): `error: Function is missing a type annotation`

A function has no parameter or return annotations and `--disallow-untyped-defs` is enabled. Add type annotations to all parameters and the return type.

### mypy (strict): `error: Returning Any from function declared to return "str"`

The function's return annotation is `str`, but the return expression has type `Any`. Narrow the value with `isinstance`, `assert`, or a cast before returning.

### pyright: `Type of "x" is "Unknown"` (strict mode)

pyright uses `Unknown` (a stricter variant of `Any`) in strict mode to mark values whose types could not be inferred. Add an explicit annotation or narrow the type.

### mypy: `error: Call to untyped function "f" in typed context`

With `--disallow-untyped-calls`, calling a function that has no annotations from a fully-typed function is an error. Add annotations to the callee or use a stub.

### mypy: `note: Revealed type is "builtins.list[builtins.int]"`

Not an error — this is the output of `reveal_type()`. It shows the checker's inferred type for the expression. Use this to debug unexpected type behavior.

### pyright: `"Any" is not allowed in this context (reportAny)`

pyright's strict mode can flag explicit `Any` usage. Replace `Any` with a more specific type, or suppress the diagnostic if `Any` is intentional.

## Use-case cross-references

- [-> UC-04](../usecases/UC04-generic-constraints.md) Use type parameters instead of `Any` to write generic code that is still type-safe
- [-> UC-16](../usecases/UC16-nullability.md) Enforce non-nullability at the type level via strict mode

## When to Use It

Use gradual typing techniques when:

### 1. Integrating with untyped libraries

```python
# External library has no type stubs
import requests

response = requests.get("https://api.example.com")
data: Any = response.json()  # Explicit Any for boundary

# Narrow at the boundary before propagating
if isinstance(data, dict) and "id" in data:
    process_id(data["id"])
```

### 2. During incremental migration from untyped code

```python
# Legacy function being gradually typed
def process_data(items):  # Any parameters
    results = []
    for item in items:
        results.append(item * 2)  # Works with both str and list
    return results

# Add return type first, then parameters
def process_data(items: list[int]) -> list[int]:  # Partially typed
    ...
```

### 3. Handling truly dynamic data with runtime behavior

```python
from typing import Any

class DynamicObject:
    """Object with dynamic attributes at runtime"""
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        return self._data.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_data":
            super().__setattr__(name, value)
        else:
            self._data[name] = value
```

### 4. Writing adapters or proxies for external systems

```python
from typing import Any, Callable

def create_proxy(target: Any) -> Any:
    """Proxy that forwards all calls to target"""
    class Proxy:
        def __init__(self, tgt: Any) -> None:
            self._target = tgt
        def __getattr__(self, name: str) -> Any:
            return getattr(self._target, name)
    return Proxy(target)
```

### 5. Mocking and testing frameworks

```python
from unittest.mock import Mock

def test_with_mock() -> None:
    mock: Any = Mock()  # Mock is inherently dynamic
    mock.foo.return_value = 42
    assert mock.foo() == 42
```

## When NOT to Use It

Avoid gradual typing shortcuts when:

### 1. You know the shape upfront

```python
from typing import Any

# BAD: using Any when shape is known
def create_user(name: Any, email: Any) -> Any:
    return {"name": name, "email": email}

# GOOD: explicit types
def create_user(name: str, email: str) -> dict[str, str]:
    return {"name": name, "email": email}
```

### 2. In stable, fully-typed codebases

```python
from typing import Any

class UserService:
    def get_user(self, id: int) -> User:  # Fully typed API
        ...

# BAD: using Any in new code breaks the chain
def get_user_name(service: Any) -> str:
    user = service.get_user(1)  # No checking
    return user.name  # No checking
```

### 3. For lazy typing (procrastination)

```python
from typing import Any

# BAD: "I'll add types later" becomes permanent debt
def process_data(data: Any) -> Any:
    return data["value"] + data["extra"]

# GOOD: add types incrementally
def process_data(data: dict[str, Any]) -> Any:
    value = data["value"]  # At least we know it's a dict
    return value
```

### 4. When `object` suffices for "any value"

```python
from typing import Any

# BAD: Any when you just need "any object"
def log(value: Any) -> None:
    print(value)  # No checking

# GOOD: object allows any value but still checked
def log(value: object) -> None:
    print(value)  # Still can't call undefined methods
```

### 5. When type narrowing is straightforward

```python
from typing import Any

# BAD: Any prevents narrowing benefits
def get_length(value: Any) -> int:
    return len(value)  # No type checking on value

# GOOD: Union with narrowing
def get_length(value: str | list[int]) -> int:
    return len(value)  # Fully checked
```

## Antipatterns When Using Gradual Typing

### 1. The `Any` cascade — letting `Any` propagate

```python
from typing import Any

# BAD: Any at boundary pollutes everything downstream
def fetch_data() -> Any:
    import requests
    return requests.get("/api/data").json()

def extract_name(data: Any) -> str:
    return data["name"]  # No checking

name: str = extract_name(fetch_data())  # Errors not caught
```

### 2. Overusing `# type: ignore` without tracking

```python
from typing import Any

# BAD: silent suppression with no accountability
def process(x: Any) -> int:
    return x.value  # type: ignore

# GOOD: document the suppression
def process(x: Any) -> int:
    return x.value  # type: ignore[return-value] — TODO: add stub
```

### 3. Using `cast()` without justification

```python
from typing import cast, Any

# BAD: arbitrary type cast with no runtime check
data = fetch_json()
user = cast(User, data)  # No safety, crashes at runtime

# GOOD: cast with documented reason or runtime check
data = fetch_json()
if not isinstance(data, dict):
    raise TypeError("Expected dict")
user = cast(User, data)  # At least validated structure
```

### 4. Using `Any` for union types

```python
from typing import Any

# BAD: hiding complexity with Any
def process_value(value: Any) -> int:
    if isinstance(value, str):
        return len(value)
    if isinstance(value, int):
        return value * 2
    return 0

# GOOD: explicit union type
def process_value(value: str | int) -> int:
    if isinstance(value, str):
        return len(value)
    return value * 2
```

### 5. Ignoring `--strict` warnings permanently

```python
# BAD: disabling strict checks globally
# mypy.ini: disallow_untyped_defs = false

def add(a, b):  # Implicit Any parameters
    return a + b

result: int = add("hello", [1, 2])  # No error, runtime crash
```

### 6. Using `dict[str, Any]` instead of `TypedDict`

```python
from typing import Any

# BAD: lose key safety entirely
def create_config() -> dict[str, Any]:
    return {"port": 8080, "host": "localhost"}

def get_port(config: dict[str, Any]) -> int:
    return config["port"]  # No KeyError protection

# GOOD: TypedDict enforces structure
from typing import TypedDict

class Config(TypedDict):
    port: int
    host: str

def create_config() -> Config:
    return {"port": 8080, "host": "localhost"}

def get_port(config: Config) -> int:
    return config["port"]  # Checked keys
```

## Antipatterns With Other Techniques (Improved by Gradual Typing)

### 1. With TypedDict — `dict[str, Any]` vs typed dict

```python
from typing import Any

# BAD: dict[str, Any] loses all structure checking
def process_config(config: dict[str, Any]) -> int:
    port = config.get("port")
    return port * 1000  # No type checking on port

# GOOD: TypedDict provides structure checking
from typing import TypedDict

class PortConfig(TypedDict):
    port: int

def process_config(config: PortConfig) -> int:
    port = config["port"]  # Checked: must be int
    return port * 1000
```

### 2. With Protocols — `Any` vs structural typing

```python
from typing import Any, Protocol

class HasLength(Protocol):
    def __len__(self) -> int: ...

# BAD: Any prevents protocol matching
def get_size(obj: Any) -> int:
    return len(obj)  # No checking

# GOOD: Protocol enables structural typing
def get_size(obj: HasLength) -> int:
    return len(obj)  # Any object with __len__ works
```

### 3. With Type Guards — checking `Any` vs narrowing

```python
from typing import Any

# BAD: type guard on Any is meaningless
def is_string(value: Any) -> bool:
    return isinstance(value, str)

x: Any = get_value()
if is_string(x):
    x.unknown_method()  # No error — type guard didn't help

# GOOD: type guard works with Union
def is_string(value: object) -> bool:
    return isinstance(value, str)

y: str | int = get_value()
if is_string(y):
    y.upper()  # OK — narrowed to str
```

### 4. With generics — `Any` vs type parameters

```python
from typing import Any

# BAD: Any in generic function
def first_item(items: list[Any]) -> Any:
    return items[0]

result = first_item([1, 2, 3])
result.upper()  # Compiles, crashes at runtime (int has no .upper)

# GOOD: TypeVar preserves type information
from typing import TypeVar

T = TypeVar("T")

def first_item(items: list[T]) -> T:
    return items[0]

result = first_item([1, 2, 3])  # inferred as int
result.upper()  # Error: int has no attribute 'upper'
```

### 5. With Callable — `Any` vs callable signatures

```python
from typing import Any

# BAD: Any for callback parameters
def apply_callback(data: Any, callback: Any) -> Any:
    return callback(data)

result = apply_callback("hello", str.upper)
result + 1  # Compiles, crashes at runtime

# GOOD: Callable signature provides checking
from typing import Callable

def apply_callback(data: str, callback: Callable[[str], int]) -> int:
    return callback(data)

result = apply_callback("hello", str.__len__)  # Error: str -> int required
```

### 6. With Optional/Union — `Any` vs explicit nullability

```python
from typing import Any

# BAD: Any hides None handling
def get_name(user: Any) -> Any:
    return user.get("name")  # Could be None, dict, etc.

# GOOD: Optional provides explicit None handling
from typing import Optional

def get_name(user: dict[str, Optional[str]]) -> Optional[str]:
    return user.get("name")  # Fully checked

name = get_name({"name": None})  # type is Optional[str]
```

### 7. With Literal types — `Any` vs precise values

```python
from typing import Any

# BAD: Any for enum-like values
def set_mode(mode: Any) -> None:
    if mode == "read":
        ...

set_mode(123)  # No error

# GOOD: Literal enforces exact values
from typing import Literal

def set_mode(mode: Literal["read", "write"]) -> None:
    if mode == "read":
        ...

set_mode(123)  # Error: "int" not assignable to Literal["read", "write"]
```

## Use-case cross-references

- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
- [PEP 526 — Syntax for Variable Annotations](https://peps.python.org/pep-0526/)
- [typing module — Any](https://docs.python.org/3/library/typing.html#typing.Any)
- [mypy docs — Running mypy](https://mypy.readthedocs.io/en/stable/running_mypy.html)
- [mypy docs — The Any type](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#the-any-type)
- [pyright docs — Configuration](https://microsoft.github.io/pyright/#/configuration)
- [typing spec — Gradual typing](https://typing.readthedocs.io/en/latest/spec/concepts.html#gradual-types)
