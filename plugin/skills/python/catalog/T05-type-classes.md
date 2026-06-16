# Abstract Base Classes

> **Since:** Python 3.0 (PEP 3119) | **Typing integration:** Python 3.5+ (PEP 484)

## What it is

An Abstract Base Class (ABC) defines a nominal interface — a contract that subclasses must fulfill by implementing all declared abstract methods and properties. Unlike Protocols (which use structural subtyping), ABCs require explicit inheritance: a class must declare `class MyImpl(MyABC):` to be considered a subtype.

The `abc` module provides the `ABC` convenience base class and the `@abstractmethod` decorator. Marking a method as `@abstractmethod` means two things: (1) the class cannot be instantiated directly — attempting `MyABC()` raises `TypeError` at runtime, and (2) the type checker flags any concrete subclass that fails to implement the abstract method.

ABCs can also define concrete (non-abstract) methods that subclasses inherit, making them useful as partial implementations — unlike Protocols, which are purely structural contracts. The `collections.abc` module provides a rich library of pre-built ABCs (`Iterable`, `Mapping`, `Sequence`, etc.) that the type checker understands.

## What constraint it enforces

**Subclasses must implement all abstract methods and properties before they can be instantiated. The type checker rejects both direct instantiation of an ABC and subclasses with missing implementations.**

Specifically:

- A class with any unimplemented abstract methods cannot be instantiated — both the type checker and the runtime reject it.
- The type checker verifies that overriding methods have compatible signatures (parameter types, return type).
- `@abstractmethod` can be combined with `@property`, `@classmethod`, and `@staticmethod`.
- ABCMeta's `register()` can declare a "virtual subclass" that satisfies `isinstance()` at runtime but is *not* checked by the type checker for method completeness.

## Minimal snippet

```python
# expect-error
from abc import ABC, abstractmethod
from typing import override

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def perimeter(self) -> float: ...

class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self.radius = radius

    @override
    def area(self) -> float:
        return 3.14159 * self.radius ** 2

    @override
    def perimeter(self) -> float:
        return 2 * 3.14159 * self.radius

Shape()                     # error: Cannot instantiate abstract class "Shape"
Circle(5.0)                 # OK

class BadShape(Shape):
    @override
    def area(self) -> float:
        return 0.0
    # perimeter() is missing

BadShape()                  # error: Cannot instantiate abstract class "BadShape"
                            #   with abstract method "perimeter"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Protocol** [-> T07](T07-structural-typing.md) | Protocols check structure; ABCs check inheritance. A class can satisfy a Protocol *and* inherit from an ABC. Use Protocol when you want decoupling; use ABC when you want a shared implementation base. |
| **Generics / TypeVar** [-> T04](T04-generics-bounds.md) | ABCs can be generic: `class Repository(ABC, Generic[T])`. The TypeVar tracks the entity type across abstract methods. |
| **Dataclasses** [-> T06](T06-derivation.md) | A dataclass can inherit from an ABC and provide concrete implementations of abstract methods. The dataclass machinery generates `__init__` and friends; the ABC enforces the method contract. |
| **Final / ClassVar** [-> T32](T32-immutability-markers.md) | An ABC method can be `@final` to prevent further overriding in deeper subclasses. `ClassVar` attributes in an ABC are shared class-level state. |
| **Self type** [-> T33](T33-self-type.md) | Abstract methods returning `Self` ensure subclass methods return the correct subtype. |

## Gotchas and limitations

1. **`register()` bypasses type checking.** ABCMeta's `register()` makes a class a virtual subclass for `isinstance()` at runtime, but the type checker does not verify that the registered class implements the abstract methods.

    ```python
    from abc import ABC, abstractmethod

    class Printable(ABC):
        @abstractmethod
        def to_string(self) -> str: ...

    class Widget:
        pass                                # no to_string() method

    Printable.register(Widget)
    isinstance(Widget(), Printable)          # True at runtime
    # But type checker does NOT treat Widget as Printable
    ```

2. **`@property` + `@abstractmethod` decorator order matters.** The `@property` decorator must wrap `@abstractmethod` (i.e., `@property` on top):

    ```python
    # expect-error
    from abc import ABC, abstractmethod

    class Config(ABC):
        @property
        @abstractmethod
        def name(self) -> str: ...          # OK: @property wraps @abstractmethod

        @abstractmethod
        @property                           # error: wrong order
        def value(self) -> int: ...
    ```

3. **ABCs with all concrete methods can still be abstract.** An ABC subclass of another ABC inherits abstract methods. If it does not override them, it remains abstract even if it adds new concrete methods.

4. **No structural checking at all.** Unlike Protocol, an ABC does not accept classes that happen to have the right methods but do not inherit. This means you cannot pass an `io.BytesIO` where an ABC-based `ReadableStream` is expected unless `BytesIO` actually inherits from it.

5. **Multiple inheritance diamond with ABCs.** When multiple ABCs define the same abstract method, the concrete class must implement it once, but the MRO (Method Resolution Order) must be consistent. Conflicting MROs cause `TypeError` at class definition time.

6. **Abstract `__init__` is unusual.** While you *can* mark `__init__` as `@abstractmethod`, it is rarely useful — subclasses almost always define their own `__init__`, and the signatures typically differ.

## Beginner mental model

Think of an ABC as a contract with blanks. The ABC says "any subclass must fill in these blanks" — the blanks are the abstract methods. You cannot use the contract (instantiate the class) until all blanks are filled. The type checker enforces the contract at check time, and Python enforces it again at runtime when you try to call the constructor.

The key difference from Protocol is that ABC requires *signing the contract* (inheriting from the ABC). Protocol just checks whether you happen to have all the right methods, without caring whether you signed anything.

## Example A — Repository interface with required CRUD methods

```python
# expect-error
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, override

T = TypeVar("T")
ID = TypeVar("ID")

class Repository(ABC, Generic[T, ID]):
    """Abstract repository — subclasses must implement all CRUD operations."""

    @abstractmethod
    def get(self, id: ID) -> T | None: ...

    @abstractmethod
    def list_all(self) -> list[T]: ...

    @abstractmethod
    def save(self, entity: T) -> None: ...

    @abstractmethod
    def delete(self, id: ID) -> bool: ...

    # Concrete method — shared by all implementations
    def exists(self, id: ID) -> bool:
        return self.get(id) is not None

# Concrete implementation
class InMemoryUserRepo(Repository[dict[str, object], str]):
    def __init__(self) -> None:
        self._store: dict[str, dict[str, object]] = {}

    @override
    def get(self, id: str) -> dict[str, object] | None:
        return self._store.get(id)

    @override
    def list_all(self) -> list[dict[str, object]]:
        return list(self._store.values())

    @override
    def save(self, entity: dict[str, object]) -> None:
        self._store[str(entity["id"])] = entity

    @override
    def delete(self, id: str) -> bool:
        return self._store.pop(id, None) is not None

repo: Repository[dict[str, object], str] = InMemoryUserRepo()  # OK
repo.save({"id": "1", "name": "Alice"})                        # OK
repo.exists("1")                                                # OK — uses concrete method

# Incomplete implementation
class BrokenRepo(Repository[str, int]):
    @override
    def get(self, id: int) -> str | None:
        return None
    # list_all, save, delete are missing

BrokenRepo()                # error: Cannot instantiate abstract class "BrokenRepo"
                            #   with abstract methods "delete", "list_all", "save"
```

## Example B — Abstract property enforcing subclass provides configuration

```python
# expect-error
from abc import ABC, abstractmethod
from typing import ClassVar, override

class BaseService(ABC):
    """Services must declare their name and timeout via abstract properties."""

    max_instances: ClassVar[int] = 10           # shared, not abstract

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Each subclass must provide its service name."""
        ...

    @property
    @abstractmethod
    def timeout_seconds(self) -> float:
        """Each subclass must declare its timeout."""
        ...

    def describe(self) -> str:
        return f"{self.service_name} (timeout={self.timeout_seconds}s)"

class AuthService(BaseService):
    @property
    @override
    def service_name(self) -> str:
        return "auth"

    @property
    @override
    def timeout_seconds(self) -> float:
        return 5.0

class IncompleteService(BaseService):
    @property
    @override
    def service_name(self) -> str:
        return "incomplete"
    # timeout_seconds is missing

AuthService()                # OK
AuthService().describe()     # OK — returns "auth (timeout=5.0s)"
IncompleteService()          # error: Cannot instantiate abstract class
                             #   "IncompleteService" with abstract method "timeout_seconds"

# Abstract classmethod
class Deserializable(ABC):
    @classmethod
    @abstractmethod
    def from_json(cls, data: str) -> "Deserializable": ...

class User(Deserializable):
    def __init__(self, name: str) -> None:
        self.name = name

    @classmethod
    @override
    def from_json(cls, data: str) -> "User":
        import json
        return cls(json.loads(data)["name"])

User.from_json('{"name": "Alice"}')             # OK
Deserializable.from_json('{}')                   # error: Method "from_json" cannot be called because it is abstract and unimplemented
```

Note the checker divergence on the last line: pyright flags calling an abstract classmethod on the ABC itself (`reportAbstractUsage`), but mypy is silent — the call only fails at runtime if the body is `...`/`raise NotImplementedError`.

## Common type-checker errors and how to read them

### mypy: `Cannot instantiate abstract class "X" with abstract method "Y"`

Trying to create an instance of a class that has unimplemented abstract methods.

```text
error: Cannot instantiate abstract class "BadShape" with abstract method "perimeter"
```

**Fix:** Implement all abstract methods listed in the error, or if the class is meant to be abstract itself, do not instantiate it directly.

### pyright: `"X" cannot be instantiated — it is abstract`

Pyright's equivalent message, sometimes with a list of missing methods.

```text
error: Cannot instantiate abstract class "BrokenRepo"
  "BrokenRepo" is abstract because it does not implement "list_all", "save", "delete"
```

**Fix:** Same — implement the listed methods.

### mypy: `Return type "X" of "method" incompatible with return type "Y" in supertype "ABC"`

The overriding method's return type is not compatible with the abstract method's declared return type.

```text
error: Return type "str" of "area" incompatible with return type "float"
       in supertype "Shape"
```

**Fix:** Ensure the override's return type is the same or a subtype of the abstract method's return type.

### mypy: `Signature of "method" incompatible with supertype "ABC"`

The overriding method changes the parameter types in an incompatible way.

```text
error: Signature of "get" incompatible with supertype "Repository"
  Superclass:   def get(self, id: ID) -> T | None
  Subclass:     def get(self, id: str, default: str = ...) -> str
```

**Fix:** Keep parameter types the same or widen them (contravariance for parameters).

## When to Use ABCs

Use ABCs when you need **explicit contracts with enforced inheritance**:

- **You want runtime enforcement**: ABCs prevent instantiation of incomplete implementations at runtime, not just type-check time.

  ```python
  # expect-error
  from abc import ABC, abstractmethod
  from typing import override

  class PaymentProcessor(ABC):
      @abstractmethod
      def charge(self, amount: float) -> bool: ...

  class StripeProcessor(PaymentProcessor):
      @override
      def charge(self, amount: float) -> bool:
          return True

  # Missing implementation catches at both check and runtime
  class BadProcessor(PaymentProcessor):
      pass

  BadProcessor()  # TypeError: Can't instantiate abstract class
  ```

- **Security-boundary enforcement**: Prevent untrusted code from satisfying your interface accidentally.

  ```python
  # expect-error
  from abc import ABC, abstractmethod

  class CryptoSigner(ABC):
      @abstractmethod
      def sign(self, data: bytes) -> bytes: ...

  def use_signer(signer: CryptoSigner) -> bytes:
      return signer.sign(b"test")

  # Even this won't work without inheritance:
  malicious = {"sign": lambda d: d}
  use_signer(malicious)  # Type error: requires CryptoSigner subclass
  ```

- **Defining library APIs with clear contracts**: Third-party implementers must explicitly opt-in by inheriting from your ABC.

---

## When NOT to Use ABCs

Avoid ABCs when:

- **You want structural matching**: Any object with the right methods should work.

  ```python
  # Bad: forces inheritance for simple callbacks
  from abc import ABC, abstractmethod

  class ABCFileReader(ABC):
      @abstractmethod
      def read(self) -> str: ...

  # Good: Protocol accepts any object with .read()
  from typing import Protocol

  class FileReader(Protocol):
      def read(self) -> str: ...

  def process(reader: FileReader) -> str:
      return reader.read()

  from io import StringIO

  process(open("file.txt"))        # OK with Protocol
  process(StringIO("text"))       # OK with Protocol
  ```

- **You only need a mixin with utility methods and no abstract requirements.**

  ```python
  # Bad: why use ABC at all?
  from abc import ABC

  class UsefulMixinABC(ABC):
      def helper(self) -> str:
          return "help"

      def another(self) -> int:
          return 42

  # Better: plain old class
  class UsefulMixin:
      def helper(self) -> str:
          return "help"

      def another(self) -> int:
          return 42
  ```

- **You need interface segregation**: One big ABC with 20 methods is a smell.

  ```python
  # Bad: monolithic ABC
  from abc import ABC, abstractmethod
  from typing import override

  class Service(ABC):
      @abstractmethod
      def start(self) -> None: ...
      @abstractmethod
      def stop(self) -> None: ...
      @abstractmethod
      def status(self) -> str: ...
      @abstractmethod
      def config(self) -> dict[str, str]: ...
      @abstractmethod
      def logging(self) -> None: ...
      # ... 15 more methods

  # A read-only service now must implement write methods it can't support
  class ReadOnlyService(Service):
      @override
      def start(self) -> None: ...
      @override
      def stop(self) -> None: ...
      # ... must stub out 20 methods
  ```

  **Better**: Split into focused ABCs.

  ```python
  from abc import ABC, abstractmethod
  from typing import Any, override

  class Startable(ABC):
      @abstractmethod
      def start(self) -> None: ...

      @abstractmethod
      def stop(self) -> None: ...

  class Configurable(ABC):
      @abstractmethod
      def config(self) -> dict[str, Any]: ...

  # Compose only what's needed
  class ReadOnlyService(Startable):
      @override
      def start(self) -> None: ...
      @override
      def stop(self) -> None: ...
  ```

- **You rely on `register()` for runtime flexibility.**

  ```python
  # Bad: virtual subclass that doesn't actually implement interface
  from abc import ABC, abstractmethod

  class Printable(ABC):
      @abstractmethod
      def as_string(self) -> str: ...

  class Data:
      pass  # no as_string method!

  Printable.register(Data)
  isinstance(Data(), Printable)  # True at runtime

  def process_printable(p: Printable) -> str:
      return p.as_string()

  process_printable(Data())  # error: "Data" is not assignable to "Printable" — correctly rejected
  ```

- **You need flexible constructors across subclasses.**

  ```python
  # Bad: abstract __init__ forces same signature
  from abc import ABC, abstractmethod

  class Entity(ABC):
      def __init__(self, id: int, name: str) -> None:
          self.id = id
          self.name = name

  # Good: let subclasses define their own constructors
  class EntityBase(ABC):
      @abstractmethod
      def get_id(self) -> int: ...

      @abstractmethod
      def get_name(self) -> str: ...
  ```

- **You're building a library where users prefer duck typing.**

  ```python
  # Bad: requires inheritance for simple iteration
  from abc import ABC, abstractmethod
  from collections.abc import Iterator
  from typing import Protocol

  class Item: ...

  class ItemIterableBad(ABC):
      @abstractmethod
      def __iter__(self) -> Iterator[Item]: ...

  def process_items_bad(container: ItemIterableBad) -> list[Item]:
      return list(container)

  # Now can't pass list, tuple, custom iterators...
  process_items_bad([Item()])  # error: "list[Item]" is not assignable to "ItemIterableBad"

  # Good: Protocol accepts any iterable
  class ItemIterableGood(Protocol):
      def __iter__(self) -> Iterator[Item]: ...

  def process_items_good(container: ItemIterableGood) -> list[Item]:
      return list(container)

  process_items_good([Item()])  # OK!
  ```

---

## Antipatterns

### Antipattern A: Duck typing without any contract

No type annotations, no enforcement — errors only surface at runtime.

```python
# Bad: no contract — what if .read() is missing, or takes arguments?
from abc import ABC, abstractmethod

def process_reader(reader):  # error: Type annotation is missing for parameter "reader"
    return reader.read().strip()  # error: Type of "read" is unknown

# ABC enforces the contract
class Reader(ABC):
    @abstractmethod
    def read(self) -> str: ...

def process_reader_typed(reader: Reader) -> str:
    return reader.read().strip()  # Compile-time safety
```

### Antipattern B: isinstance chains instead of polymorphism

Using type checks instead of a shared interface.

```python
from abc import ABC, abstractmethod

class File:
    def read(self) -> bytes: ...

class Socket:
    def recv(self) -> bytes: ...

class String:
    def decode(self) -> bytes: ...

# Bad: if-else chain with type checks
def handle(obj: File | Socket | String) -> bytes:
    if isinstance(obj, File):
        return obj.read()
    elif isinstance(obj, Socket):
        return obj.recv()
    else:
        return obj.decode()

# Good: ABC with single interface
class Source(ABC):
    @abstractmethod
    def read(self) -> bytes: ...

def handle_typed(source: Source) -> bytes:
    return source.read()  # Polymorphism, no isinstance needed
```

### Antipattern C: Passing `None` as "not implemented"

Using sentinel values or `None` instead of enforcing implementation.

```python
from abc import ABC, abstractmethod

# Bad: optional abstract method that returns None
class BadWidget:
    def customize(self) -> str | None:
        return None  # Base impl returns None

class MyWidget(BadWidget):
    pass  # Inherits None behavior — is this intentional?

def handle_unsupported() -> None: ...

result = MyWidget().customize()  # runtime surprise
if result is None:
    handle_unsupported()

# Good: ABC with abstract method
class Widget(ABC):
    @abstractmethod
    def customize(self) -> str: ...  # Must be implemented
```

### Antipattern D: Base class with "do not use directly" comment

Relying on documentation instead of enforcement.

```python
from abc import ABC, abstractmethod

# Bad: documented but not enforced
class BaseHandler:
    """Do not instantiate directly — subclass and implement methods."""
    def handle(self) -> str:
        raise NotImplementedError("subclasses must implement")

handler = BaseHandler()   # no static error
handler.handle()          # NotImplementedError at runtime only

# Good: ABC prevents instantiation, statically and at runtime
class AbstractHandler(ABC):
    @abstractmethod
    def handle(self) -> str: ...

handler2 = AbstractHandler()  # error: Cannot instantiate abstract class "AbstractHandler"
```

### Antipattern E: Partial implementation without awareness

Subclassing but not realizing some method is required.

```python
from abc import ABC, abstractmethod
from typing import override

# Bad: no way to know what's required
class PluginBase:
    def initialize(self) -> None:
        pass  # default no-op

    def run(self, data: str) -> str:
        return data  # default passthrough

class MyPluginBase(PluginBase):
    # Forgot to override .initialize()
    @override
    def run(self, data: str) -> str:
        return data.upper()

MyPluginBase().run("test")  # Runs, but init not called!

# Good: ABC shows what's required
class Plugin(ABC):
    @abstractmethod
    def initialize(self) -> None: ...
    @abstractmethod
    def run(self, data: str) -> str: ...

class MyPlugin(Plugin):
    @override
    def initialize(self) -> None:
        ...
    @override
    def run(self, data: str) -> str:
        return data.upper()

MyPlugin()  # OK — implements all abstract methods
```

### Antipattern F: Interface segregation failure with union types

Using union types for separate concepts that should be distinct.

```python
# Bad: union of unrelated functionality
from abc import ABC, abstractmethod

class Reader(ABC):
    @abstractmethod
    def read(self) -> str: ...

class Writer(ABC):
    @abstractmethod
    def write(self, data: str) -> None: ...

def process_io(io: Reader | Writer) -> None:
    # Need isinstance checks inside
    if isinstance(io, Reader):
        io.read()
    if isinstance(io, Writer):
        io.write("data")

# Good: separate ABCs, separate functions
def read_data(reader: Reader) -> str:
    return reader.read()

def write_data(writer: Writer, data: str) -> None:
    writer.write(data)

# Or compose with intersection
from typing import Protocol

class ReadWrite(Protocol):
    def read(self) -> str: ...
    def write(self, data: str) -> None: ...

def copy_all(src: ReadWrite, dst: ReadWrite) -> None:
    dst.write(src.read())  # Both have both methods
```

## Source anchors

- [PEP 3119 — Introducing Abstract Base Classes](https://peps.python.org/pep-3119/)
- [`abc` module docs](https://docs.python.org/3/library/abc.html)
- [`collections.abc` module docs](https://docs.python.org/3/library/collections.abc.html)
- [typing spec: Abstract methods](https://typing.readthedocs.io/en/latest/spec/class-compat.html)
- [mypy docs: Abstract base classes](https://mypy.readthedocs.io/en/stable/class_basics.html#abstract-base-classes-and-multiple-inheritance)
