# Associated Types (via Protocol Members and ClassVar)

> **Since:** `Protocol` Python 3.8 (PEP 544); `ClassVar` Python 3.5.3 (PEP 526); `Generic` Python 3.5 (PEP 484) | **Backport:** `typing_extensions`

## What it is

In Rust, associated types let a trait define a type member that each implementation fills in (`type Output;`), avoiding extra generic parameters on the trait itself. Python has no direct associated-type syntax, but the pattern can be **approximated** using three techniques:

1. **Protocol with class-level type annotations.** A Protocol declares an attribute (e.g., `element_type: type[T]`) that each implementing class fills with a concrete type. This is closest to Rust's associated types but requires a runtime attribute.

2. **ClassVar members that vary by implementation.** `ClassVar[type[X]]` declares a class-level attribute that the type checker tracks per subclass. Each subclass sets it to a different concrete type.

3. **Generic Protocols with "output" type parameters.** A `Protocol[Input, Output]` where `Output` is determined by the implementation — the caller specifies `Input` and the implementation fixes `Output`. This uses extra generic parameters rather than true associated types, but achieves the same effect.

The key insight is that Python's type system ties associated outputs to a *generic parameter* rather than to the implementing class itself. This is more verbose than Rust's `type Output = Foo` but structurally equivalent for most use cases.

## What constraint it enforces

**Protocol members and generic output parameters let each implementation define its own output type. The type checker tracks these per-class types and ensures callers handle the correct concrete output type for each implementation.**

## Minimal snippet

```python
from typing import Protocol, TypeVar, Generic

T = TypeVar("T")

class Parser(Protocol[T]):
    """Protocol with an 'associated' output type T."""
    def parse(self, raw: str) -> T: ...

class IntParser:
    def parse(self, raw: str) -> int:
        return int(raw)

class FloatParser:
    def parse(self, raw: str) -> float:
        return float(raw)

def run_parser(parser: Parser[T], data: str) -> T:
    return parser.parse(data)

x: int = run_parser(IntParser(), "42")       # OK — T inferred as int
y: float = run_parser(FloatParser(), "3.14") # OK — T inferred as float
z: str = run_parser(IntParser(), "42")       # error: int is not str
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **ABC** [-> catalog/T05](T05-type-classes.md) | ABCs can define abstract methods with concrete return types in subclasses. Combined with `Generic`, this achieves associated-type-like patterns through nominal inheritance. |
| **Protocol** [-> catalog/T07](T07-structural-typing.md) | Protocols are the primary vehicle for associated types in Python. A `Protocol[T]` where `T` is the "output" type lets each implementation fix `T` to a concrete type. |
| **Generics / TypeVar** [-> catalog/T04](T04-generics-bounds.md) | Generic type parameters serve as the mechanism for associated outputs. Unlike Rust (where the associated type is inside the trait), Python makes it an explicit generic parameter. |
| **ClassVar** [-> catalog/T32](T32-immutability-markers.md) | `ClassVar[type[X]]` can hold a class-level type reference that varies per subclass, approximating a type-level associated member. |
| **Callable types** [-> catalog/T22](T22-callable-typing.md) | A factory Protocol `class Factory(Protocol[T]): def create(self) -> T: ...` uses the associated-type pattern for typed factory methods. |

## Gotchas and limitations

1. **Extra generic parameters instead of named associated types.** Python requires you to thread the output type as a generic parameter (`Protocol[Input, Output]`), which adds verbosity compared to Rust's `type Output = Foo` inside the impl block.

2. **ClassVar type members are not checked structurally.** If you use `ClassVar[type[int]]` in a Protocol, the checker verifies the attribute exists but may not use it to constrain method return types. You typically need a generic parameter for the checker to track the relationship.

3. **No "type projection" syntax.** You cannot write `Parser.Output` to refer to an implementation's associated type. You must use the generic parameter (`T` in `Parser[T]`) or extract it via `type()` / `TypeVar` inference.

4. **Generic Protocol variance matters.** If your associated output type appears only in return positions, it should be covariant (`TypeVar("T", covariant=True)`). Getting variance wrong causes confusing "incompatible type" errors.

   ```python
   from typing import TypeVar, Protocol

   T_co = TypeVar("T_co", covariant=True)

   class Producer(Protocol[T_co]):
       def produce(self) -> T_co: ...

   # A Producer[int] is assignable to Producer[object] (covariant)
   ```

5. **Runtime access to the associated type requires explicit attributes.** Unlike Rust where `<T as Trait>::Output` is a compile-time construct, Python code that needs the output type at runtime must store it explicitly (e.g., as a `ClassVar`).

6. **Type inference has limits with complex associated-type patterns.** When multiple generic parameters interact, checkers may require explicit type annotations at call sites to resolve ambiguity.

## Beginner mental model

Think of a Protocol with a generic parameter as a **form template** with a blank field. The template says "parser that produces ___". Each concrete class fills in the blank: `IntParser` fills in "int", `FloatParser` fills in "float". When you write a function accepting `Parser[T]`, you are saying "give me any filled-in form, and I will work with whatever type is in the blank." The type checker reads the filled-in blank and ensures you use the result correctly — if the parser produces `int`, you cannot treat the output as `str`.

## Example A — Repository pattern with associated entity type

```python
from typing import Protocol, TypeVar, Generic, ClassVar

T = TypeVar("T")

class Entity(Protocol):
    id: int

class User:
    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name

class Product:
    def __init__(self, id: int, title: str, price: float) -> None:
        self.id = id
        self.title = title
        self.price = price

class Repository(Protocol[T]):
    """Repository with associated entity type T."""
    def get(self, id: int) -> T | None: ...
    def save(self, entity: T) -> None: ...
    def all(self) -> list[T]: ...

class UserRepo:
    _store: dict[int, User] = {}

    def get(self, id: int) -> User | None:
        return self._store.get(id)

    def save(self, entity: User) -> None:
        self._store[entity.id] = entity

    def all(self) -> list[User]:
        return list(self._store.values())

class ProductRepo:
    _store: dict[int, Product] = {}

    def get(self, id: int) -> Product | None:
        return self._store.get(id)

    def save(self, entity: Product) -> None:
        self._store[entity.id] = entity

    def all(self) -> list[Product]:
        return list(self._store.values())

def count_all(repo: Repository[T]) -> int:
    return len(repo.all())

count_all(UserRepo())      # OK — T inferred as User
count_all(ProductRepo())   # OK — T inferred as Product
```

## Example B — Serializer with associated output format

```python
from typing import Protocol, TypeVar

T_co = TypeVar("T_co", covariant=True)

class Serializer(Protocol[T_co]):
    """Each implementation fixes the output type."""
    def serialize(self, data: dict[str, object]) -> T_co: ...

class JsonSerializer:
    def serialize(self, data: dict[str, object]) -> str:
        import json
        return json.dumps(data)

class BinarySerializer:
    def serialize(self, data: dict[str, object]) -> bytes:
        import json
        return json.dumps(data).encode("utf-8")

def write_output(serializer: Serializer[T_co], data: dict[str, object]) -> T_co:
    return serializer.serialize(data)

result_str: str = write_output(JsonSerializer(), {"key": "value"})     # OK
result_bytes: bytes = write_output(BinarySerializer(), {"key": "value"})  # OK
bad: bytes = write_output(JsonSerializer(), {"key": "value"})           # error: str != bytes
```

## When to Use Associated Types

**Use generic Protocol interfaces (implementor fixes type) when:**

1. **You have a contract with a per-implementation type**: Each implementation should commit to one concrete type.

```python
from typing import Protocol, TypeVar

T = TypeVar("T")

class Handler(Protocol[T]):
    def handle(self, input: T) -> T: ...

class UpperHandler:
    def handle(self, input: str) -> str:
        return input.upper()

# T is fixed as str — clean separation
```

2. **You need type-safe generic combinators**: Functions that compose implementations should preserve the associated type.

```python
def compose_handler(handler: Handler[T]) -> Handler[T]:
    def wrapped(x: T) -> T:
        return handler.handle(x)
    return wrapped
```

3. **You model domain entities**: Repository, Service, Codec patterns where the entity type defines the implementation.

**Use ClassVar type members when:**

1. **You need runtime access to the associated type**: Storing `element_type: type[T]` allows runtime introspection.

```python
from typing import ClassVar, type

class Container(Protocol[T]):
    element_type: ClassVar[type[T]]

class IntContainer:
    element_type: ClassVar[type[int]] = int
```

2. **You build factory patterns that need type dispatch**: Factories can use the class-level type to construct instances.

## When NOT to Use Associated Types

**Avoid generic Protocols when:**

1. **A single class needs multiple type associations**: Prefer separate protocols or use dataclasses with multiple fields.

```python
# Bad: trying to encode multiple associated types in one Protocol
class Transform(Protocol[T, U]):
    def transform(self, t: T) -> U: ...

# Prefer separate roles
class Source(Protocol[T]):
    def next(self) -> T: ...

class Sink(Protocol[T]):
    def write(self, t: T) -> None: ...
```

2. **The "associated" type varies per call, not per implementation**: Use regular generic method parameters or function overloads.

```python
# Bad: entity type varies per call
class Cache(Protocol[T]):
    def get(self) -> T: ...

class MultiCache:
    def get(self) -> int: return 1
    def get(self) -> str: return "a"  # type error!

# Prefer: generic method
class Cache:
    def get(self, default: T) -> T:
        return default
```

3. **You need runtime polymorphism across different types**: Use union types or object tags instead.

```python
from typing import Any

class PolymorphicBox:
    # Not ideal for associated types
    def get(self) -> Any:  # loses type safety
        ...
```

**Avoid ClassVar type members when:**

1. **Type checkers cannot use the ClassVar to constrain return types**: The annotation won't flow to method signatures.

```python
# Problem: ClassVar doesn't constrain return type
class BadContainer(Protocol):
    element_type: ClassVar[type[int]]
    def get(self) -> int: ...  # must hardcode return type
```

2. **You're building abstract interfaces without runtime needs**: Generic parameters are cleaner for pure type checking.

## Antipatterns When Using Associated Types

**Antipattern 1: Overly broad generic constraints**

```python
from typing import Any

# Bad: T can be anything, weakening type safety
class Box(Protocol[T]):
    value: T

class AnyBox:
    value: Any = {}  # type safety lost

# Prefer: constrain T meaningfully
class IdMixin:
    id: int

class Box(Protocol[T]):
    value: T  # T should have constraints in real code
```

**Antipattern 2: Leaking implementation details in type members**

```python
from typing import ClassVar, type

# Bad: exposes internal storage type
class StringContainer(Protocol[T]):
    storage_type: ClassVar[type[list]]  # leaks implementation

class MyContainer:
    storage_type: ClassVar[type[list]] = list  # should be private
```

**Antipattern 3: Using Protocol type parameters for unrelated concerns**

```python
from typing import TypeVar, Protocol

# Bad: mixing input and output in one parameter
T = TypeVar("T")

class Transformer(Protocol[T]):
    def transform(self, t: T) -> T: ...
    def log(self, msg: str) -> None: ...  # unrelated to T

# Prefer: separate concerns
class Transformable(Protocol[T]):
    def transform(self, t: T) -> T: ...

class Loggable:
    def log(self, msg: str) -> None: ...
```

**Antipattern 4: Nested generic types create hard-to-read signatures**

```python
from typing import TypeVar, Protocol, Generic

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")

# Bad: hard to understand the relationship
class TripleMapper(Protocol[T, U, V]):
    def map(self, t: T) -> tuple[U, V]: ...

# Prefer: decompose
class Mapper(Protocol[T, U]):
    def map(self, t: T) -> U: ...

class Pair:
    def __init__(self, u: type, v: type):
        self.u = u
        self.v = v
```

## Antipatterns Solved by Associated Types

**Pattern 1: Duplicated return types**

```python
# Bad: duplicated return type
class JsonEncoder:
    def encode(self, obj: dict) -> str:
        import json
        return json.dumps(obj)

def encode_and_log(obj: dict) -> str:
    encoder = JsonEncoder()
    result = encoder.encode(obj)  # must know return type is str
    return result

# Good: inference handles it
T = TypeVar("T")

class Encoder(Protocol[T]):
    def encode(self, obj: dict) -> T: ...

class JsonEncoder:
    def encode(self, obj: dict) -> str:
        import json
        return json.dumps(obj)

def encode_and_log(encoder: Encoder[T], obj: dict) -> T:
    result = encoder.encode(obj)  # T inferred as str
    return result
```

**Pattern 2: Manual type repetition in generic functions**

```python
# Bad: must repeat the return type
def parse_twice(parser: Parser[T], data1: str, data2: str) -> tuple[T, T]:
    return (parser.parse(data1), parser.parse(data2))

# Without associated types, you'd write:
def parse_twice_int(data1: str, data2: str) -> tuple[int, int]:
    ...

def parse_twice_float(data1: str, data2: str) -> tuple[float, float]:
    ...

# Good: generic function with associated type
def parse_twice(parser: Parser[T], data1: str, data2: str) -> tuple[T, T]:
    return (parser.parse(data1), parser.parse(data2))
```

**Pattern 3: Uncoupled producer-consumer types**

```python
# Bad: disconnected types
class Producer:
    def produce(self) -> str:
        return "hello"

class Consumer:
    def consume(self, x: str) -> None:  # what if Producer changes?
        ...

# Types can drift apart

# Good: coupled via associated type
T = TypeVar("T")

class Pipeline(Protocol[T]):
    def produce(self) -> T: ...
    def consume(self, x: T) -> None: ...

class StringPipeline:
    def produce(self) -> str:
        return "hello"
    def consume(self, x: str) -> None:
        print(x)
```

**Pattern 4: Type assertions in generic code**

```python
from typing import cast

# Bad: requires type assertions
def first_element(items: list) -> object:
    if items:
        return cast(object, items[0])  # assertion needed

# Good: inference handles it
T = TypeVar("T")

def first_element(items: list[T]) -> T | None:
    return items[0] if items else None
```

## Example C — Factory with associated type

```python
from typing import Protocol, TypeVar

T = TypeVar("T")

class Factory(Protocol[T]):
    """Each implementation fixes the output type T."""
    def create(self) -> T: ...

class UserFactory:
    def create(self) -> dict:
        return {"type": "user", "name": "Alice"}

class ProductFactory:
    def create(self) -> dict:
        return {"type": "product", "sku": "12345"}

def initialize(factory: Factory[T]) -> T:
    return factory.create()

user = initialize(UserFactory())      # T inferred as dict
product = initialize(ProductFactory()) # T inferred as dict
```

## Use-case cross-references

- [-> UC-04](../usecases/UC04-generic-constraints.md) — Generic Protocols with output type parameters encode per-implementation type constraints.
- [-> UC-05](../usecases/UC05-structural-contracts.md) — Structural contracts where each implementation determines its own output type.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Repository and serializer patterns where the entity/output type is associated with the implementation.

## Source anchors

- [PEP 544 — Protocols: Structural subtyping (static duck typing)](https://peps.python.org/pep-0544/)
- [PEP 526 — Syntax for Variable Annotations (ClassVar)](https://peps.python.org/pep-0526/)
- [typing — Protocol and Generic](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [mypy — Generic Protocols](https://mypy.readthedocs.io/en/stable/protocols.html#generic-protocols)
- [typing spec — Variance](https://typing.readthedocs.io/en/latest/spec/generics.html#variance)
