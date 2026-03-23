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
from typing import Protocol

# Nominal approach: ABC
class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

class Circle(Shape):
    def __init__(self, r: float) -> None:
        self.r = r
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
| **ABC** [-> catalog/T05](T05-type-classes.md) | ABCs define nominal interfaces with `@abstractmethod`. They are the traditional approach to trait-like polymorphism in Python. |
| **Protocol** [-> catalog/T07](T07-structural-typing.md) | Protocols define structural interfaces. They serve the same dispatch role as ABCs but without requiring inheritance — closer to Go's implicit interfaces or Rust's duck-typed traits. |
| **Type narrowing** [-> catalog/T14](T14-type-narrowing.md) | `isinstance(obj, Shape)` narrows `Shape | str` to `Shape`. For `@runtime_checkable` Protocols, `isinstance(obj, HasArea)` narrows at runtime (checking method existence only). |
| **Generics** [-> catalog/T04](T04-generics-bounds.md) | `TypeVar("T", bound=HasArea)` creates a generic function that accepts any type satisfying the interface while preserving the concrete type in the return. |
| **Callable types** [-> catalog/T22](T22-callable-typing.md) | A Protocol with `__call__` serves as a typed function trait — more precise than `Callable[...]` because it can include attributes alongside the call signature. |

## Gotchas and limitations

1. **ABCs require inheritance; Protocols do not.** This is the fundamental trade-off. ABCs give clearer error messages when a subclass forgets to implement a method (error at class definition time). Protocols give errors only at call sites where the incomplete type is used.

2. **`@runtime_checkable` Protocol checks are shallow.** `isinstance(obj, MyProtocol)` only verifies that the required method *names* exist as attributes. It does not check parameter types, return types, or even that the attribute is callable.

   ```python
   from typing import Protocol, runtime_checkable

   @runtime_checkable
   class Processor(Protocol):
       def process(self, data: bytes) -> str: ...

   class Fake:
       process = 42   # attribute, not a method!

   isinstance(Fake(), Processor)   # True! — 'process' attribute exists
   ```

3. **ABC + Protocol mix is possible but rarely needed.** A class can satisfy a Protocol *and* inherit from an ABC. These are checked independently — the ABC checks at class creation, the Protocol checks at usage sites. Combining them adds complexity without clear benefit in most cases.

4. **No multi-dispatch on trait objects.** Python's method resolution is single-dispatch by default. For multi-method dispatch on multiple trait parameters, use `functools.singledispatch` or a library like `multipledispatch`. The type checker has limited support for `singledispatch` (pyright supports it; mypy support is partial).

5. **Performance of Protocol isinstance checks.** `@runtime_checkable` Protocol `isinstance` checks inspect the class's MRO for each required member on every call. For hot paths, prefer `isinstance` against an ABC (which uses `__subclasshook__` caching) or precomputed type checks.

6. **Abstract properties require careful syntax.** Combining `@abstractmethod` with `@property` requires the decorators in the correct order:

   ```python
   class Labeled(ABC):
       @property
       @abstractmethod
       def label(self) -> str: ...   # correct order
   ```

## Beginner mental model

Think of an **ABC** as a job description posted by a company — you must formally apply (inherit) and prove you have every listed qualification (implement abstract methods). A **Protocol** is like a freelance marketplace: anyone who can demonstrably do the work (has the right methods) gets the contract, no formal application needed. Both result in the same thing — someone doing the job at runtime — but the hiring process differs. `isinstance` is the background check: thorough for ABC hires (checks the entire inheritance chain), but only a quick resume scan for Protocol freelancers (checks method names exist).

## Example A — Plugin system with ABC dispatch

```python
from abc import ABC, abstractmethod

class Exporter(ABC):
    @abstractmethod
    def export(self, data: dict[str, object]) -> bytes: ...

    @abstractmethod
    def content_type(self) -> str: ...

class JsonExporter(Exporter):
    def export(self, data: dict[str, object]) -> bytes:
        import json
        return json.dumps(data).encode()

    def content_type(self) -> str:
        return "application/json"

class CsvExporter(Exporter):
    def export(self, data: dict[str, object]) -> bytes:
        header = ",".join(data.keys())
        values = ",".join(str(v) for v in data.values())
        return f"{header}\n{values}".encode()

    def content_type(self) -> str:
        return "text/csv"

def send_report(exporter: Exporter, data: dict[str, object]) -> None:
    payload = exporter.export(data)
    print(f"Sending {len(payload)} bytes as {exporter.content_type()}")

send_report(JsonExporter(), {"name": "Alice", "score": 95})   # OK
send_report(CsvExporter(), {"name": "Alice", "score": 95})    # OK
send_report("not an exporter", {})                              # error
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

- [-> UC-05](../usecases/UC05-structural-contracts.md) — Protocols define structural contracts for plug-in architectures without coupling to specific classes.
- [-> UC-04](../usecases/UC04-generic-constraints.md) — TypeVars bounded by ABC or Protocol enable generic algorithms over trait-like interfaces.
- [-> UC-07](../usecases/UC07-callable-contracts.md) — Callable Protocols combine runtime dispatch with precise signature typing.

## Source anchors

- [PEP 3119 — Introducing Abstract Base Classes](https://peps.python.org/pep-3119/)
- [PEP 544 — Protocols: Structural subtyping (static duck typing)](https://peps.python.org/pep-0544/)
- [abc module — Abstract Base Classes](https://docs.python.org/3/library/abc.html)
- [typing — Protocol and runtime_checkable](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [mypy — Abstract base classes and Protocols](https://mypy.readthedocs.io/en/stable/protocols.html)
