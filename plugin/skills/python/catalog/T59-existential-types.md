# Existential Types (via Protocol and Type Erasure)

> **Since:** `Protocol` Python 3.8 (PEP 544); `TypeVar` Python 3.5 (PEP 484); structural subtyping via Protocol

## What it is

Python does not have true existential quantification in its type system. However, **`Protocol` classes** achieve a similar effect: they define an interface without knowing the concrete type that implements it. A function accepting `Summarizable` (a Protocol with a `summary()` method) works with any object that has that method -- the concrete type is existentially hidden behind the protocol.

This is structural subtyping (duck typing with type-checker support). The caller provides a value of some unknown concrete type; the receiver sees only the protocol interface. Combined with `TypeVar` bounds and `isinstance` runtime checks, Protocol-based existentials let you write code that operates on "something with property P" without naming the concrete type.

## What constraint it enforces

**A Protocol defines the minimal interface a value must satisfy. The type checker ensures the caller provides a structurally-compatible type, while the receiver can only use methods declared in the Protocol -- not methods specific to the concrete type.**

- Protocol members are the only operations available to the receiver.
- No registration or explicit subclassing is needed -- structural compatibility suffices.
- Runtime `isinstance` checks are available via `runtime_checkable` protocols.

## Minimal snippet

```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> str: ...

class Circle:
    def __init__(self, r: float) -> None:
        self.r = r
    def draw(self) -> str:
        return f"Circle(r={self.r})"

class Square:
    def __init__(self, side: float) -> None:
        self.side = side
    def draw(self) -> str:
        return f"Square(side={self.side})"

def render(shape: Drawable) -> None:
    print(shape.draw())   # OK — Drawable protocol guarantees draw()
    # print(shape.r)      # error: Drawable has no attribute "r"

render(Circle(5.0))    # OK — Circle is structurally Drawable
render(Square(3.0))    # OK — Square is structurally Drawable
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Structural typing** [-> catalog/T07](T07-structural-typing.md) | Protocol IS structural typing. It defines the shape a type must have, achieving existential hiding through structural compatibility rather than nominal subtyping. |
| **Generics / TypeVar** [-> catalog/T04](T04-generics-bounds.md) | `TypeVar` bound to a Protocol creates a universally-quantified variable constrained to the protocol. Without the bound, an unbound TypeVar with Protocol parameters approximates existential quantification. |
| **Union types** [-> catalog/T02](T02-union-intersection.md) | `Circle | Square` is a closed union (the caller knows the options). `Drawable` is an open existential (any structurally-compatible type works). |
| **Type narrowing** [-> catalog/T14](T14-type-narrowing.md) | `isinstance` with `runtime_checkable` protocols narrows a value to the protocol type, recovering the existential interface from an `object` or `Any`. |
| **Callable typing** [-> catalog/T22](T22-callable-typing.md) | `Protocol` with `__call__` defines existential callable types -- "something callable with signature X" without naming the concrete callable. |

## Gotchas and limitations

1. **No true existential quantification.** Python's type system cannot express "there exists a type T such that ...". Protocol is structural subtyping, not existential packing. You cannot return "a Drawable whose concrete type is hidden" in the same way Scala's abstract type members or Rust's `dyn Trait` can.

2. **runtime_checkable is shallow.** `@runtime_checkable` only checks method existence, not signatures. `isinstance(obj, Drawable)` returns `True` if `obj` has a `draw` attribute, even if its signature is wrong.

   ```python
   from typing import runtime_checkable, Protocol

   @runtime_checkable
   class Drawable(Protocol):
       def draw(self) -> str: ...

   class Fake:
       draw = 42   # not callable!

   isinstance(Fake(), Drawable)   # True — only checks attribute exists
   ```

3. **Protocol members must be defined in the Protocol.** You cannot use methods not declared in the Protocol, even if the concrete type has them. This is the existential hiding in action, but it can feel restrictive.

4. **No variance inference on Protocols.** The type checker does not automatically infer whether a Protocol is covariant or contravariant. You must use `TypeVar` with explicit `covariant=True` or `contravariant=True` if variance matters.

5. **Generic Protocols require careful TypeVar scoping.** A `Protocol[T]` with a TypeVar creates a family of protocols. Confusing the TypeVar scope between the Protocol definition and usage leads to subtle type errors.

## Beginner mental model

Think of a Protocol as a **job description** rather than a specific person. The job description says "must be able to draw." Anyone who can draw qualifies -- you do not need to know their name, background, or other skills. When you accept a `Drawable`, you get "someone who can draw" but you cannot ask them to do anything not in the job description. This is existential hiding: you know *something* about the value (it can draw) but not *everything* (its concrete type).

## Example A -- Heterogeneous collection via Protocol

```python
from typing import Protocol

class HasLength(Protocol):
    def __len__(self) -> int: ...

def total_length(items: list[HasLength]) -> int:
    return sum(len(item) for item in items)

result = total_length(["hello", [1, 2, 3], b"bytes"])
print(result)  # 13 — str, list, and bytes all have __len__
```

## Example B -- Protocol with generic existential parameter

```python
from typing import Protocol, TypeVar, Iterator

T_co = TypeVar("T_co", covariant=True)

class DataSource(Protocol[T_co]):
    def fetch(self) -> Iterator[T_co]: ...
    def name(self) -> str: ...

class CsvSource:
    def __init__(self, path: str) -> None:
        self.path = path
    def fetch(self) -> Iterator[list[str]]:
        yield ["Alice", "30"]
        yield ["Bob", "25"]
    def name(self) -> str:
        return f"CSV({self.path})"

def describe(source: DataSource[object]) -> str:
    """Accepts any DataSource — the element type is existentially hidden."""
    return f"Source '{source.name()}' ready"

print(describe(CsvSource("data.csv")))  # OK — CsvSource satisfies DataSource
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Protocol-based existentials restrict operations to declared interfaces, preventing misuse of hidden concrete types.
- [-> UC-02](../usecases/UC02-domain-modeling.md) -- Domain boundaries use Protocols to accept any type satisfying domain constraints without coupling to concrete implementations.

## Source anchors

- [PEP 544 -- Protocols: Structural subtyping](https://peps.python.org/pep-0544/)
- [typing -- Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [mypy -- Protocols and structural subtyping](https://mypy.readthedocs.io/en/stable/protocols.html)
- [pyright -- Protocols](https://microsoft.github.io/pyright/#/protocols)
