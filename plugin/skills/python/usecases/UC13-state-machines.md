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

## When to Use It

Use state machines when your domain has **sequential invariants** — operations that must be called in a specific order:

```python
from typing import Generic, TypeVar

class Draft: ...
class Published: ...

S = TypeVar("S")

class Document(Generic[S]):
    @staticmethod
    def create(content: str) -> "Document[Draft]":
        return Document()

def edit(doc: Document[Draft], content: str) -> Document[Draft]:
    return Document()

def publish(doc: Document[Draft]) -> Document[Published]:
    return Document()

doc = Document.create("hello")
published = publish(doc)
edit(published, "oops")  # error: expected Document[Draft], got Document[Published]
```

Use state machines when **data availability depends on state** — some attributes only exist in certain states:

```python
from dataclasses import dataclass

@dataclass
class Empty:
    pass

@dataclass
class Filled:
    value: int

def fill_form(dataclass: Empty, value: int) -> Filled:
    return Filled(value)

def submit(Filled: Filled) -> str:
    return f"Submitted: {Filled.value}"

empty = Empty()
# submit(empty)  # error: Empty has no attribute 'value'
filled = fill_form(empty, 42)
submit(filled)  # OK: value exists in Filled state
```

Use state machines when **wrong sequencing causes bugs** — the type system prevents runtime errors:

```python
from typing import Literal, overload

@overload
def start(txn: Literal["none"]) -> Literal["active"]: ...
@overload
def start(txn: str) -> str: ...

def start(txn: str) -> str:
    return "active" if txn == "none" else txn

@overload
def commit(txn: Literal["active"]) -> Literal["done"]: ...
@overload
def commit(txn: str) -> str: ...

def commit(txn: str) -> str:
    return "done" if txn == "active" else txn

txn = start("none")      # inferred: "active"
done = commit(txn)       # OK
commit("none")           # error at call site, not runtime
```

## When Not to Use It

Avoid state machines for **simple flags** where ordering doesn't matter:

```python
# ❌ Don't use: independent boolean flags
class UserSettings:
    dark_mode: bool
    notifications: bool
    language: str

# ✅ Keep it simple - no state machine needed
```

Avoid state machines for **high-churn state graphs** with many transient states:

```python
# ❌ Don't use: 20+ states with complex transitions
State = Draft | Editing | Reviewing | Approved | Rejected | Resubmitted | ...

# ✅ Better: use a runtime state machine library like FinitePy or simple enum + runtime checks
from enum import Enum

class State(Enum):
    DRAFT = 1
    PUBLISHED = 2

def transition(state: State, event: str) -> State:
    # Runtime validation with clear error messages
    ...
```

Avoid state machines for **shared mutable state** where state is distributed:

```python
# ❌ Don't use: cached values shared across requests
class Cache:
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...

# Type state cannot track distributed state - use runtime checks instead
```

## Antipatterns When Using State Machines

### Antipattern 1: State explosion via over-refinement

```python
# ❌ Anti-pattern: too many states for simple logic
from dataclasses import dataclass

@dataclass
class ButtonState:
    variant: (
        "idle" | "clicked" | "clicked_once" | "clicked_twice" | 
        "hovered_idle" | "hovered_clicked" | "hovered_clicked_once"
    )

# ✅ Better: separate orthogonal concerns
@dataclass
class ButtonState:
    click_count: int
    is_hovered: bool
```

### Antipattern 2: Runtime state diverges from type state

```python
from typing import Generic, TypeVar

class Draft: ...
class Published: ...

S = TypeVar("S")

class Document(Generic[S]):
    def __init__(self) -> None:
        self._actual_state: str = "draft"  # hidden runtime state
    
    def publish(self) -> "Document[Published]":
        self._actual_state = "published"
        return self  # ❌ returns self cast to wrong type
    
    def edit(self) -> "Document[Draft]":
        if self._actual_state != "draft":
            raise RuntimeError("Cannot edit published doc")  # late error
        return self

# ✅ Better: don't mutate - return new instances
class Document(Generic[S]):
    @staticmethod
    def create() -> "Document[Draft]": ...

def publish(doc: Document[Draft]) -> Document[Published]:
    return Document()  # fresh instance, guaranteed Published

def edit(doc: Document[Draft]) -> Document[Draft]:
    return Document()  # fresh instance, guaranteed Draft
```

### Antipattern 3: Excessive `reveal_type` or manual assertions

```python
# ❌ Anti-pattern: trusting the type system without runtime validation
from typing import Generic, TypeVar, assert_never

class Open: ...
class Closed: ...

S = TypeVar("S")

class Socket(Generic[S]):
    def connect(self) -> "Socket[Open]":
        # No runtime check - just assume state transition works
        reveal_type(self)  # Only works during type checking
        return self  # ❌ runtime state unchanged!

# ✅ Better: validate runtime state in transitions
class Socket:
    def __init__(self) -> None:
        self._connected = False
    
    def connect(self) -> "Socket[Open]":
        if self._connected:
            raise RuntimeError("Already connected")
        self._connected = True
        return self  # Now runtime matches type
```

### Antipattern 4: Forgetting exhaustiveness checks

```python
from dataclasses import dataclass
from typing import assert_never

@dataclass
class Idle: pass
@dataclass
class Running: pass  
@dataclass
class Stopped: pass

TaskState = Idle | Running | Stopped

def handle_task(task: TaskState) -> str:
    match task:
        case Idle():
            return "Ready to start"
        case Running():
            return "Executing"
        # ❌ Forgot Stopped case! Bug when new state added

# ✅ Better: assert_never catches missing cases
def handle_task(task: TaskState) -> str:
    match task:
        case Idle():
            return "Ready to start"
        case Running():
            return "Executing"
        case Stopped():
            return "Completed"
        case _:
            assert_never(task)  # Compile error if new state added
```

## Antipatterns with Other Techniques (where State Machines Help)

### Antipattern 1: Nested if/else chains for state

```python
# ❌ Anti-pattern: if/else cascade
class Order:
    def __init__(self):
        self.status: str = "pending"
    
    def checkout(self) -> None:
        if self.status == "pending":
            self.status = "processing"
        elif self.status == "processing":
            raise ValueError("Already processing")
        elif self.status == "completed":
            raise ValueError("Already completed")
        elif self.status == "cancelled":
            raise ValueError("Cannot checkout cancelled order")
        else:
            raise ValueError(f"Unknown status: {self.status}")

# ✅ Better: discriminated union with exhaustive match
from dataclasses import dataclass, field

@dataclass
class PendingOrder:
    items: list[str] = field(default_factory=list)

@dataclass  
class ProcessingOrder:
    items: list[str]
    payment_id: str

@dataclass
class CompletedOrder:
    items: list[str]
    tracking_number: str

OrderState = PendingOrder | ProcessingOrder | CompletedOrder

def checkout(order: PendingOrder) -> ProcessingOrder:
    return ProcessingOrder(items=order.items, payment_id="pay_123")

def ship(order: ProcessingOrder) -> CompletedOrder:
    return CompletedOrder(items=order.items, tracking_number="TRK456")

# checkout(CompletedOrder(...))  # error: expected PendingOrder
```

### Antipattern 2: Union of boolean flags

```python
# ❌ Anti-pattern: inconsistent flag combinations
class Payment:
    has_card: bool = False
    has_token: bool = False
    is_processing: bool = False
    is_completed: bool = False
    # Can be in invalid state: has_card=True AND is_completed=True

# ✅ Better: mutually exclusive states
from dataclasses import dataclass

@dataclass
class EmptyPayment: pass

@dataclass
class HasCardPayment:
    card: str

@dataclass
class ProcessingPayment:
    transaction_id: str

@dataclass
class CompletedPayment:
    receipt: str

PaymentState = EmptyPayment | HasCardPayment | ProcessingPayment | CompletedPayment
# Exactly one state at a time - no invalid combinations
```

### Antipattern 3: Magic string state values

```python
# ❌ Anti-pattern: string states with no validation
class Workflow:
    def __init__(self):
        self.state: str = "draft"
    
    def approve(self) -> None:
        if self.state != "draft":  # What if typo: "drafft"?
            raise ValueError("Can only approve drafts")
        self.state = "review"

# ✅ Better: literal types enforce correct values
from typing import Literal

class Workflow:
    def __init__(self):
        self.state: Literal["draft", "review", "approved"] = "draft"
    
    def approve(self) -> None:
        if self.state != "draft":
            raise ValueError("Can only approve drafts")
        self.state = "review"  # error: cannot assign "review" to "draft"

# Or better: use separate state classes
@dataclass
class Draft: pass
@dataclass  
class Review: pass
@dataclass
class Approved: pass

def approve(workflow: Draft) -> Review:
    return Review()

# approve(Review())  # error: expected Draft, got Review
```

### Antipattern 4: Mutable state with runtime guards everywhere

```python
# ❌ Anti-pattern: runtime guards scattered throughout
class Editor:
    def __init__(self):
        self.state: Literal["draft", "published"] = "draft"
        self.content: str = ""
    
    def edit(self, content: str) -> None:
        if self.state != "draft":
            raise RuntimeError("Cannot edit published document")
        self.content = content
    
    def publish(self) -> None:
        if self.state != "draft":
            raise RuntimeError("Already published")
        self.state = "published"
    
    def delete(self) -> None:
        if self.state == "published":
            raise RuntimeError("Cannot delete published document")
        self.content = ""

editor = Editor()
editor.publish()
editor.edit("oops")  # Runtime error! Too late.

# ✅ Better: immutable state machine
from typing import Generic, TypeVar

class Draft: ...
class Published: ...

S = TypeVar("S", Draft, Published)

class Editor(Generic[S]):
    def __init__(self, content: str) -> None:
        self._content = content
    
    @staticmethod
    def create(content: str) -> "Editor[Draft]":
        return Editor(content)
    
    @property
    def content(self) -> str:
        return self._content

def edit(editor: Editor[Draft], content: str) -> Editor[Draft]:
    return Editor(content)

def publish(editor: Editor[Draft]) -> Editor[Published]:
    return Editor(editor.content)

# Cannot call delete on Published - method doesn't exist
# Cannot call edit after publish - type error at compile time
```
