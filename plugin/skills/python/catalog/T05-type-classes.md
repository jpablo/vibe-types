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
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def perimeter(self) -> float: ...

class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return 3.14159 * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * 3.14159 * self.radius

Shape()                     # error: Cannot instantiate abstract class "Shape"
Circle(5.0)                 # OK

class BadShape(Shape):
    def area(self) -> float:
        return 0.0
    # perimeter() is missing

BadShape()                  # error: Cannot instantiate abstract class "BadShape"
                            #   with abstract method "perimeter"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Protocol** [-> catalog/09](T07-structural-typing.md) | Protocols check structure; ABCs check inheritance. A class can satisfy a Protocol *and* inherit from an ABC. Use Protocol when you want decoupling; use ABC when you want a shared implementation base. |
| **Generics / TypeVar** [-> catalog/07](T04-generics-bounds.md) | ABCs can be generic: `class Repository(ABC, Generic[T])`. The TypeVar tracks the entity type across abstract methods. |
| **Dataclasses** [-> catalog/06](T06-derivation.md) | A dataclass can inherit from an ABC and provide concrete implementations of abstract methods. The dataclass machinery generates `__init__` and friends; the ABC enforces the method contract. |
| **Final / ClassVar** [-> catalog/12](T32-immutability-markers.md) | An ABC method can be `@final` to prevent further overriding in deeper subclasses. `ClassVar` attributes in an ABC are shared class-level state. |
| **Self type** [-> catalog/16](T33-self-type.md) | Abstract methods returning `Self` ensure subclass methods return the correct subtype. |

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

2. **`@abstractmethod` must be the innermost decorator.** When combining with `@property`, `@classmethod`, or `@staticmethod`, `@abstractmethod` must come last (closest to the `def`).

   ```python
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
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

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

    def get(self, id: str) -> dict[str, object] | None:
        return self._store.get(id)

    def list_all(self) -> list[dict[str, object]]:
        return list(self._store.values())

    def save(self, entity: dict[str, object]) -> None:
        self._store[str(entity["id"])] = entity

    def delete(self, id: str) -> bool:
        return self._store.pop(id, None) is not None

repo: Repository[dict[str, object], str] = InMemoryUserRepo()  # OK
repo.save({"id": "1", "name": "Alice"})                        # OK
repo.exists("1")                                                # OK — uses concrete method

# Incomplete implementation
class BrokenRepo(Repository[str, int]):
    def get(self, id: int) -> str | None:
        return None
    # list_all, save, delete are missing

BrokenRepo()                # error: Cannot instantiate abstract class "BrokenRepo"
                            #   with abstract methods "delete", "list_all", "save"
```

## Example B — Abstract property enforcing subclass provides configuration

```python
from abc import ABC, abstractmethod
from typing import ClassVar

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
    def service_name(self) -> str:
        return "auth"

    @property
    def timeout_seconds(self) -> float:
        return 5.0

class IncompleteService(BaseService):
    @property
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
    def from_json(cls, data: str) -> "User":
        import json
        return cls(json.loads(data)["name"])

User.from_json('{"name": "Alice"}')             # OK
Deserializable.from_json('{}')                   # error: Cannot instantiate abstract class
```

## Common type-checker errors and how to read them

### mypy: `Cannot instantiate abstract class "X" with abstract method "Y"`

Trying to create an instance of a class that has unimplemented abstract methods.

```
error: Cannot instantiate abstract class "BadShape" with abstract method "perimeter"
```

**Fix:** Implement all abstract methods listed in the error, or if the class is meant to be abstract itself, do not instantiate it directly.

### pyright: `"X" cannot be instantiated — it is abstract`

Pyright's equivalent message, sometimes with a list of missing methods.

```
error: Cannot instantiate abstract class "BrokenRepo"
  "BrokenRepo" is abstract because it does not implement "list_all", "save", "delete"
```

**Fix:** Same — implement the listed methods.

### mypy: `Return type "X" of "method" incompatible with return type "Y" in supertype "ABC"`

The overriding method's return type is not compatible with the abstract method's declared return type.

```
error: Return type "str" of "area" incompatible with return type "float"
       in supertype "Shape"
```

**Fix:** Ensure the override's return type is the same or a subtype of the abstract method's return type.

### mypy: `Signature of "method" incompatible with supertype "ABC"`

The overriding method changes the parameter types in an incompatible way.

```
error: Signature of "get" incompatible with supertype "Repository"
  Superclass:   def get(self, id: ID) -> T | None
  Subclass:     def get(self, id: str, default: str = ...) -> str
```

**Fix:** The override must accept at least the same parameter types as the abstract declaration. Adding required parameters that the base does not have breaks the contract.

## Use-case cross-references

- [-> UC-04](../usecases/UC04-generic-constraints.md) — ABCs define plug-in interfaces where all implementations must provide a complete method set.
- [-> UC-05](../usecases/UC05-structural-contracts.md) — Abstract properties enforce that subclasses declare configuration values at the type level.

## When to Use ABCs

Use ABCs when you need **explicit contracts with enforced inheritance**:

- **You want runtime enforcement**: ABCs prevent instantiation of incomplete implementations at runtime, not just type-check time.

  ```python
  from abc import ABC, abstractmethod

  class PaymentProcessor(ABC):
      @abstractmethod
      def charge(self, amount: float) -> bool: ...

  class StripeProcessor(PaymentProcessor):
      def charge(self, amount: float) -> bool:
          return True

  # Missing implementation catches at both check and runtime
  class BadProcessor(PaymentProcessor):
      pass

  BadProcessor()  # TypeError: Can't instantiate abstract class
  ```

- **You want shared implementation**: ABCs can provide concrete methods that all implementations inherit.

  ```python
  class CacheStorage(ABC):
      def get_or_compute(self, key: str, fn: callable) -> str:
          val = self.get(key)
          if val is None:
              val = fn()
              self.set(key, val)
          return val

      @abstractmethod
      def get(self, key: str) -> str | None: ...

      @abstractmethod
      def set(self, key: str, value: str) -> None: ...
  ```

- **You need nominal boundaries**: You want only explicitly declared subclasses to satisfy the interface, not accidental duck-types.

  ```python
  class CryptoSigner(ABC):
      @abstractmethod
      def sign(self, data: bytes) -> bytes: ...

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
  class FileReader(ABC):
      @abstractmethod
      def read(self) -> str: ...

  # Good: Protocol accepts any object with .read()
  from typing import Protocol

  class FileReader(Protocol):
      def read(self) -> str: ...

  def process(reader: FileReader) -> str:
      return reader.read()

  process(open("file.txt"))        # OK with Protocol
  process(StringIO("text"))       # OK with Protocol
  ```

- **You're mocking for tests**: Abstract classes require full subclass implementation.

  ```python
  # Bad: verbose mock
  class MockRepo(Repository):
      def get(self, id: int) -> User: return User()
      def save(self, u: User) -> None: pass
      def delete(self, id: int) -> None: pass
      def list_all(self) -> list[User]: return []

  # Good: simple dict works with Protocol
  mock_repo = {"get": lambda id: User(), "save": lambda u: None}
  ```

- **You're adding interface to third-party class**: Can't subclass classes you don't own.

  ```python
  # Can't make list satisfy Iterable via inheritance
  # (it already does via collections.abc, but the point stands)
  ```

- **You need mixin-style composition**: ABCs are single-base focused; use Protocols for cross-cutting concerns.

---

## Antipatterns When Using ABCs

### Antipattern 1: ABC With All Concrete Methods

Creating an ABC that has no abstract methods defeats the purpose — use a regular class.

```python
# Bad: why use ABC at all?
class UsefulMixin(ABC):
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

---

### Antipattern 2: Too Many Abstract Methods (God Interface)

ABCs with 20+ abstract methods force implementers to provide everything, even unused methods.

```python
# Bad: monolithic ABC
class Service(ABC):
    @abstractmethod def start(self) -> None: ...
    @abstractmethod def stop(self) -> None: ...
    @abstractmethod def status(self) -> str: ...
    @abstractmethod def config(self) -> dict: ...
    @abstractmethod def logging(self) -> None: ...
    # ... 15 more methods

# A read-only service now must implement write methods it can't support
class ReadOnlyService(Service):
    def start(self) -> None: ...
    def stop(self) -> None: ...
    # ... must stub out 20 methods
```

**Better**: Split into focused ABCs.

```python
class Startable(ABC):
    @abstractmethod def start(self) -> None: ...
    @abstractmethod def stop(self) -> None: ...

class Configurable(ABC):
    @abstractmethod def config(self) -> dict: ...

# Compose only what's needed
class ReadOnlyService(Startable):
    def start(self) -> None: ...
    def stop(self) -> None: ...
```

---

### Antipattern 3: Using `register()` to Bypass the Contract

`ABCMeta.register()` creates virtual subclasses that pass `isinstance()` but don't satisfy the type checker — defeats the whole point.

```python
# Bad: virtual subclass that doesn't actually implement interface
class Printable(ABC):
    @abstractmethod
    def print(self) -> str: ...

class Data:
    pass  # no print method!

Printable.register(Data)
isinstance(Data(), Printable)  # True at runtime
process.printable(Data())      # Type error! (correctly rejected)
```

---

### Antipattern 4: Abstract `__init__` Signature

Marking `__init__` as abstract is rarely useful since subclasses always have different constructor signatures.

```python
# Bad: abstract __init__ forces same signature
class Entity(ABC):
    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name

# Good: let subclasses define their own constructors
class Entity(ABC):
    @abstractmethod
    def get_id(self) -> int: ...
    
    @abstractmethod
    def get_name(self) -> str: ...
```

---

### Antipattern 5: ABC Where Protocol Suffers Better

Using ABC when structural typing would allow more flexibility.

```python
# Bad: requires inheritance for simple iteration
class ItemIterable(ABC):
    @abstractmethod
    def __iter__(self) -> Iterator[Item]: ...

def process_items(container: ItemIterable) -> list[Item]:
    return list(container)

# Now can't pass list, tuple, custom iterators...
process_items([Item()])  # Type error!

# Good: Protocol accepts any iterable
class ItemIterable(Protocol):
    def __iter__(self) -> Iterator[Item]: ...

process_items([Item()])  # OK!
```

---

## Antipatterns with Other Techniques (Where ABCs Improve Code)

### Antipattern A: Overusing duck typing without any interface

No interface forces runtime errors and makes refactoring hazardous.

```python
# Bad: no contract, errors only at runtime
def process_reader(reader):
    return reader.read().strip()  # What if .read() missing?
                                 # What if it takes args?

# ABC enforces the contract
class Reader(ABC):
    @abstractmethod
    def read(self) -> str: ...

def process_reader(reader: Reader) -> str:
    return reader.read().strip()  # Compile-time safety
```

---

### Antipattern B: Using `isinstance()` checks everywhere

Runtime type checking instead of static contracts.

```python
# Bad: if-else chain with type checks
def handle(obj):
    if isinstance(obj, File):
        obj.read()
    elif isinstance(obj, Socket):
        obj.recv()
    elif isinstance(obj, String):
        obj.decode()
    else:
        raise TypeError("unsupported")

# Good: ABC with single interface
class Source(ABC):
    @abstractmethod
    def read(self) -> bytes: ...

def handle(source: Source) -> bytes:
    return source.read()  # Polymorphism, no isinstance needed
```

---

### Antipattern C: Passing `None` as "not implemented"

Using sentinel values or `None` instead of enforcing implementation.

```python
# Bad: optional abstract method that returns None
class Widget:
    def customize(self) -> str | None:
        return None  # Base impl returns None

class MyWidget(Widget):
    pass  # Inherits None behavior — is this intentional?

result = MyWidget().customize()  # runtime surprise
if result is None:
    handle_unsupported()

# Good: ABC with abstract method
class Widget(ABC):
    @abstractmethod
    def customize(self) -> str: ...  # Must be implemented
```

---

### Antipattern D: Base class with "do not use directly" comment

Relying on documentation instead of enforcement.

```python
# Bad: documented but not enforced
class BaseHandler:
    """Do not instantiate directly — subclass and implement methods."""
    def handle(self) -> str:
        raise NotImplementedError("subclasses must implement")

handler = BaseHandler()
handler.handle()  # TypeError at runtime only

# Good: ABC prevents instantiation
class BaseHandler(ABC):
    @abstractmethod
    def handle(self) -> str: ...

handler = BaseHandler()  # TypeError at instantiation time
```

---

### Antipattern E: Partial implementation without awareness

Subclassing but not realizing some method is required.

```python
# Bad: no way to know what's required
class Plugin:
    def initialize(self) -> None:
        pass  # default no-op
    
    def run(self, data: str) -> str:
        return data  # default passthrough

class MyPlugin(Plugin):
    # Forgot to override .initialize()
    def run(self, data: str) -> str:
        return data.upper()

MyPlugin().run("test")  # Runs, but init not called!

# Good: ABC shows what's required
class Plugin(ABC):
    @abstractmethod
    def initialize(self) -> None: ...
    @abstractmethod
    def run(self, data: str) -> str: ...

class MyPlugin(Plugin):
    def initialize(self) -> None:
        ...
    def run(self, data: str) -> str:
        return data.upper()

MyPlugin()  # OK — implements all abstract methods
```

---

### Antipattern F: Interface segregation failure with union types

Using union types for separate concepts that should be distinct.

```python
# Bad: union of unrelated functionality
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

---

## Source anchors

- [PEP 3119 — Introducing Abstract Base Classes](https://peps.python.org/pep-3119/)
- [`abc` module docs](https://docs.python.org/3/library/abc.html)
- [`collections.abc` module docs](https://docs.python.org/3/library/collections.abc.html)
- [typing spec: Abstract methods](https://typing.readthedocs.io/en/latest/spec/class-compat.html)
- [mypy docs: Abstract base classes](https://mypy.readthedocs.io/en/stable/class_basics.html#abstract-base-classes-and-multiple-inheritance)
