# Path-Dependent Types (Not Available)

> **Since:** N/A -- Python's type system does not support path-dependent types

## What it is

Path-dependent types allow a type to be tied to a specific instance: in Scala, `x.Inner` and `y.Inner` are distinct types even when `x` and `y` have the same class. Python has **no equivalent mechanism**. Python's type system does not track which object instance a type originates from, and there is no syntax or concept for a type that varies with the runtime identity of a value.

This file documents the gap and the idioms that Python developers use to approximate some of the same patterns — primarily `TypeVar`, `Generic`, and `Protocol`.

## What constraint it enforces

**Python enforces no path-dependent constraint.** There is no way to declare that a type member belongs to a specific object instance or that two type expressions are incompatible because they originate from different instances of the same class.

Where Scala uses path-dependent types to ensure "nodes from graph A cannot be mixed with nodes from graph B," Python relies on runtime checks, conventions, or generic type parameters that provide weaker (class-level, not instance-level) separation.

## Minimal snippet

```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Container(Generic[T]):
    """Generic provides class-level parameterization, not instance-level."""
    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value

# Both are Container[int] -- the type system sees them as the same type.
a = Container(1)
b = Container(2)

# No way to distinguish a.T from b.T -- they are both int.
# In Scala, these could have distinct path-dependent type members.
```

## Interaction with other features

| Feature | How it relates |
|---------|---------------|
| **Generics and bounds** [-> catalog/T04](T04-generics-bounds.md) | `Generic[T]` parameterizes at the class level, not the instance level. All instances of `Container[int]` share the same type parameter. This is the closest Python gets to abstract type members. |
| **Structural typing** [-> catalog/T07](T07-structural-typing.md) | `Protocol` defines structural interfaces, but protocol members cannot depend on instance identity. A `Protocol` with a type variable constrains the class, not individual objects. |
| **Type aliases** [-> catalog/T23](T23-type-aliases.md) | `TypeAlias` and `type` statements create aliases but not instance-scoped type members. An alias is global, not bound to an object path. |

## Gotchas and limitations

1. **No instance-level type distinction.** Two instances of `Container[int]` are indistinguishable to the type checker. You cannot express "this particular container's element type" as distinct from another container of the same class and type parameter.

2. **`TypeVar` is class-level, not value-level.** A `TypeVar` bound to a class via `Generic` is resolved when the class is parameterized, not when an instance is created. All instances of `MyClass[int]` share the same resolved `TypeVar`.

3. **No abstract type members.** Python classes cannot declare `type Inner` as an abstract member to be filled in by subclasses in a type-checked way. You can use class variables with `ClassVar` and `type` annotations, but the type checker does not enforce the same constraints.

4. **Workaround: newtype per instance.** You can create distinct `NewType` wrappers to separate types, but this is manual and does not scale — you need a new type for each "path."

5. **Runtime tagging as escape hatch.** Libraries like `attrs` or `pydantic` use runtime validation and metadata to associate types with specific instances, but this is invisible to static type checkers like mypy or pyright.

## Beginner mental model

In languages with path-dependent types, each object carries its own personal type that no other object shares — like a unique ID badge that the compiler checks. In Python, objects carry values but not unique types. Two containers holding `int` values look identical to the type checker, no matter how different they are at runtime. If you need the compiler to keep them separate, you have to create entirely different classes or use distinct type parameters manually.

## Example A — Generic class as the closest approximation

```python
from typing import TypeVar, Generic

K = TypeVar("K")
V = TypeVar("V")

class TypedStore(Generic[K, V]):
    def __init__(self) -> None:
        self._data: dict[K, V] = {}

    def put(self, key: K, value: V) -> None:
        self._data[key] = value

    def get(self, key: K) -> V | None:
        return self._data.get(key)

# The store is parameterized at the class level, not per-key.
store: TypedStore[str, int] = TypedStore()
store.put("age", 30)        # OK
# store.put("age", "thirty")  # mypy error: expected int

# But there is no way to have DIFFERENT value types for different keys
# in the same store — that requires path-dependent types.
```

## Example B — Protocol for structural constraints (no path dependence)

```python
from typing import Protocol, TypeVar

T_co = TypeVar("T_co", covariant=True)

class HasFirst(Protocol[T_co]):
    def first(self) -> T_co: ...

class Names:
    def __init__(self, items: list[str]) -> None:
        self._items = items
    def first(self) -> str:
        return self._items[0]

class Scores:
    def __init__(self, items: list[int]) -> None:
        self._items = items
    def first(self) -> int:
        return self._items[0]

def peek(c: HasFirst[T_co]) -> T_co:
    return c.first()

# The return type varies with the CLASS, not the instance.
name: str = peek(Names(["Alice"]))
score: int = peek(Scores([100]))
```

## Example C — Manual separation with NewType

```python
from typing import NewType

# Manually creating distinct types for different "paths"
GraphANode = NewType("GraphANode", int)
GraphBNode = NewType("GraphBNode", int)

def connect_a(src: GraphANode, dst: GraphANode) -> None: ...
def connect_b(src: GraphBNode, dst: GraphBNode) -> None: ...

a_node = GraphANode(1)
b_node = GraphBNode(2)

connect_a(a_node, a_node)  # OK
# connect_a(a_node, b_node)  # mypy error: expected GraphANode, got GraphBNode
# This works, but you need a new NewType for every "graph instance."
```

## Use-case cross-references

- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Generic constraints provide class-level type separation, the closest Python gets to path-dependent patterns.

## Source anchors

- [Python typing docs -- Generics](https://docs.python.org/3/library/typing.html#generics)
- [Python typing docs -- NewType](https://docs.python.org/3/library/typing.html#newtype)
- [Python typing docs -- Protocol](https://docs.python.org/3/library/typing.html#protocols)
- [mypy docs -- Generics](https://mypy.readthedocs.io/en/stable/generics.html)
- [PEP 544 -- Protocols: Structural subtyping](https://peps.python.org/pep-0544/)
