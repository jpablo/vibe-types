# Typestate (via Literal Types and Overload)

> **Since:** `Literal` Python 3.8 (PEP 586); `@overload` Python 3.5 (PEP 484); `Generic` Python 3.5 (PEP 484)

## What it is

Python does not have native typestate support, but the **type checker** can enforce state-dependent method availability using a combination of `Generic[State]` with `Literal` type parameters and `@overload` decorators. The pattern uses a generic class parameterized by a state type (e.g., `Literal["open"]`, `Literal["closed"]`), and `@overload` signatures restrict which methods are available in each state.

The checker (mypy, pyright) enforces that methods declared for `Connection[Literal["open"]]` cannot be called on a `Connection[Literal["closed"]]`. State transitions return a new object with the updated type parameter. At runtime, the state parameter has no cost — `Generic` subscripts are erased, and `Literal` types exist only during static analysis.

This pattern is less ergonomic than Rust's or Scala's typestate because Python's type system requires explicit `@overload` declarations and `TYPE_CHECKING` guards, but it provides the same compile-time safety when used with a strict type checker.

## What constraint it enforces

**Methods annotated with `@overload` for a specific `Literal` state are only callable when the type checker can prove the object is in that state. State transitions change the `Literal` type parameter, and the checker rejects calls that do not match the current state.**

## Minimal snippet

```python
from typing import Generic, Literal, TypeVar, overload

S = TypeVar("S")

class Door(Generic[S]):
    def __init__(self, state: S) -> None:
        self._state = state

    @staticmethod
    def create() -> "Door[Literal['closed']]":
        return Door("closed")

def open_door(door: Door[Literal["closed"]]) -> Door[Literal["open"]]:
    return Door("open")

def enter(door: Door[Literal["open"]]) -> None:
    print("Entering!")

d = Door.create()
# enter(d)           # error: expected Door[Literal["open"]], got Door[Literal["closed"]]
d2 = open_door(d)
enter(d2)            # OK
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Literal types** [-> T52](T52-literal-types.md) | `Literal["open"]`, `Literal["closed"]` serve as state tags. The checker distinguishes them at analysis time; at runtime they are plain strings. |
| **Generics / TypeVar** [-> T04](T04-generics-bounds.md) | `Generic[S]` parameterizes the class by state. The state is a type parameter that the checker tracks through assignments and returns. |
| **@overload** [-> T22](T22-callable-typing.md) | `@overload` provides different type signatures for different state parameters, restricting which methods are available per state. |
| **Phantom types** [-> T27](T27-erased-phantom.md) | Typestate is a specific application of phantom types where the phantom parameter encodes a finite state machine. |
| **Type narrowing** [-> T14](T14-type-narrowing.md) | After a state transition (function returning the new type), the checker narrows the variable's type to the new state. |
| **TYPE_CHECKING guard** | State tag classes can be defined under `if TYPE_CHECKING:` to avoid any runtime cost for the state type definitions themselves. |

## Gotchas and limitations

1. **No ownership / linear types.** After a state transition, the old variable still exists with the old type. Nothing prevents using the stale reference. Developers must discipline themselves to rebind: `d = open_door(d)`.

2. **@overload is verbose.** Each state-specific method requires a separate `@overload` signature plus the implementation. For many states and methods, this leads to significant boilerplate.

3. **Runtime state is not linked to type state.** The `Literal` type parameter is erased at runtime. If runtime code inspects `self._state`, it may disagree with the checker's view. Keep the runtime state synchronized manually.

4. **Limited checker support.** Not all type checkers handle `Literal`-parameterized `Generic` classes equally well. pyright has the best support; mypy may require `# type: ignore` in some edge cases.

5. **No exhaustive state checking.** Unlike Rust's `match` or Scala's sealed traits, Python's type checkers do not enforce exhaustive handling of all states. You must manually ensure all state transitions are covered.

6. **Cannot express "any state" easily.** A function that works on a `Door` in any state requires `Door[Any]` or a plain `Door` (unparameterized), which loses the state tracking. There is no built-in "existential state" type.

## Beginner mental model

Think of the `Literal` state parameter as a **color-coded label** on the object. A `Door[Literal["closed"]]` has a red label; `Door[Literal["open"]]` has a green label. The `enter` function has a sign saying "green labels only." The `open_door` function takes a red-labeled door and hands back a green-labeled one. The type checker is the security guard checking labels. At runtime, the labels are invisible — they exist only in the checker's analysis.

## Example A -- HTTP connection with state tracking

```python
from __future__ import annotations
from typing import Generic, Literal, TypeVar

S = TypeVar("S")

class HttpConn(Generic[S]):
    def __init__(self, host: str) -> None:
        self._host = host

    @staticmethod
    def create(host: str) -> HttpConn[Literal["idle"]]:
        return HttpConn(host)

def connect(c: HttpConn[Literal["idle"]]) -> HttpConn[Literal["connected"]]:
    return HttpConn(c._host)

def authenticate(c: HttpConn[Literal["connected"]], token: str) -> HttpConn[Literal["auth"]]:
    return HttpConn(c._host)

def fetch(c: HttpConn[Literal["auth"]], path: str) -> str:
    return f"Response from {c._host}{path}"

# Valid:
c = HttpConn.create("api.example.com")
c2 = connect(c); c3 = authenticate(c2, "tok"); data = fetch(c3, "/users")
# fetch(HttpConn.create("x"), "/")  # error: expected auth, got idle
```

## Example B -- File handle with read/write modes

```python
from __future__ import annotations
from typing import Generic, Literal, TypeVar

M = TypeVar("M")

class TypedFile(Generic[M]):
    def __init__(self, path: str) -> None: self._path = path

    @staticmethod
    def open_read(path: str) -> TypedFile[Literal["r"]]: return TypedFile(path)
    @staticmethod
    def open_write(path: str) -> TypedFile[Literal["w"]]: return TypedFile(path)

def read_line(f: TypedFile[Literal["r"]]) -> str: return "line"
def write_line(f: TypedFile[Literal["w"]], line: str) -> None: ...

rf = TypedFile.open_read("data.txt")
read_line(rf)         # OK
# write_line(rf, "x") # error: expected Literal["w"], got Literal["r"]
wf = TypedFile.open_write("out.txt")
write_line(wf, "hello")  # OK
# read_line(wf)           # error: expected Literal["r"], got Literal["w"]
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Typestate makes invalid state transitions a type-checker error, preventing operations in the wrong state.
- [-> UC-08](../usecases/UC08-error-handling.md) -- Protocol violations are caught during static analysis instead of producing runtime exceptions.

## Source anchors

- [PEP 586 -- Literal Types](https://peps.python.org/pep-0586/)
- [PEP 484 -- Type Hints (@overload, Generic)](https://peps.python.org/pep-0484/)
- [mypy -- Literal types](https://mypy.readthedocs.io/en/stable/literal_types.html)
- [pyright -- Literal type narrowing](https://microsoft.github.io/pyright/#/type-concepts-advanced?id=literal-types)
