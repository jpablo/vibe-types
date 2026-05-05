# Typestate (via Literal Types and Overload)

> **Since:** `Literal` Python 3.8 (PEP 586); `@overload` Python 3.5 (PEP 484); `Generic` Python 3.5 (PEP 484)

## What it is

Python does not have native typestate support, but the **type checker** can enforce state-dependent method availability using a combination of `Generic[State]` with `Literal` type parameters and `@overload` decorators. The pattern uses a generic class parameterized by a state type (e.g., `Literal["open"]`, `Literal["closed"]`), and `@overload` signatures restrict which methods are available in each state.

The checker (mypy, pyright) enforces that methods declared for `Connection[Literal["open"]]` cannot be called on a `Connection[Literal["closed"]]`. State transitions return a new object with the updated type parameter. At runtime, the state parameter has no cost — `Generic` subscripts are erased, and `Literal` types exist only during static analysis.

This pattern is less ergonomic than Rust's or Scala's typestate because Python's type system requires explicit `@overload` declarations and `TYPE_CHECKING` guards, but it provides the same compile-time safety when used with a strict type checker.

## What constraint it enforces

**Methods annotated with `@overload` for a specific `Literal` state are only callable when the type checker can prove the object is in that state. State transitions change the `Literal` type parameter, and the checker rejects calls that do not match the current state.**

## Minimal snippet

```python
from typing import Generic, Literal, TypeVar, overload

S = TypeVar("S")

class Door(Generic[S]):
    def __init__(self, state: S) -> None:
        self._state = state

    @staticmethod
    def create() -> "Door[Literal['closed']]":
        return Door("closed")

def open_door(door: Door[Literal["closed"]]) -> Door[Literal["open"]]:
    return Door("open")

def enter(door: Door[Literal["open"]]) -> None:
    print("Entering!")

d = Door.create()
# enter(d)           # error: expected Door[Literal["open"]], got Door[Literal["closed"]]
d2 = open_door(d)
enter(d2)            # OK
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Literal types** [-> T52](T52-literal-types.md) | `Literal["open"]`, `Literal["closed"]` serve as state tags. The checker distinguishes them at analysis time; at runtime they are plain strings. |
| **Generics / TypeVar** [-> T04](T04-generics-bounds.md) | `Generic[S]` parameterizes the class by state. The state is a type parameter that the checker tracks through assignments and returns. |
| **@overload** [-> T22](T22-callable-typing.md) | `@overload` provides different type signatures for different state parameters, restricting which methods are available per state. |
| **Phantom types** [-> T27](T27-erased-phantom.md) | Typestate is a specific application of phantom types where the phantom parameter encodes a finite state machine. |
| **Type narrowing** [-> T14](T14-type-narrowing.md) | After a state transition (function returning the new type), the checker narrows the variable's type to the new state. |
| **TYPE_CHECKING guard** | State tag classes can be defined under `if TYPE_CHECKING:` to avoid any runtime cost for the state type definitions themselves. |

## Gotchas and limitations

1. **No ownership / linear types.** After a state transition, the old variable still exists with the old type. Nothing prevents using the stale reference. Developers must discipline themselves to rebind: `d = open_door(d)`.

2. **@overload is verbose.** Each state-specific method requires a separate `@overload` signature plus the implementation. For many states and methods, this leads to significant boilerplate.

3. **Runtime state is not linked to type state.** The `Literal` type parameter is erased at runtime. If runtime code inspects `self._state`, it may disagree with the checker's view. Keep the runtime state synchronized manually.

4. **Limited checker support.** Not all type checkers handle `Literal`-parameterized `Generic` classes equally well. pyright has the best support; mypy may require `# type: ignore` in some edge cases.

5. **No exhaustive state checking.** Unlike Rust's `match` or Scala's sealed traits, Python's type checkers do not enforce exhaustive handling of all states. You must manually ensure all state transitions are covered.

6. **Cannot express "any state" easily.** A function that works on a `Door` in any state requires `Door[Any]` or a plain `Door` (unparameterized), which loses the state tracking. There is no built-in "existential state" type.

## Beginner mental model

Think of the `Literal` state parameter as a **color-coded label** on the object. A `Door[Literal["closed"]]` has a red label; `Door[Literal["open"]]` has a green label. The `enter` function has a sign saying "green labels only." The `open_door` function takes a red-labeled door and hands back a green-labeled one. The type checker is the security guard checking labels. At runtime, the labels are invisible — they exist only in the checker's analysis.

## Example A -- HTTP connection with state tracking

```python
from __future__ import annotations
from typing import Generic, Literal, TypeVar

S = TypeVar("S")

class HttpConn(Generic[S]):
    def __init__(self, host: str) -> None:
        self._host = host

    @staticmethod
    def create(host: str) -> HttpConn[Literal["idle"]]:
        return HttpConn(host)

def connect(c: HttpConn[Literal["idle"]]) -> HttpConn[Literal["connected"]]:
    return HttpConn(c._host)

def authenticate(c: HttpConn[Literal["connected"]], token: str) -> HttpConn[Literal["auth"]]:
    return HttpConn(c._host)

def fetch(c: HttpConn[Literal["auth"]], path: str) -> str:
    return f"Response from {c._host}{path}"

# Valid:
c = HttpConn.create("api.example.com")
c2 = connect(c); c3 = authenticate(c2, "tok"); data = fetch(c3, "/users")
# fetch(HttpConn.create("x"), "/")  # error: expected auth, got idle
```

## Example B -- File handle with read/write modes

```python
from __future__ import annotations
from typing import Generic, Literal, TypeVar

M = TypeVar("M")

class TypedFile(Generic[M]):
    def __init__(self, path: str) -> None: self._path = path

    @staticmethod
    def open_read(path: str) -> TypedFile[Literal["r"]]: return TypedFile(path)
    @staticmethod
    def open_write(path: str) -> TypedFile[Literal["w"]]: return TypedFile(path)

def read_line(f: TypedFile[Literal["r"]]) -> str: return "line"
def write_line(f: TypedFile[Literal["w"]], line: str) -> None: ...

rf = TypedFile.open_read("data.txt")
read_line(rf)         # OK
# write_line(rf, "x") # error: expected Literal["w"], got Literal["r"]
wf = TypedFile.open_write("out.txt")
write_line(wf, "hello")  # OK
# read_line(wf)           # error: expected Literal["r"], got Literal["w"]
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Typestate makes invalid state transitions a type-checker error, preventing operations in the wrong state.
- [-> UC-08](../usecases/UC08-error-handling.md) -- Protocol violations are caught during static analysis instead of producing runtime exceptions.

## When to Use

Use typestate when **method availability depends on protocol-compliant state transitions**:

- **Multi-step builders**: Query builders, form builders, request builders where methods must be called in specific order.
- **Resource lifecycle management**: Database connections, file handles, network sockets with valid operations per state.
- **Protocol implementations**: TCP handshakes, TLS negotiation, API auth flows with strict transition sequences.
- **Domain workflows**: Order processing pipelines, document approval chains, deployment stages with valid transitions.
- **Configuration APIs**: Builders requiring `.with_required_field()` before `.build()` is available.

```python
# Good fit: query builder requires .from() before .select()
from typing import Generic, Literal, TypeVar

Q = TypeVar("Q")

class Query(Generic[Q]):
    def __init__(self) -> None:
        self._table: str = ""
        self._columns: list[str] = []

    @staticmethod
    def begin() -> "Query[Literal['no_table']]":
        return Query()

def from_table(q: Query[Literal["no_table"]], table: str) -> Query[Literal["has_table"]]:
    q._table = table
    return q

def select_columns(q: Query[Literal["has_table"]], columns: list[str]) -> Query[Literal["has_table"]]:
    q._columns = columns
    return q

# .select_columns() before .from_table() is a type error
q = select_columns(from_table(Query.begin(), "users"), ["id", "name"])  # OK
# select_columns(Query.begin(), ["id"])  # error: expected has_table, got no_table
```

## When Not to Use

Avoid typestate when:

- **State doesn't affect method availability**: If all methods work in all states, use runtime guards instead.
- **Simple two-state toggles**: A boolean flag with runtime checks is clearer for open/closed switches.
- **Highly dynamic or user-defined states**: When states are created at runtime, static analysis cannot help.
- **Frequent state oscillation**: When the same value transitions back and forth repeatedly, variable reassignment becomes awkward.
- **Collections of mixed states**: Typestate makes it hard to store values in different states together.

```python
# Bad fit: simple toggle doesn't need typestate
from typing import Generic, Literal, TypeVar

S = TypeVar("S")

class LightSwitch(Generic[S]):
    """Overkill: typestate for a simple boolean toggle."""
    def __init__(self, on: bool) -> None:
        self._on = on

# Better: just use a boolean property
class LightSwitch:
    def __init__(self) -> None:
        self._on = False

    def toggle(self) -> None:
        self._on = not self._on

    @property
    def is_on(self) -> bool:
        return self._on
```

## Antipatterns When Using Typestate

### A. Keeping stale references after transitions

```python
from typing import Generic, Literal, TypeVar

S = TypeVar("S")

class Connection(Generic[S]):
    def __init__(self, host: str) -> None:
        self._host = host

    @staticmethod
    def create(host: str) -> "Connection[Literal['disconnected']]":
        return Connection(host)

def connect(c: Connection[Literal["disconnected"]]) -> Connection[Literal["connected"]]:
    return Connection(c._host)

def query(c: Connection[Literal["connected"]], sql: str) -> None:
    print(f"Running: {sql}")

# Antipattern: old_conn still typed as disconnected
c = Connection.create("db.example.com")
c2 = connect(c)
query(c2, "SELECT 1")  # OK
# query(c, "SELECT 1")  # type error, but c still exists in scope!

# Better: use let-style reassignment pattern
c = Connection.create("db.example.com")
c = connect(c)  # rebind to update type
query(c, "SELECT 1")  # OK
```

### B. Mismatched runtime and type states

```python
from typing import Generic, Literal, TypeVar

S = TypeVar("S")

class Buffer(Generic[S]):
    def __init__(self) -> None:
        self._data: list[int] = []
        self._runtime_state: str = "empty"  # runtime state

    @staticmethod
    def create() -> "Buffer[Literal['empty']]":
        return Buffer()

def fill(b: Buffer[Literal["empty"]]) -> Buffer[Literal["filled"]]:
    b._runtime_state = "filled"  # OK: runtime matches type
    b._data = [1, 2, 3]
    return b

def process(b: Buffer[Literal["filled"]]) -> int:
    return sum(b._data)

# Antipattern: runtime state diverges from type state
b = Buffer.create()
b._runtime_state = "filled"  # BUG: type says 'empty', runtime says 'filled'
# process(b)  # type error prevents this, but runtime would work!

# Also bad: modifying runtime state without type transition
class Buffer(Generic[S]):
    def __init__(self) -> None:
        self._data: list[int] = []
        self._ready = False

    @staticmethod
    def create() -> "Buffer[Literal['empty']]":
        return Buffer()

fill_buffer = lambda b: setattr(b, '_ready', True) or b  # no type change!
```

### C. Overly granular state explosion

```python
from typing import Generic, Literal, TypeVar

S = TypeVar("S")

# Antipattern: combinatorial state explosion
class Builder(Generic[S]):
    pass

def with_name(b: Builder[Literal["base"]]) -> Builder[Literal["has_name"]]: ...
def with_age(b: Builder[Literal["has_name"]]) -> Builder[Literal["has_name_and_age"]]: ...
def with_email(b: Builder[Literal["has_name_and_age"]]) -> Builder[Literal["has_name_age_email"]]: ...
# Adding more fields creates more states combinatorially

# Better: use a single phase dimension
Phase = Literal["step0", "step1", "step2", "step3"]

class Builder(Generic[Phase]):
    def __init__(self, phase: Phase) -> None:
        self._phase = phase

    @staticmethod
    def begin() -> "Builder['step0']":
        return Builder("step0")

def complete_step(current: "Builder['step0']") -> "Builder['step1']":
    return Builder("step1")
```

### D. Using `Literal[Any]` to bypass state checks

```python
from typing import Generic, Literal, TypeVar, Any

S = TypeVar("S")

class Session(Generic[S]):
    @staticmethod
    def create() -> "Session[Literal['anonymous']]":
        return Session()

def login(s: Session[Literal["anonymous"]]) -> Session[Literal["authenticated"]]:
    return Session()

def access_admin(s: Session[Literal["authenticated"]]) -> None:
    print("Admin access granted")

# Antipattern: bypassing type safety with casts
s = Session.create()
s_as_any: Session[Any] = s  # or `typing.cast`, `# type: ignore`
# access_admin(s_as_any)  # no error! type safety bypassed

# Or worse: # type: ignore
s = Session.create()
access_admin(s)  # type: ignore  # NO! defeats the whole point
```

## Antipatterns Fixed by Typestate

### A. Runtime None checks for required initialization

```python
from typing import Generic, Literal, TypeVar

# Antipattern: runtime error if initialized incorrectly
class UserBuilderAnti:
    def __init__(self) -> None:
        self._name: str | None = None
        self._email: str | None = None

    def with_name(self, name: str) -> "UserBuilderAnti":
        self._name = name
        return self

    def with_email(self, email: str) -> "UserBuilderAnti":
        self._email = email
        return self

    def build(self) -> dict[str, str]:
        if self._name is None:
            raise RuntimeError("name not set")  # runtime error
        if self._email is None:
            raise RuntimeError("email not set")  # runtime error
        return {"name": self._name, "email": self._email}

# Runtime error:
UserBuilderAnti().build()  # RuntimeError at runtime

# Typestate fix: missing fields are type errors
class UserBuilder(Generic[S]):
    pass

def with_name(b: UserBuilder[Literal["none"]]) -> UserBuilder[Literal["name"]]:
    b._name = "John"  # type: ignore
    return b

def with_email(b: UserBuilder[Literal["name"]]) -> UserBuilder[Literal["both"]]:
    b._email = "john@example.com"  # type: ignore
    return b

def build_user(b: UserBuilder[Literal["both"]]) -> dict[str, str]:
    return {"name": b._name, "email": b._email}  # type: ignore

# Type error:
# build_user(UserBuilder())  # error: expected Literal["both"], got Literal["none"]
# build_user(with_name(UserBuilder()))  # error: expected Literal["both"], got Literal["name"]
build_user(with_email(with_name(UserBuilder())))  # OK
```

### B. Invalid state transitions caught at runtime

```python
from typing import Generic, Literal, TypeVar

# Antipattern: wrong state caught at runtime
class VendingMachineAnti:
    def __init__(self) -> None:
        self._state: str = "idle"

    def insert_coin(self) -> None:
        if self._state != "idle":
            raise RuntimeError("Cannot insert coin: not in idle state")
        self._state = "awaiting_selection"

    def select_item(self) -> None:
        if self._state != "awaiting_selection":
            raise RuntimeError("Cannot select: no coin inserted")
        self._state = "dispensing"

    def dispense(self) -> None:
        if self._state != "dispensing":
            raise RuntimeError("Cannot dispense: item not selected")
        self._state = "idle"

# Runtime errors:
vm = VendingMachineAnti()
vm.select_item()  # RuntimeError: Cannot select: no coin inserted

# Typestate fix: invalid transitions don't type-check
class VendingMachine(Generic[S]):
    pass

def insert_coin(vm: VendingMachine[Literal["idle"]]) -> VendingMachine[Literal["awaiting_selection"]]:
    return VendingMachine()

def select_item(vm: VendingMachine[Literal["awaiting_selection"]]) -> VendingMachine[Literal["dispensing"]]:
    return VendingMachine()

def dispense(vm: VendingMachine[Literal["dispensing"]]) -> VendingMachine[Literal["idle"]]:
    return VendingMachine()

# Type errors:
# select_item(VendingMachine())  # error: expected awaiting_selection, got idle
# dispense(VendingMachine())  # error: expected dispensing, got idle

# Correct sequence:
vm = dispense(select_item(insert_coin(VendingMachine())))  # OK
```

### C. Magic string state checks

```python
from typing import Generic, Literal, TypeVar

# Antipattern: error-prone string comparison
class OrderAnti:
    def __init__(self) -> None:
        self._status: str = "pending"

    def confirm(self) -> None:
        if self._status == "pending":  # magic string, typo-prone
            self._status = "confirmed"
        else:
            raise RuntimeError("Already confirmed")

    def ship(self) -> None:
        if self._status == "confirmed":  # another magic string
            self._status = "shipped"
        else:
            raise RuntimeError("Must confirm first")

# Runtime errors from typos or wrong sequence:
order = OrderAnti()
order.ship()  # RuntimeError: Must confirm first

# Typestate fix: wrong operations don't compile
S = TypeVar("S")

class Order(Generic[S]):
    pass

def confirm(order: Order[Literal["pending"]]) -> Order[Literal["confirmed"]]:
    return Order()

def ship(order: Order[Literal["confirmed"]]) -> Order[Literal["shipped"]]:
    return Order()

# Type error:
# ship(Order())  # error: expected confirmed, got pending

# Correct sequence:
ship(confirm(Order()))  # OK
```

### D. Mutable object in wrong state without guards

```python
from typing import Generic, Literal, TypeVar

# Antipattern: runtime guard on mutable state
class FormAnti:
    def __init__(self) -> None:
        self._validated = False
        self._data: dict = {}

    def validate(self) -> None:
        self._validated = True

    def submit(self) -> None:
        if not self._validated:
            raise ValueError("Form not validated")  # runtime check
        print("Submitting:", self._data)

# Runtime error:
f = FormAnti()
f.submit()  # ValueError: Form not validated

# Typestate fix: .submit() unavailable until .validate() called
class Form(Generic[S]):
    pass

def validate(form: Form[Literal["draft"]]) -> Form[Literal["validated"]]:
    return Form()

def submit(form: Form[Literal["validated"]]) -> None:
    print("Submitting validated form")

# Type error:
# submit(Form())  # error: expected validated, got draft

# Correct:
submit(validate(Form()))  # OK
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Typestate makes invalid state transitions a type-checker error, preventing operations in the wrong state.
- [-> UC-08](../usecases/UC08-error-handling.md) -- Protocol violations are caught during static analysis instead of producing runtime exceptions.
- [-> UC-09](../usecases/UC09-builder-config.md) -- Builder APIs that enforce required configuration steps before building.
- [-> UC-11](../usecases/UC11-effect-tracking.md) -- Track resource lifecycle (open/closed, connected/authenticated) at the type level.
- [-> UC-13](../usecases/UC13-state-machines.md) -- Encode state machine valid transitions so invalid transitions are compile errors.

## Source anchors

- [PEP 586 -- Literal Types](https://peps.python.org/pep-0586/)
- [PEP 484 -- Type Hints (@overload, Generic)](https://peps.python.org/pep-0484/)
- [mypy -- Literal types](https://mypy.readthedocs.io/en/stable/literal_types.html)
- [pyright -- Literal type narrowing](https://microsoft.github.io/pyright/#/type-concepts-advanced?id=literal-types)
