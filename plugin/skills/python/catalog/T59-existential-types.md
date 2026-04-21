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

2. **You need to hide implementation details** — internal state or helpers shouldn't leak:

```python
class Counter:
    def increment(self) -> None: ...
    def get(self) -> int: ...

def new_counter() -> Counter:
    count = 0  # hidden closure variable
    def increment() -> None:
        nonlocal count
        count += 1
    def get() -> int:
        return count
    return type("Counter", (), {"increment": increment, "get": get})()

c = new_counter()
c.increment()
# c.count  # AttributeError: can't access hidden state
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

1. **You need exhaustive type checking** — use `Union` with discriminated literals when the set is closed:

```python
from typing import Protocol
from dataclasses import dataclass

# Bad: Protocol hides which variant you have
class Shape(Protocol):
    def area(self) -> float: ...

def use_shape(s: Shape) -> None:
    a = s.area()
    # No way to handle circles vs squares differently

# Good: discriminated Union enables exhaustive checks
@dataclass
class Circle:
    kind: str = "circle"
    radius: float = 0.0

@dataclass
class Square:
    kind: str = "square"
    side: float = 0.0

Shape = Circle | Square

def use_shape(s: Shape) -> float:
    if s.kind == "circle":
        return 3.14 * s.radius ** 2
    elif s.kind == "square":
        return s.side ** 2
    # Type checker knows all cases handled (with narrow types)
```

2. **You need access to type-specific methods** — don't hide features you'll need:

```python
from typing import Protocol

# Bad: Protocol hides type-specific operations
class Pet(Protocol):
    def feed(self) -> None: ...

dogs_and_cats: list[Pet] = [...]
for p in dogs_and_cats:
    p.feed()
    # Can't call dog-specific methods later

# Good: use Union when you need type-specific ops
from dataclasses import dataclass

@dataclass
class Dog:
    name: str
    def feed(self) -> None: ...
    def bark(self) -> None: ...

@dataclass
class Cat:
    name: str
    def feed(self) -> None: ...
    def meow(self) -> None: ...

def is_dog(p: Dog | Cat) -> bool:
    return isinstance(p, Dog)

for p in [Dog("Rex"), Cat("Whiskers")]:
    if is_dog(p):
        p.bark()  # OK
```

3. **The abstraction leaks anyway** — Protocol is structural; extra attributes remain accessible:

```python
from typing import Protocol

class Simple(Protocol):
    foo: str

def create_simple() -> Simple:
    return type("Simple", (), {"foo": "bar", "secret": 42})()

s = create_simple()
# s.secret  # Accessible! Protocol hides only at type-check time.
```

## Antipatterns When Using This Technique

**P1: Protocol with too many members**

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

# Every implementor provides all 7, even if unused

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

# Use intersections where needed
type_entity = Identifiable & Named & Timestamped & Mutable
```

**P2: Returning implementation type from factory**

```python
from typing import Protocol

class Box(Protocol):
    value: int

def create_box(n: int) -> Box:
    # Bad: implementation details leak through type inference
    class _Box:
        def __init__(self, v: int):
            self.value = v
            self._cache = {}  # leaks extra props
    return _Box(n)

b = create_box(1)
# b._cache  # Accessible via inference

# Good: use runtime_checkable and explicit interface
from typing import runtime_checkable

@runtime_checkable
class BoxClean(Protocol):
    value: int

def create_box_clean(n: int) -> BoxClean:
    return type("Box", (), {"value": n})()

b = create_box_clean(1)
# b._cache  # AttributeError
```

**P3: Protocol with instance state that can't be checked**

```python
from typing import runtime_checkable, Protocol

@runtime_checkable
class HasMethod(Protocol):
    def method(self) -> int: ...

class Fake:
    method = 42  # not callable

isinstance(Fake(), HasMethod)  # True — shallow check only
```

**P4: Protocol tied to one implementation**

```python
from typing import Protocol

# Bad: protocol tied to dog-specific details
class DogProtocol(Protocol):
    name: str
    def bark(self) -> str: ...
    breed: str  # too specific

# Only Dogs can implement this; can't extend to other animals

# Good: abstract shared behavior
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
```

## Antipatterns Where This Technique Is Better

**A1: Union explosion for open-ended types**

```python
from dataclasses import dataclass

# Bad: Union grows unbounded
@dataclass
class TextWidget:
    type: str = "text"
    label: str = ""

@dataclass
class NumberWidget:
    type: str = "number"
    min: float = 0
    max: float = 100

@dataclass
class DateWidget:
    type: str = "date"
    default: str = ""

# ... 20 more widget variants

Widget = TextWidget | NumberWidget | DateWidget  # unmanageable

def render_widget(w: Widget) -> str:
    # 20-case match, breaks when adding new widgets
    if w.type == "text":
        return f"<label>{w.label}</label>"
    # ... 19 more cases

# Good: use Protocol for open extensibility
from typing import Protocol

class WidgetProto(Protocol):
    type: str
    def render(self) -> str: ...

class TextWidget:
    type = "text"
    def __init__(self, label: str):
        self.label = label
    def render(self) -> str:
        return f"<label>{self.label}</label>"

class NumberWidget:
    type = "number"
    def __init__(self, min_val: float, max_val: float):
        self.min = min_val
        self.max = max_val
    def render(self) -> str:
        return f"<input type='number' min={self.min} max={self.max}>"

# Adding new widgets doesn't break render()
def render_widget(w: WidgetProto) -> str:
    return w.render()
```

**A2: Giant dataclass with optional fields**

```python
from dataclasses import dataclass

# Bad: dataclass enumerates all states
@dataclass
class ButtonConfig:
    text: str | None = None
    icon: str | None = None
    on_click: callable | None = None
    on_hover: callable | None = None
    disabled: bool = False
    loading: bool = False
    # ... 30 more optional fields

# Consumer must handle all combinations of None vs value

# Good: polymorphic dataclasses
from typing import Protocol

class Component(Protocol):
    def render(self) -> str: ...

class TextButton:
    def __init__(self, text: str, on_click: callable | None = None):
        self.text = text
        self.on_click = on_click
    def render(self) -> str:
        return f"<button onclick={self.on_click}>{self.text}</button>"

class IconButton:
    def __init__(self, icon: str):
        self.icon = icon
    def render(self) -> str:
        return f"<button><img src={self.icon}/></button>"

# Each handles its own configuration
buttons: list[Component] = [TextButton("Click"), IconButton("/icon.svg")]
```

**A3: Manual type checks (if/hasattr) everywhere**

```python
# Bad: manual capability checking
from typing import Any

def register_handler(h: Any) -> None:
    if hasattr(h, "on_event"):
        h.on_event({})  # No type checking!

# Good: Protocol enforces capability at type-check time
from typing import Protocol

class Event(Protocol):
    pass

class Handler(Protocol):
    def on_event(self, e: Event) -> None: ...

def register_handler(h: Handler) -> None:
    h.on_event({})  # Type checker verifies h has on_event
```
