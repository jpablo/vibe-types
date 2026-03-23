# Protocol and State Machines

## The constraint

State transitions must be encoded in the type system so that calling a
method invalid for the current state is a type error — not a runtime
exception. The checker should verify that operations are only available
in the states where they are valid.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| `Literal` + `@overload` | Return different types based on state-valued arguments | [-> T52](../catalog/T52-literal-types.md), [-> T22](../catalog/T22-callable-typing.md) |
| Generic state parameter | Encode state as a type parameter; transitions change the parameter | [-> T04](../catalog/T04-generics-bounds.md) |
| Union + narrowing | Model states as union variants; narrow to access state-specific data | [-> T02](../catalog/T02-union-intersection.md), [-> T14](../catalog/T14-type-narrowing.md) |
| `Protocol` | Define available operations per state as structural interfaces | [-> T07](../catalog/T07-structural-typing.md) |

## Patterns

### A — `Literal` + `@overload` for state-dependent returns

Use `Literal` values to represent states and `@overload` to give the checker
distinct return types based on the state argument.

```python
from typing import Literal, overload

@overload
def connect(state: Literal["disconnected"]) -> "Connected": ...
@overload
def connect(state: Literal["connected"]) -> "Error": ...

def connect(state: str) -> "Connected | Error":
    if state == "disconnected":
        return Connected()
    return Error("already connected")

from dataclasses import dataclass

@dataclass
class Connected:
    def send(self, data: bytes) -> int:
        return len(data)

@dataclass
class Error:
    message: str

result = connect("disconnected")
result.send(b"hello")          # OK — checker knows result is Connected

result2 = connect("connected")
result2.send(b"hello")         # error: "Error" has no attribute "send"
```

### B — Generic state parameter for type-safe transitions

Encode the state in a type parameter. Transition methods return a new object
with a different state type, so the checker tracks the current state.

```python
from typing import Generic, TypeVar, Literal

class Open: ...
class Closed: ...
class HalfOpen: ...

type GateState = type[Open] | type[Closed] | type[HalfOpen]

S = TypeVar("S")

class Gate(Generic[S]):
    def __init__(self, state: type[S]) -> None:
        self._state = state

    @staticmethod
    def create() -> "Gate[Closed]":
        return Gate(Closed)

def open_gate(g: Gate[Closed]) -> Gate[Open]:
    return Gate(Open)

def half_close(g: Gate[Open]) -> Gate[HalfOpen]:
    return Gate(HalfOpen)

def close_gate(g: Gate[HalfOpen]) -> Gate[Closed]:
    return Gate(Closed)

gate = Gate.create()             # Gate[Closed]
opened = open_gate(gate)         # Gate[Open]
half = half_close(opened)        # Gate[HalfOpen]
closed = close_gate(half)        # Gate[Closed]

open_gate(opened)                # error: expected Gate[Closed], got Gate[Open]
close_gate(gate)                 # error: expected Gate[HalfOpen], got Gate[Closed]
```

### C — Union variants for states with data

Model each state as a distinct dataclass. The checker enforces narrowing
before accessing state-specific attributes.

```python
from dataclasses import dataclass
from typing import assert_never

@dataclass
class Draft:
    content: str

@dataclass
class UnderReview:
    content: str
    reviewer: str

@dataclass
class Published:
    content: str
    url: str

type ArticleState = Draft | UnderReview | Published

def submit(article: Draft, reviewer: str) -> UnderReview:
    return UnderReview(content=article.content, reviewer=reviewer)

def publish(article: UnderReview, url: str) -> Published:
    return Published(content=article.content, url=url)

def describe(article: ArticleState) -> str:
    match article:
        case Draft(content):
            return f"Draft: {content[:20]}..."
        case UnderReview(_, reviewer):
            return f"Under review by {reviewer}"
        case Published(_, url):
            return f"Live at {url}"
        case _ as unreachable:
            assert_never(unreachable)

publish(Draft("hello"), "/blog/1")   # error: expected UnderReview, got Draft
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---|---|---|
| **`Literal` + `@overload`** | Precise return types per state value | Overload count grows with states; string-based |
| **Generic state param** | Transitions are type-checked; state is a type, not a value | Verbose; creates many small state classes |
| **Union variants** | Each state carries its own data; exhaustive matching | Requires narrowing at every use site |
| **Protocol per state** | Only valid operations are available on each state type | More types to define; indirection |

## When to use which feature

- **Use `Literal` + `@overload`** for simple state machines with 2-3 states where the state is a string parameter (connection mode, file mode).
- **Use Generic state parameters** when you want the type itself to track which state an object is in, making invalid transitions compile-time errors.
- **Use Union variants** when each state carries different data and you want exhaustive matching — document workflows, order pipelines.
- **Use Protocols** when you want to hide the state representation and expose only the operations valid in each state.

## Source anchors

- [PEP 586 — Literal Types](https://peps.python.org/pep-0586/)
- [PEP 484 — @overload](https://peps.python.org/pep-0484/#function-method-overloading)
- [PEP 484 — Generics](https://peps.python.org/pep-0484/#generics)
- [mypy — Overloaded functions](https://mypy.readthedocs.io/en/stable/more_types.html#function-overloading)
- [typing spec: Literal types](https://typing.readthedocs.io/en/latest/spec/literal.html)
