# Callable Types and @overload

> **Since:** `Callable` Python 3.5 (PEP 484); `@overload` Python 3.5 (PEP 484); Protocol `__call__` Python 3.8 (PEP 544) | **Backport:** `typing_extensions`

## What it is

`Callable[[Arg1, Arg2], Return]` is the standard way to annotate function-typed values in Python: callback parameters, function factories, and higher-order functions. `@overload` lets you declare multiple type-level signatures for a single function so that the checker can select a more precise return type based on the arguments at each call site. When `Callable` is too restrictive (no keyword arguments, no optional parameters), you define a `Protocol` with a `__call__` method to describe the exact signature.

## What constraint it enforces

**The type checker verifies that every function passed where a `Callable` (or callable Protocol) is expected matches the declared parameter and return types, and that every `@overload`-decorated function is called with arguments matching at least one declared overload.**

## Minimal snippet

```python
from collections.abc import Callable

def apply(fn: Callable[[int, int], str], a: int, b: int) -> str:
    return fn(a, b)

def good(x: int, y: int) -> str:
    return f"{x + y}"

def bad(x: int, y: int) -> int:
    return x + y

apply(good, 1, 2)  # OK
apply(bad, 1, 2)    # error — return type int is incompatible with str
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Generics / TypeVar** [-> catalog/07](T04-generics-bounds.md) | A `Callable` can use `TypeVar` to express generic callbacks: `Callable[[T], T]` preserves the input type through the return. |
| **ParamSpec** [-> catalog/08](T45-paramspec-variadic.md) | `ParamSpec` captures an entire parameter list, letting decorators preserve the wrapped function's full signature — something `Callable` alone cannot do. |
| **Protocol** [-> catalog/09](T07-structural-typing.md) | A Protocol with `__call__` replaces `Callable` when the callback needs keyword arguments, optional parameters, or overloaded signatures. |

## Gotchas and limitations

1. **`Callable` cannot express keyword arguments.** `Callable[[int, str], bool]` describes positional-only parameters. For keyword arguments use a Protocol with `__call__`.

2. **`Callable` cannot express optional or default parameters.** There is no syntax for `Callable[[int, str = ...], bool]`. Use a Protocol instead.

3. **`@overload` order matters.** The checker evaluates overloads top-to-bottom and picks the first match. Put more specific signatures before more general ones.

4. **The implementation body is not checked against overloads by mypy.** Mypy checks callers against the overload signatures but does not verify that the implementation body actually satisfies all overloads. Pyright does check the implementation body.

5. **`@overload` functions must have at least two overload signatures.** A single `@overload` decorator is meaningless and will be flagged.

6. **Contravariance of argument types.** `Callable` is contravariant in its parameter types and covariant in its return type. A `Callable[[object], int]` can substitute for `Callable[[str], int]`, not the other way around.

## Beginner mental model

Think of `Callable[[A, B], R]` as a **shape stamp for functions**: any function that takes an `A` and a `B` and returns an `R` fits the stamp. `@overload` is like writing **multiple stamps** for the same function name so the checker can pick the most precise one at each call site. When neither is flexible enough, a Protocol with `__call__` lets you draw the stamp in full detail.

## Example A — Callback parameter with typed signature

```python
from collections.abc import Callable

type Comparator[T] = Callable[[T, T], bool]

def find_max(items: list[int], is_greater: Comparator[int]) -> int | None:
    if not items:
        return None
    best = items[0]
    for item in items[1:]:
        if is_greater(item, best):
            best = item
    return best

def ascending(a: int, b: int) -> bool:
    return a > b

def wrong_sig(a: int, b: str) -> bool:  # note: second param is str
    return True

find_max([3, 1, 4], ascending)    # OK
find_max([3, 1, 4], wrong_sig)    # error — Callable[[int, str], bool]
                                   #   is incompatible with Callable[[int, int], bool]
```

Using a Protocol when keyword arguments are required:

```python
from typing import Protocol

class Formatter(Protocol):
    def __call__(self, value: float, *, precision: int = 2) -> str: ...

def render(fmt: Formatter, v: float) -> str:
    return fmt(v, precision=4)

def my_fmt(value: float, *, precision: int = 2) -> str:
    return f"{value:.{precision}f}"

render(my_fmt, 3.14159)  # OK
```

## Example B — @overload for a parse function returning different types based on input

```python
from typing import overload

@overload
def parse(raw: str, as_int: bool = ...) -> str: ...
@overload
def parse(raw: bytes, as_int: bool = ...) -> int: ...

def parse(raw: str | bytes, as_int: bool = False) -> str | int:
    if isinstance(raw, bytes):
        return int.from_bytes(raw, "big")
    return raw.strip()

x: str = parse("hello")      # OK — first overload selected
y: int = parse(b"\x00\x01")  # OK — second overload selected
z: str = parse(b"\x00\x01")  # error — overload returns int for bytes input
```

A more realistic overload — `json.loads`-style dispatch:

```python
from typing import Any, overload, Literal

@overload
def fetch(url: str, *, json: Literal[True]) -> dict[str, Any]: ...
@overload
def fetch(url: str, *, json: Literal[False] = ...) -> str: ...

def fetch(url: str, *, json: bool = False) -> dict[str, Any] | str:
    import urllib.request, json as _json
    resp = urllib.request.urlopen(url).read().decode()
    if json:
        return _json.loads(resp)
    return resp

data: dict[str, Any] = fetch("https://api.example.com", json=True)   # OK
text: str = fetch("https://example.com")                              # OK
bad: dict[str, Any] = fetch("https://example.com")                    # error
```

## Common type-checker errors and how to read them

### `Argument of type "..." is not assignable to parameter of type "Callable[...]"`

**Pyright** reports this when a function's signature does not match the expected `Callable` type. Check parameter types (contravariant) and return type (covariant).

### `Overloaded function signature N is not compatible with implementation`

**Pyright** checks that the implementation signature is a supertype of each overload. The implementation must accept the union of all overloaded parameter types and return a type compatible with all overloaded return types.

### `Overload signatures overlap with incompatible return types`

Both checkers flag this when two `@overload` signatures match the same arguments but promise different return types. Reorder or refine the overload signatures to eliminate ambiguity.

### `No overload variant matches argument types`

**mypy** reports this when a call does not match any declared overload. Verify the argument types and check overload ordering.

### `"Callable[..., T]" has no attribute "keyword_arg"` (conceptual)

You cannot call a `Callable` with keyword arguments — the type does not encode parameter names. Switch to a Protocol with `__call__` to support keyword arguments.

## Use-case cross-references

- [-> UC-07](../usecases/UC07-callable-contracts.md) — Callback-driven architectures where functions are passed as configuration.
- [-> UC-09](../usecases/UC09-builder-config.md) — Plugin systems that accept callable hooks with typed signatures.

## When to Use

Use `Callable`, `@overload`, and callable Protocols when you need to:

- **Enforce callback contracts**: Ensure functions passed as arguments have the correct signature.

  ```python
  from collections.abc import Callable

  def process(data: str, transformer: Callable[[str], int]) -> int:
      return transformer(data)

  process("123", int)  # OK
  process("abc", float)  # error — returns float, not int
  ```

- **Narrow return types by literal arguments**: Overloads make invalid combinations errors.

  ```python
  from typing import overload

  @overload
  def get_item(key: Literal["name"]) -> str: ...
  @overload
  def get_item(key: Literal["age"]) -> int: ...

  def get_item(key: str) -> str | int: ...

  name: str = get_item("name")  # OK
  age: int = get_item("age")    # OK
  ```

- **Express keyword arguments in callbacks**: Protocols with `__call__` support named parameters.

  ```python
  from typing import Protocol

  class Formatter(Protocol):
      def __call__(self, value: float, *, precision: int = 2) -> str: ...

  def format_number(fmt: Formatter, v: float) -> str:
      return fmt(v, precision=4)  # keyword arg works
  ```

- **Preserve input-output type relationships**: Generic callables maintain the connection.

  ```python
  from typing import TypeVar

  T = TypeVar("T")

  def identity(fn: Callable[[T], T], x: T) -> T:
      return fn(x)

  result = identity(str.lower, "HELLO")  # result: str
  ```

## When Not to Use

Avoid `Callable`, `@overload`, and callable Protocols when:

- **The function has a single straightforward signature**: Overengineering with overloads adds complexity.

  ```python
  # Unnecessary overload
  @overload
  def add(a: int, b: int) -> int: ...
  def add(a: int, b: int) -> int:
      return a + b

  # Prefer: just the implementation
  def add(a: int, b: int) -> int:
      return a + b
  ```

- **Arguments are truly interchangeable**: Use optional parameters or union types instead.

  ```python
  # Overkill
  @overload
  def connect(host: str, port: int) -> Connection: ...
  @overload
  def connect(config: dict) -> Connection: ...

  # Simpler with union
  def connect(host: str | None = None, port: int = 80) -> Connection: ...
  ```

- **You're modeling unrelated operations**: Separate functions are clearer than overloads.

  ```python
  # Confusing
  @overload
  def parse(s: str) -> int: ...
  @overload
  def parse(n: int) -> str: ...

  # Clearer: distinct functions
  def parse_string(s: str) -> int: ...
  def to_string(n: int) -> str: ...
  ```

- **The callback is truly flexible**: `Callable[..., Any]` or no annotation is sometimes appropriate.

  ```python
  # Overly restrictive for generic iterators
  def map_items(items: list[t], fn: Callable[[T], U]) -> list[U]: ...

  # OK for truly arbitrary callbacks
  def run_callbacks(*fns: Callable[..., Any]) -> None: ...
  ```

## Antipatterns When Using Callable Typing

### Overload ordering mistake

Broad overload before narrow one makes the narrow unreachable.

```python
# ❌ Wrong: narrow overload unreachable
@overload
def handle(x: str | int) -> str: ...
@overload
def handle(x: int) -> int: ...
def handle(x): ...

# ✅ Correct: narrow first
@overload
def handle(x: int) -> int: ...
@overload
def handle(x: str) -> str: ...
def handle(x: str | int) -> str | int: ...
```

### Using `Callable` for optional parameters

`Callable` cannot express optional or default parameters.

```python
# ❌ Wrong: Callable is too permissive
def run(fn: Callable[[int], str]) -> str:
    return fn(0)

# This passes but crashes at runtime
def bad(x: int, required: str) -> str: ...
run(bad)  # type-checks, but fails: missing required arg
```

### Ignoring contravariance

`Callable` is contravariant in parameters — a broader parameter type is substitutable.

```python
# ❌ Wrong: expects str but function takes narrower int
def with_callback(fn: Callable[[int], None]) -> None:
    fn(1)

with_callback(lambda s: print(s))  # OK: str accepts int (no, actually not!)
# Correction:
with_callback(lambda i: print(i))  # OK: int parameter
```

### Using `Callable[[...], Any]` everywhere

Loses all type information for callbacks.

```python
# ❌ Wrong
def process(data: list, fn: Callable[..., Any]) -> list:
    return [fn(x) for x in data]

# ✅ With proper generic callable
T = TypeVar("T")
U = TypeVar("U")

def map_fn(data: list[T], fn: Callable[[T], U]) -> list[U]:
    return [fn(x) for x in data]
```

### Overlapping overload signatures with incompatible returns

Two overloads can't match the same arguments with different return types.

```python
# ❌ Wrong: overlapping with incompatible returns
@overload
def get(x: str | int) -> str: ...
@overload
def get(x: int) -> int: ...

# ✅ Correct: non-overlapping
@overload
def get(x: int) -> int: ...
@overload
def get(x: str) -> str: ...
```

## Antipatterns with Other Techniques (Solved by Callable Typing)

### Using union types instead of callable types

Union types lose the function contract entirely.

```python
# ❌ Wrong: loses function type information
Callbacks = list[str | int | bytes]

# ✅ With proper callable type
Callbacks = list[Callable[[], None]]
```

### Using `Protocol` for simple callbacks when `Callable` suffices

Overhead of defining a Protocol for trivial cases.

```python
# ❌ Overkill for simple callbacks
class SimpleCallback(Protocol):
    def __call__(self, x: int) -> str: ...

def run(cb: SimpleCallback) -> str: ...

# ✅ Callable is sufficient
def run(cb: Callable[[int], str]) -> str: ...
```

### Using duck typing without annotations for callbacks

No compile-time checking of callback signatures.

```python
# ❌ No type checking
def process(items, callback):
    for item in items:
        callback(item)

# ✅ With typed callback
def process(items: list[int], callback: Callable[[int], None]) -> None:
    for item in items:
        callback(item)
```

### Using `Optional[Callable[...]]` without runtime check

Passing `None` to a callable parameter causes runtime errors.

```python
# ❌ Wrong: None is allowed but not handled
def transform(fn: Callable[[int], str] | None, x: int) -> str:
    return fn(x)  # crashes if fn is None

# ✅ With proper handling
def transform(fn: Callable[[int], str] | None, x: int) -> str:
    if fn is None:
        return str(x)
    return fn(x)
```

### Not using `@overload` when return type depends on input

Union return types lose precision.

```python
# ❌ Wrong: return type is always union
def get_value(key: str) -> str | int | float:
    if key == "name": return "alice"
    elif key == "age": return 30
    return 3.14

# ✅ With overloads
@overload
def get_value(key: Literal["name"]) -> str: ...
@overload
def get_value(key: Literal["age"]) -> int: ...
@overload
def get_value(key: Literal["pi"]) -> float: ...
def get_value(key: str) -> str | int | float: ...
```

## Source anchors

- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/) — `Callable` and `@overload`
- [PEP 544 — Protocols: Structural subtyping](https://peps.python.org/pep-0544/) — Protocol `__call__`
- [PEP 612 — Parameter Specification Variables](https://peps.python.org/pep-0612/) — `ParamSpec` for advanced callable typing
- [typing spec — Callable](https://typing.readthedocs.io/en/latest/spec/callables.html)
- [mypy docs — Overloading](https://mypy.readthedocs.io/en/stable/more_types.html#function-overloading)
