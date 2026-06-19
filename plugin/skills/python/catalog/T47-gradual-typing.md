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
z = {"a": 1, "b": 2}      # inferred as dict[str, int]

x = "hello"               # mypy flags this (x was inferred as int);
                          # pyright widens the declared type of x to int | str

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
| **Basic annotations** [-> T13](T13-null-safety.md) | Annotations are the entry point for the type system. Without them, the checker falls back to inference or `Any`. |
| **TypeAlias** [-> T23](T23-type-aliases.md) | Type aliases interact with inference: a bare `X = int` may be inferred as a variable rather than an alias if `TypeAlias` is not used. |
| **Annotated** [-> T26](T26-refinement-types.md) | `Annotated[T, ...]` carries metadata alongside an inferred or explicit type. The base type `T` participates in inference normally. |
| **Protocol** [-> T07](T07-structural-typing.md) | Protocols enable structural typing, which works with inference: if an object has the right methods, it satisfies the Protocol even without explicit annotation. |

## Gotchas and limitations

1. **Untyped code is `Any`-typed, not "unchecked."** A function without annotations has `Any` parameters and return type. In basic mode it silently accepts and returns anything — no errors, but also no safety. In strict mode the missing annotations themselves are flagged:

   ```python
   def add(a, b):          # error: type annotation is missing for parameter "a" (and "b") (strict)
       return a + b        # error: return type is unknown (strict)

   result: int = add("hello", [1, 2])   # error: type of "result" is unknown (strict)
                                        # basic mode: accepted — and crashes at runtime
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
   from typing import Any

   def f(x: object) -> None:
       x.foo()    # error: cannot access attribute "foo" for class "object"

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
# expect-error — under strict mode, every implicit Any below is flagged
# --- Phase 1: Untyped legacy code (all Any) ---

def parse_config(path):          # (str) -> Any  (implicit)
    import json
    with open(path) as f:
        return json.load(f)

def get_db_url(config):          # (Any) -> Any  (implicit)
    return config["database"]["url"]

# In basic mode: no errors, no safety. Any mistake is a runtime crash.
```

```python
# --- Phase 2: Type the public API boundary ---
import json
from typing import Any

def parse_config(path: str) -> dict[str, Any]:    # return partially typed
    with open(path) as f:
        return json.load(f)                        # OK — json.load returns Any

def get_db_url(config: dict[str, Any]) -> str:
    url = config["database"]["url"]                # Any — not fully checked
    assert isinstance(url, str)                    # runtime guard
    return url                                     # OK — narrowed to str
```

```python
# --- Phase 3: Replace Any with precise types ---
import json
from typing import TypedDict

class DBConfig(TypedDict):
    url: str
    pool_size: int

class AppConfig(TypedDict):
    database: DBConfig
    debug: bool

def parse_config(path: str) -> AppConfig:
    with open(path) as f:
        return json.load(f)                        # OK — json.load returns Any

def get_db_url(config: AppConfig) -> str:
    return config["database"]["url"]               # OK — fully typed, str

# Now the checker catches mistakes:
def get_db_url_bad(config: AppConfig) -> int:
    return config["database"]["url"]               # error: "str" is not assignable to "int"
```

Each phase adds more type information without requiring a rewrite. The boundary between typed and untyped code moves inward over time.

## Example B — Strict mode catching implicit Any

```python
# mypy --strict or pyright strict mode

# --- This function has no annotations ---
def add(a, b):          # error: type annotation is missing for parameters "a" and "b"
    return a + b        # error: return type is unknown

# --- Fix: add annotations ---
def add_typed(a: int, b: int) -> int:
    return a + b        # OK

# --- Returning Any from a typed function ---
import json

def load_name(path: str) -> str:
    data = json.load(open(path))   # data is Any (json.load returns Any)
    return data["name"]            # mypy --strict: "Returning Any from function
                                   # declared to return str" (pyright stays silent —
                                   # explicit Any propagates without complaint)

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

### pyright (strict): `Type of parameter "x" is unknown (reportUnknownParameterType)`

pyright never flags an *explicit* `Any` — writing `x: Any` is always accepted. What strict mode flags is *implicit* `Any`: missing or un-inferable annotations, surfaced through `reportMissingParameterType` and the `reportUnknown*` family. (A rule that also bans explicit `Any`, `reportAny`, exists only in the basedpyright fork — it is not part of pyright.)

## Use-case cross-references

- [-> UC-04](../usecases/UC04-generic-constraints.md) Use type parameters instead of `Any` to write generic code that is still type-safe
- [-> UC-16](../usecases/UC16-nullability.md) Enforce non-nullability at the type level via strict mode

## When to Use It

Use gradual typing techniques when:

### 1. Integrating with untyped libraries

```python
import json
from typing import Any

def process_id(value: int) -> None:
    print(f"id={value}")

payload: Any = json.loads('{"id": 1}')   # explicit Any at the untyped boundary

# Narrow before propagating — don't let Any spread
raw_id: Any = payload["id"]
if isinstance(raw_id, int):
    process_id(raw_id)                   # OK — narrowed to int
```

### 2. Gradually typing legacy functions

```python
# expect-error — the untyped original is flagged under strict mode
# ❌ Before: untyped legacy helper
def process_data(items):
    results = []
    for item in items:
        results.append(item * 2)
    return results

# ✅ After: annotate the boundary first; the body is checked for free
def process_data_typed(items: list[int]) -> list[int]:
    results: list[int] = []
    for item in items:
        results.append(item * 2)
    return results
```

### 3. Objects with dynamic attributes

```python
from typing import Any, override

class DynamicObject:
    """Object with dynamic attributes at runtime"""
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        return self._data.get(name)

    @override
    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_data":
            super().__setattr__(name, value)
        else:
            self._data[name] = value
```

### 4. Proxies that forward everything

```python
from typing import Any

def create_proxy(target: Any) -> Any:
    """Proxy that forwards all attribute access to target"""
    class Proxy:
        def __init__(self, tgt: Any) -> None:
            self._target = tgt
        def __getattr__(self, name: str) -> Any:
            return getattr(self._target, name)
    return Proxy(target)
```

### 5. Mocking and testing frameworks

```python
from typing import Any
from unittest.mock import Mock

def test_with_mock() -> None:
    mock: Any = Mock()  # Mock is inherently dynamic
    mock.foo.return_value = 42
    assert mock.foo() == 42
```

## When NOT to Use It

Avoid `Any` when:

### 1. The data shape is known

```python
from typing import Any

# BAD: using Any when shape is known
def create_user(name: Any, email: Any) -> Any:
    return {"name": name, "email": email}

# GOOD: explicit types
def create_user_ok(name: str, email: str) -> dict[str, str]:
    return {"name": name, "email": email}
```

### 2. In stable, fully-typed codebases

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class User:
    name: str

class UserService:
    def get_user(self, user_id: int) -> User: ...

# BAD: Any in new code breaks the typed chain
def get_user_name_bad(service: Any) -> str:
    return service.get_user(1).nme    # typo not caught — Any disables checking

# GOOD: keep the chain typed
def get_user_name(service: UserService) -> str:
    return service.get_user(1).name   # fully checked
```

### 3. "I'll add types later"

```python
from typing import Any

# BAD: blanket Any becomes permanent debt
def process_data_any(data: Any) -> Any:
    return data["value"] + data["extra"]

# GOOD: add types incrementally — type what you know now
def process_data_dict(data: dict[str, Any]) -> Any:
    value = data["value"]  # at least the dict shape is checked
    return value
```

### 4. When you just need "any object"

```python
from typing import Any

# BAD: Any when you just need "any object"
def log_any(value: Any) -> None:
    value.upper()  # no error — Any disables checking (crashes for non-str values)

# GOOD: object accepts any value but stays checked
def log_object(value: object) -> None:
    print(value)   # OK — only operations valid for every object are allowed
```

### 5. When type narrowing is straightforward

```python
from typing import Any

# BAD: Any prevents narrowing benefits
def get_length_any(value: Any) -> int:
    return len(value)  # no type checking on value

# GOOD: Union with narrowing
def get_length(value: str | list[int]) -> int:
    return len(value)  # fully checked
```

## Antipatterns When Using Gradual Typing

### 1. The `Any` cascade — letting `Any` propagate

```python
import json
from typing import Any

# BAD: Any at the boundary pollutes everything downstream
def fetch_data() -> Any:
    return json.loads('{"name": "x"}')

def extract_name(data: Any) -> str:
    return data["name"]  # no checking

name: str = extract_name(fetch_data())  # errors not caught
```

### 2. Unchecked `cast` instead of validation

```python
from typing import Any, cast

def fetch_json() -> dict[str, Any]: ...
def load_raw() -> Any: ...
class User: ...

# BAD: arbitrary type cast with no runtime check
data = fetch_json()
user = cast(User, data)  # no safety — crashes later at runtime

# GOOD: cast only after a runtime check (or use a validation library)
raw = load_raw()
if not isinstance(raw, dict):
    raise TypeError("Expected dict")
user_checked = cast(User, raw)  # at least the structure was validated
```

### 3. Hiding unions behind `Any`

```python
from typing import Any

# BAD: hiding complexity with Any
def process_value_bad(value: Any) -> int:
    if isinstance(value, str):
        return len(value)
    if isinstance(value, int):
        return value * 2
    return 0

# GOOD: explicit union type
def process_value_good(value: str | int) -> int:
    if isinstance(value, str):
        return len(value)
    return value * 2
```

### 4. Loosening the config instead of fixing the code

```python
# expect-error — strict mode still flags the implicit Any below
# BAD: disabling strict checks globally
# mypy.ini: disallow_untyped_defs = false

def add(a, b):  # implicit Any parameters
    return a + b

result: int = add("hello", [1, 2])  # silenced once checks are off — runtime crash
```

### 5. `dict[str, Any]` config bags instead of TypedDict

```python
from typing import Any, TypedDict

# BAD: lose key and value safety entirely
def create_config_bad() -> dict[str, Any]:
    return {"port": 8080, "host": "localhost"}

def get_port_bad(config: dict[str, Any]) -> int:
    return config["port"]  # no KeyError protection, value is Any

# GOOD: TypedDict enforces structure
class Config(TypedDict):
    port: int
    host: str

def create_config_good() -> Config:
    return {"port": 8080, "host": "localhost"}

def get_port_good(config: Config) -> int:
    return config["port"]  # checked keys, value is int
```

### 6. `Any` defeats structural typing

```python
from typing import Any, Protocol

class HasLength(Protocol):
    def __len__(self) -> int: ...

# BAD: Any prevents protocol matching
def get_size_untyped(obj: Any) -> int:
    return len(obj)  # no checking

# GOOD: Protocol enables structural typing
def get_size(obj: HasLength) -> int:
    return len(obj)  # any object with __len__ works — and nothing else
```

## Antipatterns where precise types replace `Any`

### 1. With type guards — a bool "guard" on `Any` narrows nothing

```python
from typing import Any, TypeIs

def get_value() -> Any: ...

# BAD: a plain-bool guard on Any doesn't narrow
def is_string(value: Any) -> bool:
    return isinstance(value, str)

x: Any = get_value()
if is_string(x):
    x.unknown_method()  # no error — x is still Any

# GOOD: TypeIs narrows a checked union
def is_str(value: str | int) -> TypeIs[str]:
    return isinstance(value, str)

def describe(value: str | int) -> str:
    if is_str(value):
        return value.upper()   # value is str here
    return str(value * 2)      # value is int here
```

### 2. With generics — TypeVar preserves what `Any` erases

```python
from typing import Any

# BAD: Any in generic function
def first_item_unsafe(items: list[Any]) -> Any:
    return items[0]

result_unsafe = first_item_unsafe([1, 2, 3])
result_unsafe.upper()  # no error — crashes at runtime (int has no .upper)

# GOOD: a type parameter preserves the element type
def first_item[T](items: list[T]) -> T:
    return items[0]

result = first_item([1, 2, 3])  # inferred as int
result.upper()  # error: cannot access attribute "upper" for class "int"
```

### 3. With Callable — `Any` vs callable signatures

```python
from collections.abc import Callable
from typing import Any

# BAD: Any for callback parameters
def apply_callback_any(data: Any, callback: Any) -> Any:
    return callback(data)

untyped = apply_callback_any("hello", str.upper)
untyped + 1  # no error — crashes at runtime (str + int)

# GOOD: Callable signature provides checking
def apply_callback(data: str, callback: Callable[[str], int]) -> int:
    return callback(data)

apply_callback("hello", str.__len__)  # OK — (str) -> int matches
apply_callback("hello", str.upper)    # error: return type "str" is incompatible with "int"
```

### 4. With Optional/Union — `Any` vs explicit nullability

```python
from typing import Any

# BAD: Any hides None handling
def get_name_any(user: Any) -> Any:
    return user.get("name")  # could be None — callers won't be warned

# GOOD: an explicit | None forces callers to handle the absence
def get_name(user: dict[str, str]) -> str | None:
    return user.get("name")
```

### 5. With Literal — `Any` vs exact values

```python
from typing import Any, Literal

# BAD: Any for enum-like values
def set_mode(mode: Any) -> None:
    if mode == "read":
        ...

set_mode(123)  # no error

# GOOD: Literal enforces exact values
def set_mode_good(mode: Literal["read", "write"]) -> None:
    if mode == "read":
        ...

set_mode_good(123)  # error: "Literal[123]" is not assignable to "Literal['read', 'write']"
```

## Source anchors

- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
- [PEP 526 — Syntax for Variable Annotations](https://peps.python.org/pep-0526/)
- [typing module — Any](https://docs.python.org/3/library/typing.html#typing.Any)
- [mypy docs — Running mypy](https://mypy.readthedocs.io/en/stable/running_mypy.html)
- [mypy docs — The Any type](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#the-any-type)
- [pyright docs — Configuration](https://microsoft.github.io/pyright/#/configuration)
- [typing spec — Gradual typing](https://typing.readthedocs.io/en/latest/spec/concepts.html#gradual-types)
