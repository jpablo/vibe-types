# Trait Objects & Runtime Polymorphism (via ABC and Protocol)

> **Since:** `ABC` Python 3.0 (PEP 3119); `Protocol` Python 3.8 (PEP 544); `@runtime_checkable` Python 3.8 (PEP 544) | **Backport:** `typing_extensions`

## What it is

In Rust, a `dyn Trait` is a fat pointer that enables runtime dispatch against an interface. Python achieves the same role through two mechanisms: **Abstract Base Classes (ABCs)** for nominal interface dispatch, and **Protocols** for structural interface dispatch. Both allow you to write functions that accept "anything implementing this interface" and dispatch method calls at runtime through Python's standard virtual method table (the MRO).

**ABCs** require explicit inheritance — a class must declare `class Impl(MyABC):` and implement all `@abstractmethod` members. The type checker and the runtime (`isinstance`) both recognize the subtyping relationship. **Protocols** require no inheritance — any class with the right methods satisfies the Protocol structurally. With `@runtime_checkable`, Protocols also support `isinstance` checks (with caveats: only method existence is checked, not signatures).

Both ABCs and Protocols serve as "trait object" types: you can annotate a parameter as `Drawable` (ABC) or `Renderable` (Protocol), and the type checker ensures only compatible implementations are passed.

## What constraint it enforces

**ABC parameters require explicit subclass inheritance and implementation of all abstract methods. Protocol parameters require structural compatibility — matching methods with correct signatures. Both enable runtime polymorphism where the caller depends only on the interface, not the concrete type.**

## Minimal snippet

```python
from abc import ABC, abstractmethod
from typing import Protocol, override

# Nominal approach: ABC
class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

class Circle(Shape):
    def __init__(self, r: float) -> None:
        self.r = r
    @override
    def area(self) -> float:
        return 3.14159 * self.r ** 2

# Structural approach: Protocol
class HasArea(Protocol):
    def area(self) -> float: ...

def print_area(shape: HasArea) -> None:
    print(f"Area: {shape.area()}")

print_area(Circle(5.0))       # OK — satisfies both Shape (ABC) and HasArea (Protocol)

class AdHocRect:
    def area(self) -> float:
        return 12.0

print_area(AdHocRect())       # OK — satisfies HasArea structurally (no inheritance)
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **ABC** [-> T05](T05-type-classes.md) | ABCs define nominal interfaces with `@abstractmethod`. They are the traditional approach to trait-like polymorphism in Python. |
| **Protocol** [-> T07](T07-structural-typing.md) | Protocols define structural interfaces. They serve the same dispatch role as ABCs but without requiring inheritance — closer to Go's implicit interfaces or Rust's duck-typed traits. |
| **Type narrowing** [-> T14](T14-type-narrowing.md) | `isinstance(obj, Shape)` narrows `Shape | str` to `Shape`. For `@runtime_checkable` Protocols, `isinstance(obj, HasArea)` narrows at runtime (checking method existence only). |
| **Generics** [-> T04](T04-generics-bounds.md) | `TypeVar("T", bound=HasArea)` creates a generic function that accepts any type satisfying the interface while preserving the concrete type in the return. |
| **Callable types** [-> T22](T22-callable-typing.md) | A Protocol with `__call__` serves as a typed function trait — more precise than `Callable[...]` because it can include attributes alongside the call signature. |

## Gotchas and limitations

1. **ABCs require inheritance; Protocols do not.** This is the fundamental trade-off. ABCs give clearer error messages when a subclass forgets to implement a method (error at class definition time). Protocols give errors only at call sites where the incomplete type is used.

2. **`@runtime_checkable` Protocol checks are shallow.** `isinstance(obj, MyProtocol)` only verifies that the required method *names* exist as attributes. It does not check parameter types, return types, or even that the attribute is callable. pyright even flags such checks as unsafe:

   ```python
   from typing import Protocol, runtime_checkable

   @runtime_checkable
   class Processor(Protocol):
       def process(self, data: bytes) -> str: ...

   class Fake:
       process = 42   # attribute, not a method!

   # True at runtime — the 'process' attribute exists, nothing else is verified:
   print(isinstance(Fake(), Processor))  # error: Class overlaps "Processor" unsafely and could produce a match at runtime
   ```

3. **ABC + Protocol mix is possible but rarely needed.** A class can satisfy a Protocol *and* inherit from an ABC. These are checked independently — the ABC checks at class creation, the Protocol checks at usage sites. Combining them adds complexity without clear benefit in most cases.

4. **No multi-dispatch on trait objects.** Python's method resolution is single-dispatch by default. For multi-method dispatch on multiple trait parameters, use `functools.singledispatch` or a library like `multipledispatch`. Type-checker support for `singledispatch` varies (mypy ships a dedicated plugin; pyright relies on the typeshed stubs for `functools.singledispatch`).

5. **Performance of Protocol isinstance checks.** `@runtime_checkable` Protocol `isinstance` checks inspect the class's MRO for each required member on every call. For hot paths, prefer `isinstance` against an ABC (which uses `__subclasshook__` caching) or precomputed type checks.

6. **Abstract properties require careful syntax.** Combining `@abstractmethod` with `@property` requires the decorators in the correct order:

   ```python
   from abc import ABC, abstractmethod

   class Labeled(ABC):
       @property
       @abstractmethod
       def label(self) -> str: ...   # correct order: @property on top
   ```

## Beginner mental model

Think of an **ABC** as a job description posted by a company — you must formally apply (inherit) and prove you have every listed qualification (implement abstract methods). A **Protocol** is like a freelance marketplace: anyone who can demonstrably do the work (has the right methods) gets the contract, no formal application needed. Both result in the same thing — someone doing the job at runtime — but the hiring process differs. `isinstance` is the background check: thorough for ABC hires (checks the entire inheritance chain), but only a quick resume scan for Protocol freelancers (checks method names exist).

## Example A — Plugin system with ABC dispatch

```python
from abc import ABC, abstractmethod
from typing import override

class Exporter(ABC):
    @abstractmethod
    def export(self, data: dict[str, object]) -> bytes: ...

    @abstractmethod
    def content_type(self) -> str: ...

class JsonExporter(Exporter):
    @override
    def export(self, data: dict[str, object]) -> bytes:
        import json
        return json.dumps(data).encode()

    @override
    def content_type(self) -> str:
        return "application/json"

class CsvExporter(Exporter):
    @override
    def export(self, data: dict[str, object]) -> bytes:
        header = ",".join(data.keys())
        values = ",".join(str(v) for v in data.values())
        return f"{header}\n{values}".encode()

    @override
    def content_type(self) -> str:
        return "text/csv"

def send_report(exporter: Exporter, data: dict[str, object]) -> None:
    payload = exporter.export(data)
    print(f"Sending {len(payload)} bytes as {exporter.content_type()}")

send_report(JsonExporter(), {"name": "Alice", "score": 95})   # OK
send_report(CsvExporter(), {"name": "Alice", "score": 95})    # OK
send_report("not an exporter", {})  # error: Argument of type "str" cannot be assigned to parameter "exporter" of type "Exporter"
```

## Example B — Protocol-based polymorphism with runtime checking

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Renderable(Protocol):
    def render(self) -> str: ...

class HtmlWidget:
    def __init__(self, tag: str, content: str) -> None:
        self.tag = tag
        self.content = content

    def render(self) -> str:
        return f"<{self.tag}>{self.content}</{self.tag}>"

class MarkdownBlock:
    def __init__(self, text: str) -> None:
        self.text = text

    def render(self) -> str:
        return f"**{self.text}**"

def render_all(items: list[Renderable]) -> str:
    return "\n".join(item.render() for item in items)

components: list[Renderable] = [
    HtmlWidget("h1", "Title"),
    MarkdownBlock("Bold text"),
]

print(render_all(components))   # OK

# Runtime check
widget = HtmlWidget("p", "hi")
assert isinstance(widget, Renderable)   # True — has render() -> str

# Filtering mixed lists at runtime
mixed: list[object] = [HtmlWidget("p", "a"), 42, MarkdownBlock("b")]
renderables = [x for x in mixed if isinstance(x, Renderable)]
print(render_all(renderables))   # OK — narrowed to Renderable
```

## Use-case cross-references

- [-> UC05](../usecases/UC05-structural-contracts.md) — Protocols define structural contracts for plug-in architectures without coupling to specific classes.
- [-> UC04](../usecases/UC04-generic-constraints.md) — TypeVars bounded by ABC or Protocol enable generic algorithms over trait-like interfaces.
- [-> UC07](../usecases/UC07-callable-contracts.md) — Callable Protocols combine runtime dispatch with precise signature typing.

## When to use

- **Plugin/extension systems**: When third parties should add implementations without modifying core code.
- **Strategy pattern**: When behavior should be swappable at runtime (e.g., `CompressionStrategy`, `AuthStrategy`).
- **Testing**: When you want to inject mocks/stubs that satisfy the same interface as production code.
- **Heterogeneous collections**: When you need a single collection holding different concrete types that share behavior.
- **Third-party integration**: When you cannot modify a third-party class but can verify it has the right methods (Protocol).

```python
# Strategy pattern — behavior is swappable
from typing import Protocol

class Strategy(Protocol):
    def execute(self, x: int) -> int: ...

def apply(s: Strategy, x: int) -> int:
    return s.execute(x)

class Doubler:
    def execute(self, x: int) -> int:
        return x * 2

apply(Doubler(), 5)  # 10
```

## Antipatterns when using trait objects

### A. Trait object for a closed set of variants

```python
# BAD: an open interface hides a closed set — no exhaustiveness checking
from typing import Protocol

class StatusProto(Protocol):
    kind: str

def handle(s: StatusProto) -> None:
    if s.kind == "ok":
        print("ok")
    # the "error" case is easily forgotten — no checker support
```

```python
# BETTER: typed variants with pattern matching — the checker enforces coverage
from dataclasses import dataclass
from typing import Literal

@dataclass
class OkStatus:
    kind: Literal["ok"]
    code: int

@dataclass
class ErrorStatus:
    kind: Literal["error"]
    code: int

type Status = OkStatus | ErrorStatus

def handle(s: Status) -> str:
    match s:
        case OkStatus():
            return "all good"
        case ErrorStatus(code=code):
            return f"failed with {code}"
    # adding a new variant to Status makes this error:
    # "must return value on all code paths"
```

### B. God interfaces mixing orthogonal concerns

```python
from abc import ABC, abstractmethod

# BAD: mixes orthogonal concerns into one fat interface
class GodService(ABC):
    @abstractmethod
    def process(self) -> None: ...
    @abstractmethod
    def serialize(self) -> str: ...
    @abstractmethod
    def save(self, path: str) -> None: ...
    @abstractmethod
    def log(self, msg: str) -> None: ...

# BETTER: separate interfaces per concern; compose where needed
class Processable(ABC):
    @abstractmethod
    def process(self) -> None: ...

class Serializable(ABC):
    @abstractmethod
    def serialize(self) -> str: ...

class Service(Processable, Serializable):
    ...
```

### C. Accidental structural satisfaction

```python
from abc import ABC, abstractmethod
from typing import Protocol, override

# BAD: Dog satisfies the Pet Protocol by accident
class Pet(Protocol):
    def meow(self) -> str: ...

class Dog:
    def meow(self) -> str:
        return ""  # wrong behavior, but it type-checks!

pet: Pet = Dog()  # accepted — structural match

# BETTER: when membership should be deliberate, use a nominal ABC
class PetABC(ABC):
    @abstractmethod
    def meow(self) -> str: ...

class Cat(PetABC):
    @override
    def meow(self) -> str:
        return "meow"

class DogNominal:
    def meow(self) -> str:
        return ""

pet2: PetABC = Cat()         # OK — explicit subclass
pet3: PetABC = DogNominal()  # error: Type "DogNominal" is not assignable to declared type "PetABC"
```

### D. Evolving a shared Protocol in place

```python
from typing import Protocol

# BAD: adding a required member to a shared Protocol breaks every existing implementation
class Payload(Protocol):
    id: str
    metadata: dict[str, object]   # newly added — old implementors no longer satisfy Payload

# BETTER: keep the original Protocol and extend it in a new one
class PayloadV1(Protocol):
    id: str

class PayloadWithMeta(PayloadV1, Protocol):
    metadata: dict[str, object]
```

Note the explicit `Protocol` in the base list of `PayloadWithMeta`. Writing `class PayloadWithMeta(PayloadV1):` would create a *concrete nominal* class, silently losing structural typing — subclassing a Protocol only produces another Protocol when `Protocol` itself is re-listed.

### E. `@runtime_checkable` on everything

```python
# BAD: @runtime_checkable adds runtime overhead and is only needed for isinstance checks
from typing import Protocol, runtime_checkable

@runtime_checkable  # unnecessary if no isinstance checks are performed
class CheckableConfig(Protocol):
    def get(self, key: str) -> object: ...

# BETTER: omit @runtime_checkable unless you need runtime isinstance checks
class Config(Protocol):
    def get(self, key: str) -> object: ...
```

## Antipatterns with other techniques (where this helps)

### A. Using generics when a trait object is sufficient

```python
# BAD: TypeVar preserves concrete type unnecessarily, complicates API
from typing import TypeVar, Protocol

T = TypeVar("T", bound="Runnable")

class Runnable(Protocol):
    def run(self) -> None: ...

def process(item: T) -> T:
    item.run()
    return item  # preserves concrete type, harder to compose

# BETTER: trait object erases concrete type, simpler API
def run(item: Runnable) -> None:
    item.run()  # no return type complexity
```

### B. Deep inheritance hierarchies instead of composition

```python
# BAD: inheritance explosion — every feature combination needs a class
class Reader:
    def read(self) -> str: ...

class FileReader(Reader):
    def __init__(self, path: str) -> None: ...

class BufferedFileReader(FileReader):
    def __init__(self, path: str, buf_size: int) -> None: ...

class ErrorHandlingBufferedFileReader(BufferedFileReader):
    def __init__(self, path: str, buf_size: int, retry: int) -> None: ...  # fragile
```

```python
# BETTER: a Protocol trait object lets independent wrappers compose
from typing import Protocol

class Reader(Protocol):
    def read(self) -> str: ...

class FileReader:
    def __init__(self, path: str) -> None:
        self._path = path

    def read(self) -> str:
        with open(self._path) as f:
            return f.read()

class Retry:
    def __init__(self, inner: Reader, attempts: int) -> None:
        self._inner = inner
        self._attempts = attempts

    def read(self) -> str:
        for _ in range(self._attempts):
            try:
                return self._inner.read()
            except OSError:
                continue
        raise RuntimeError("All retries failed")

reader: Reader = Retry(FileReader("data.txt"), attempts=3)  # compose, don't inherit
```

### C. Repeating structure across union variants

```python
# BAD: every variant repeats the same members; nothing ties them together
from dataclasses import dataclass
from typing import Literal

@dataclass
class UserEntity:
    id: str
    name: str
    type: Literal["user"] = "user"

    def save(self) -> None: ...

@dataclass
class PostEntity:
    id: str
    title: str
    type: Literal["post"] = "post"

    def save(self) -> None: ...

def persist_user(e: UserEntity) -> None:
    e.save()

def persist_post(e: PostEntity) -> None:
    e.save()   # duplicated logic per variant
```

```python
# BETTER: extract the common structure into a Protocol; one function serves all variants
from dataclasses import dataclass
from typing import Literal, Protocol

class Saveable(Protocol):
    id: str
    def save(self) -> None: ...

@dataclass
class UserEntity:
    id: str
    name: str
    type: Literal["user"] = "user"

    def save(self) -> None: ...

@dataclass
class PostEntity:
    id: str
    title: str
    type: Literal["post"] = "post"

    def save(self) -> None: ...

type Entity = UserEntity | PostEntity   # keep the union for exhaustive matching

def persist(e: Saveable) -> None:
    e.save()

persist(UserEntity(id="1", name="Ann"))  # OK — structural match
```

### D. Using `Callable` when a Protocol is clearer

```python
from collections.abc import Callable
from typing import Protocol

# BAD: Callable loses attributes, less expressive
def run_callback(f: Callable[[str], int]) -> None:
    f("input")

# BETTER: a callable Protocol preserves the full contract including attributes
class Processor(Protocol):
    description: str
    def __call__(self, s: str) -> int: ...

def run_processor(f: Processor) -> None:
    print(f.description)  # attribute available
    f("input")
```

## Source anchors

- [PEP 3119 — Introducing Abstract Base Classes](https://peps.python.org/pep-3119/)
- [PEP 544 — Protocols: Structural subtyping (static duck typing)](https://peps.python.org/pep-0544/)
- [abc module — Abstract Base Classes](https://docs.python.org/3/library/abc.html)
- [typing — Protocol and runtime_checkable](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [mypy — Abstract base classes and Protocols](https://mypy.readthedocs.io/en/stable/protocols.html)
