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
    print(shape.r)        # error: Cannot access attribute "r" for class "Drawable"

render(Circle(5.0))    # OK — Circle is structurally Drawable
render(Square(3.0))    # OK — Square is structurally Drawable
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Structural typing** [-> T07](T07-structural-typing.md) | Protocol IS structural typing. It defines the shape a type must have, achieving existential hiding through structural compatibility rather than nominal subtyping. |
| **Generics / TypeVar** [-> T04](T04-generics-bounds.md) | `TypeVar` bound to a Protocol creates a universally-quantified variable constrained to the protocol. Without the bound, an unbound TypeVar with Protocol parameters approximates existential quantification. |
| **Union types** [-> T02](T02-union-intersection.md) | `Circle | Square` is a closed union (the caller knows the options). `Drawable` is an open existential (any structurally-compatible type works). |
| **Type narrowing** [-> T14](T14-type-narrowing.md) | `isinstance` with `runtime_checkable` protocols narrows a value to the protocol type, recovering the existential interface from an `object` or `Any`. |
| **Callable typing** [-> T22](T22-callable-typing.md) | `Protocol` with `__call__` defines existential callable types -- "something callable with signature X" without naming the concrete callable. |

## Gotchas and limitations

1. **No true existential quantification.** Python's type system cannot express "there exists a type T such that ...". Protocol is structural subtyping, not existential packing. You *can* return a value annotated as a protocol type to hide its concrete type from the checker (see "When to Use It" below), but the hiding is check-time only -- there is no runtime sealing comparable to Scala's abstract type members or Rust's `dyn Trait`.

2. **runtime_checkable is shallow.** `@runtime_checkable` only checks attribute existence, not signatures or types. `isinstance(obj, Drawable)` returns `True` if `obj` has a `draw` attribute, even if it is not callable. Pyright (strict) even flags such classes as unsafe overlaps:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Drawable(Protocol):
    def draw(self) -> str: ...

class Fake:
    draw = 42   # not callable!

# Returns True at runtime — isinstance only checks the attribute exists
print(isinstance(Fake(), Drawable))   # error: Class overlaps "Drawable" unsafely and could produce a match at runtime
```

3. **Protocol members must be defined in the Protocol.** You cannot use methods not declared in the Protocol, even if the concrete type has them. This is the existential hiding in action, but it can feel restrictive.

4. **Variance inference requires PEP 695 syntax.** With Python 3.12+ type parameter syntax (`class Source[T](Protocol): ...`), the checker infers variance automatically. Only the legacy spelling lacks inference: a pre-3.12 `Protocol[T]` needs an explicit `TypeVar("T_co", covariant=True)` or `TypeVar("T_contra", contravariant=True)` when variance matters.

5. **Generic Protocols require careful TypeVar scoping.** A generic Protocol creates a family of protocols. Confusing the type parameter's scope between the Protocol definition and usage leads to subtle type errors.

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
from collections.abc import Iterator
from typing import Protocol

class DataSource[T](Protocol):
    def fetch(self) -> Iterator[T]: ...
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

## When to Use It

**Use Protocol-based existential types when:**

1. **You need open extensibility** — new implementations should be addable without changing consumer code:

```python
from typing import Protocol

class Plugin(Protocol):
    def activate(self) -> None: ...
    name: str

class LoggerPlugin:
    name = "logger"
    def activate(self) -> None:
        print("logging on")

class CachePlugin:
    name = "cache"
    def activate(self) -> None:
        print("caching on")

# Any new structurally-compatible type works without modifications
class PluginManager:
    def __init__(self) -> None:
        self._plugins: list[Plugin] = []

    def add(self, p: Plugin) -> None:
        self._plugins.append(p)

    def activate_all(self) -> None:
        for p in self._plugins:
            p.activate()
```

2. **You need to hide implementation details** — return the protocol type from a factory so internal state and helpers do not leak into the caller's view:

```python
from typing import Protocol

class Counter(Protocol):
    def increment(self) -> None: ...
    def get(self) -> int: ...

class _Counter:
    def __init__(self) -> None:
        self._count = 0  # hidden implementation detail
    def increment(self) -> None:
        self._count += 1
    def get(self) -> int:
        return self._count

def new_counter() -> Counter:
    return _Counter()  # caller sees only the Counter interface

c = new_counter()
c.increment()
print(c.get())   # 1
# c._count       # rejected by the checker: "Counter" has no attribute "_count"
```

3. **You need uniform behavior on heterogeneous data:**

```python
from typing import Protocol

class Serializable(Protocol):
    def to_json(self) -> str: ...

class User:
    def to_json(self) -> str:
        return '{"user": "alice"}'

class Product:
    def to_json(self) -> str:
        return '{"product": "widget"}'

items: list[Serializable] = [User(), Product()]

# Uniform serialization via the protocol
data = [i.to_json() for i in items]
```

## When NOT to Use It

**Avoid Protocol-based existential types when:**

1. **You need exhaustive type checking** — use a `Literal`-discriminated union when the set of variants is closed:

```python
from dataclasses import dataclass
from typing import Literal, Protocol

# Bad: a Protocol hides which variant you have
class Shaped(Protocol):
    def area(self) -> float: ...

def describe(s: Shaped) -> str:
    return f"area={s.area()}"   # no way to handle circles vs squares differently

# Good: a Literal-discriminated union enables exhaustive checks
@dataclass
class Circle:
    kind: Literal["circle"] = "circle"
    radius: float = 0.0

@dataclass
class Square:
    kind: Literal["square"] = "square"
    side: float = 0.0

type Shape = Circle | Square

def use_shape(s: Shape) -> float:
    if s.kind == "circle":
        return 3.14 * s.radius ** 2   # s narrowed to Circle
    elif s.kind == "square":
        return s.side ** 2            # s narrowed to Square
    # checker proves all cases handled — no fall-through possible
```

2. **You need variant-specific operations** — use a union plus narrowing when consumers must get back to the concrete type:

```python
from dataclasses import dataclass
from typing import Protocol

# Bad: the Protocol hides type-specific operations
class Pet(Protocol):
    def feed(self) -> None: ...

def feed_all(pets: list[Pet]) -> None:
    for p in pets:
        p.feed()
        # p.bark()  # rejected: "bark" is not declared on Pet

# Good: a union lets you narrow back to the variant
@dataclass
class Dog:
    name: str
    def feed(self) -> None: ...
    def bark(self) -> str:
        return "woof"

@dataclass
class Cat:
    name: str
    def feed(self) -> None: ...
    def meow(self) -> str:
        return "meow"

def greet(p: Dog | Cat) -> str:
    if isinstance(p, Dog):
        return p.bark()   # narrowed to Dog
    return p.meow()       # narrowed to Cat
```

## Antipatterns When Using Protocol Existentials

### A. Assuming the protocol hides attributes at runtime

The erasure is check-time only. Attributes of the concrete type remain reachable at runtime; do not rely on a Protocol for security or true encapsulation.

```python
from typing import Protocol

class Simple(Protocol):
    foo: str

class Concrete:
    foo: str = "bar"
    secret: int = 42

def create_simple() -> Simple:
    return Concrete()

s = create_simple()
# s.secret  # rejected by the checker — but still accessible at runtime
```

### B. Leaking implementation details through inferred return types

If a factory has no return annotation, the checker infers the concrete class and every internal attribute leaks into the caller's view. Annotate the protocol return type to erase them.

```python
from typing import Protocol

class Box(Protocol):
    value: int

class _Box:
    def __init__(self, v: int) -> None:
        self.value = v
        self._cache: dict[str, int] = {}  # implementation detail

def create_box(n: int) -> "_Box":   # Bad: concrete return type — _cache leaks
    return _Box(n)

def create_box_clean(n: int) -> Box:   # Good: annotation erases to the protocol
    return _Box(n)

b = create_box(1)
# b._cache       # visible to the checker (and flagged only as private usage)

b2 = create_box_clean(1)
# b2._cache      # rejected: "Box" has no attribute "_cache"
```

### C. Monolithic protocols

A fat protocol forces every implementor to provide all members, even unused ones. Compose small protocols instead.

```python
from typing import Protocol

# Bad: monolithic protocol
class Entity(Protocol):
    id: str
    name: str
    created_at: str
    def update(self) -> None: ...
    def delete(self) -> None: ...
    def clone(self) -> "Entity": ...
    def serialize(self) -> str: ...
    def validate(self) -> bool: ...

# Every implementor provides all 8 members, even if unused

# Good: compose smaller protocols
class Identifiable(Protocol):
    id: str

class Named(Protocol):
    name: str

class Timestamped(Protocol):
    created_at: str

class Mutable(Protocol):
    def update(self) -> None: ...
    def delete(self) -> None: ...

# Use inheritance to compose where needed
class ComposedEntity(Identifiable, Named, Timestamped, Mutable, Protocol):
    pass
```

### D. Protocol tied to one implementation

```python
from typing import Protocol

# Bad: protocol tied to dog-specific details
class DogProtocol(Protocol):
    name: str
    breed: str  # too specific — only dogs have this
    def bark(self) -> str: ...

# Only Dogs can implement this; can't extend to other animals

# Good: abstract the shared behavior
class Animal(Protocol):
    name: str
    def make_sound(self) -> str: ...

class Dog:
    name = "Rex"
    def make_sound(self) -> str:
        return "woof"

class Cat:
    name = "Whiskers"
    def make_sound(self) -> str:
        return "meow"

animals: list[Animal] = [Dog(), Cat()]
```

## Antipatterns Fixed by Protocol Existentials

### A. Unbounded closed union for an open family

```python
from dataclasses import dataclass
from typing import Literal, Protocol

# Bad: closed union grows unbounded as variants are added
@dataclass
class TextWidget:
    label: str
    kind: Literal["text"] = "text"

@dataclass
class NumberWidget:
    min: float
    max: float
    kind: Literal["number"] = "number"

type Widget = TextWidget | NumberWidget  # ... imagine 20 more variants

def render_widget(w: Widget) -> str:
    match w:                  # every new variant edits this match
        case TextWidget():
            return f"<label>{w.label}</label>"
        case NumberWidget():
            return f"<input type='number' min={w.min} max={w.max}>"

# Good: Protocol for open extensibility — each widget renders itself
class Renderable(Protocol):
    def render(self) -> str: ...

class TextWidgetImpl:
    def __init__(self, label: str) -> None:
        self.label = label
    def render(self) -> str:
        return f"<label>{self.label}</label>"

class NumberWidgetImpl:
    def __init__(self, min_val: float, max_val: float) -> None:
        self.min = min_val
        self.max = max_val
    def render(self) -> str:
        return f"<input type='number' min={self.min} max={self.max}>"

# Adding new widgets doesn't break render_any()
def render_any(w: Renderable) -> str:
    return w.render()
```

### B. God-config dataclass instead of polymorphic components

```python
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

# Bad: one dataclass enumerates every possible configuration
@dataclass
class ButtonConfig:
    text: str | None = None
    icon: str | None = None
    on_click: Callable[[], None] | None = None
    disabled: bool = False
    loading: bool = False
    # ... 30 more optional fields — consumers must handle every None combination

# Good: polymorphic components behind one protocol
class Component(Protocol):
    def render(self) -> str: ...

class TextButton:
    def __init__(self, text: str, on_click: Callable[[], None] | None = None) -> None:
        self.text = text
        self.on_click = on_click
    def render(self) -> str:
        return f"<button onclick={self.on_click}>{self.text}</button>"

class IconButton:
    def __init__(self, icon: str) -> None:
        self.icon = icon
    def render(self) -> str:
        return f"<button><img src={self.icon}/></button>"

# Each component handles its own configuration
buttons: list[Component] = [TextButton("Click"), IconButton("/icon.svg")]
```

### C. Manual `hasattr` capability checks

```python
from typing import Protocol

class Event(Protocol):
    name: str

class Handler(Protocol):
    def on_event(self, e: Event) -> None: ...

class ClickEvent:
    name = "click"

class PrintHandler:
    def on_event(self, e: Event) -> None:
        print(e.name)

# Bad: manual capability checking — the checker learns nothing
def register_bad(h: object) -> None:
    if hasattr(h, "on_event"):
        ...  # signature unverified; misuse surfaces only at runtime

# Good: Protocol enforces the capability at check time
def register_good(h: Handler) -> None:
    h.on_event(ClickEvent())   # checker verifies h has a compatible on_event

register_good(PrintHandler())
```

## Use-case cross-references

- [-> UC01](../usecases/UC01-invalid-states.md) -- Protocol-based existentials restrict operations to declared interfaces, preventing misuse of hidden concrete types.
- [-> UC02](../usecases/UC02-domain-modeling.md) -- Domain boundaries use Protocols to accept any type satisfying domain constraints without coupling to concrete implementations.

## Source anchors

- [PEP 544 -- Protocols: Structural subtyping](https://peps.python.org/pep-0544/)
- [typing -- Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [mypy -- Protocols and structural subtyping](https://mypy.readthedocs.io/en/stable/protocols.html)
- [pyright -- Protocols](https://microsoft.github.io/pyright/#/protocols)
