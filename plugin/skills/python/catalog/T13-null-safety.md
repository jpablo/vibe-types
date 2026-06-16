# Basic Annotations, Optional, and None

## What it is

Python type annotations let you declare the expected types of variables, function parameters, and return values. Since Python 3.5 (PEP 484), these annotations are consumed by static type checkers but ignored at runtime. Variable annotations (PEP 526) arrived in Python 3.6, and the `X | Y` union syntax (PEP 604) in Python 3.10. Together with `Optional[X]` (equivalent to `X | None`), they form the foundation of Python's gradual type system: every other typing feature builds on top of basic annotations.

**Since:** Python 3.5 (PEP 484 — function annotations); Python 3.6 (PEP 526 — variable annotations); Python 3.10 (PEP 604 — `X | Y` syntax)

## What constraint it enforces

**Variables, parameters, and return values must match their declared types; `None` must be handled explicitly via `Optional[X]` or `X | None` before accessing type-specific attributes.**

When you annotate a function parameter as `str`, the checker rejects calls that pass `int`. When you annotate a return type as `str`, returning `int` is an error. When a value may be `None`, you must narrow the type (with an `if` check, `assert`, or similar) before using it as the non-`None` type.

## Minimal snippet

```python
def greet(name: str) -> str:
    return 42  # error: Type "Literal[42]" is not assignable to return type "str"

x: int = "hello"  # error: Type "Literal['hello']" is not assignable to declared type "int"

def maybe(val: str | None) -> int:
    return len(val)  # error: Argument of type "str | None" cannot be assigned to parameter "obj" of type "Sized"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Union / Literal** [-> T02](T02-union-intersection.md) | `Union[X, Y]` and `Literal["a"]` extend basic annotations to multi-type and value-level constraints. |
| **TypeGuard / TypeIs** [-> T14](T14-type-narrowing.md) | Narrowing functions refine `Optional` and `Union` annotations inside conditional branches. |
| **Gradual typing** [-> T47](T47-gradual-typing.md) | Unannotated code defaults to `Any`, which is compatible with every type. Adding annotations is how you opt into stricter checking. |
| **Final / ClassVar** [-> T32](T32-immutability-markers.md) | `Final[int]` combines a basic annotation with an immutability constraint. |
| **TypedDict** [-> T31](T31-record-types.md) | TypedDict values are annotated with the same basic types described here. |

## Gotchas and limitations

1. **`Optional[X]` does not mean "optional parameter."** `Optional[X]` is strictly `X | None` — it says the value can be `None`, not that the caller may omit the argument. A truly optional parameter needs a default value: `def f(x: int = 0)`.

2. **Annotations are not enforced at runtime.** `def f(x: int): ...` happily accepts `f("hello")` at runtime. Enforcement is purely through type checkers. Libraries like `beartype` or `pydantic` add runtime validation separately.

3. **`None` is a type and a value.** The annotation `None` means `type(None)`. In return annotations, `-> None` means the function returns `None` (not that it has no return). This differs from languages where `void` means "no return value."

4. **mypy's `--strict` mode vs defaults.** By default, mypy allows unannotated functions (treating them as `Any`). Under `--strict`, every function needs annotations. pyright's strict mode is similar. The same code can produce zero errors or many depending on configuration.

5. **`from __future__ import annotations` (PEP 563).** This import makes all annotations strings at runtime (deferred evaluation), which affects runtime introspection but not type checking. It allows forward references and the `X | Y` syntax on Python < 3.10 for type-checking purposes.

6. **Checker divergences on `None` narrowing.** mypy and pyright sometimes differ on how aggressively they narrow `Optional` types through truthiness checks (`if x:` narrows `str | None` to `str` in most cases, but edge cases around empty strings vary).

## Beginner mental model

Think of annotations as **labels on boxes**. When you write `x: int`, you are labeling a box "integers only." The type checker acts like a strict librarian who ensures you only put integers into that box. If you write `x: int | None`, the box accepts integers *or* nothing (`None`), but the librarian will insist you check whether the box is empty before treating its contents as an integer.

Without annotations, Python treats every box as "anything goes" (`Any`). Annotations are how you trade flexibility for safety.

## Example A — Wrong return type caught

```python
def parse_age(raw: str) -> int:
    if raw.isdigit():
        return int(raw)          # OK
    return "unknown"             # error: Type "Literal['unknown']" is not assignable to return type "int"
```

```text
# mypy
error: Incompatible return value type (got "str", expected "int")

# pyright
error: Type "Literal['unknown']" is not assignable to return type "int"
```

The fix depends on intent. If "unknown" is a valid case, change the return type to `int | str` or raise an exception instead.

## Example B — Optional parameter requiring None check

Without narrowing, the checker rejects subscript and attribute access on a possibly-`None` value:

```python
def first_char_unsafe(text: str | None) -> str:
    return text[0]  # error: Object of type "None" is not subscriptable
```

Handling the `None` case first narrows the type and satisfies the checker:

```python
def first_char(text: str | None) -> str:
    if text is None:
        return ""                # early return handles the None case
    return text[0]               # OK — type narrowed to str after the None check


# Alternative: assert-based narrowing
def first_char_v2(text: str | None) -> str:
    assert text is not None      # narrows str | None to str
    return text[0]               # OK
```

## Common type-checker errors and how to read them

### Incompatible return value type

```text
# mypy
error: Incompatible return value type (got "int", expected "str")

# pyright
error: Type "int" is not assignable to type "str"
```

**Cause:** The value you return does not match the declared `-> T` annotation.
**Fix:** Either change the return value or broaden the return annotation.

### Incompatible types in assignment

```text
# mypy
error: Incompatible types in assignment (got "str", expected "int")

# pyright
error: Type "str" is not assignable to type "int"
```

**Cause:** You assigned a value that does not match the variable's declared type.
**Fix:** Change the assignment or the annotation. If the variable should accept multiple types, use a `Union`.

### Item of Optional has no attribute

```text
# mypy
error: Item "None" of "str | None" has no attribute "upper"

# pyright
error: "upper" is not a known member of "None"
```

**Cause:** You accessed an attribute on a value that might be `None`.
**Fix:** Narrow the type first with `if x is not None:`, `assert x is not None`, or use a default: `(x or "").upper()`.

### Missing return statement

```text
# mypy
error: Missing return statement

# pyright
error: Function with declared type "int" must return value on all code paths
```

**Cause:** A function annotated with a return type has code paths that fall off without returning.
**Fix:** Add a `return` statement covering all branches, or return `None` and update the annotation to `-> int | None`.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Typing function signatures for public API contracts.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Catching type mismatches in data pipelines.
- [-> UC-03](../usecases/UC03-exhaustiveness.md) — Enforcing None-safety in database query results.
- [-> UC-08](../usecases/UC08-error-handling.md) — Optional return types encode None-as-error patterns.

## Source anchors

- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
- [PEP 526 — Syntax for Variable Annotations](https://peps.python.org/pep-0526/)
- [PEP 604 — Allow writing union types as X | Y](https://peps.python.org/pep-0604/)
- [PEP 563 — Postponed Evaluation of Annotations](https://peps.python.org/pep-0563/)
- [typing module documentation](https://docs.python.org/3/library/typing.html)
- [mypy documentation — Built-in types](https://mypy.readthedocs.io/en/stable/builtin_types.html)

## When to use it

- **External/API boundaries** — JSON responses, HTTP parameters, and third-party APIs where absence is expected.

  ```python
  from dataclasses import dataclass

  @dataclass
  class User:
      name: str
      email: str | None  # absence is a normal, expected state

  def get_user(id: int) -> User | None:
      ...
  ```

- **Database queries** — lookups that may return no result.

  ```python
  from dataclasses import dataclass

  @dataclass
  class User:
      name: str

  def find_user(id: int) -> User | None:
      ...

  user = find_user(1)
  if user:
      print(user.name)
  ```

- **Optional object attributes** — config parameters, partial updates, optional dependencies.

  ```python
  class Config:
      theme: str = "dark"
      optional_plugin: str | None = None

  def load_plugin(cfg: Config) -> str:
      if cfg.optional_plugin is None:
          return "no plugin"
      return cfg.optional_plugin
  ```

- **Deep nested access** — chains of lookups where intermediate values may be absent.

  ```python
  from typing import TypedDict, NotRequired

  class CountryDict(TypedDict):
      city: str

  class AddressDict(TypedDict):
      country: NotRequired[CountryDict]

  def get_city(address: AddressDict | None) -> str:
      country = address.get("country") if address else None
      city = country.get("city") if country else None
      return city or "Unknown"
  ```

- **Defaulting absent values** — `or` for falsy-absent semantics, explicit checks for None-only defaults.

  ```python
  def maybe_int() -> int | None:
      return None

  value = maybe_int() or 42  # 0 would also become 42
  value = maybe_int() if maybe_int() is not None else 42  # only None becomes 42
  ```

## When not to use it

- **When absence is an error** — failing fast is clearer than propagating `None`.

  ```python
  from dataclasses import dataclass

  @dataclass
  class User:
      name: str

  # Instead of returning User | None and hoping callers check:
  def get_admin() -> User:
      """Raises KeyError if no admin is configured."""
      ...

  admin = get_admin()  # the error path lives in one place
  ```

- **When you need to say *why* a value is absent** — return a result union instead of a bare `None`.

  ```python
  from dataclasses import dataclass

  # Instead of: def parse(s: str) -> int | None
  @dataclass
  class ParseError:
      message: str

  @dataclass
  class ParsedValue:
      value: int

  def parse(s: str) -> ParsedValue | ParseError:
      ...
  ```

- **For collections that should be empty vs absent** — prefer empty collections over `None`.

  ```python
  class SearchResult:
      # tags: list[str] | None = None   # forces every reader to check for None
      tags: list[str] = []  # an empty list is meaningful and safe to iterate
  ```

## Antipatterns when using null safety

### Pattern: Calling `.get()` without handling the `None` return

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str

def get_user_name(users: dict[int, User], id: int) -> str:
    user = users.get(id)
    return user.name  # error: "name" is not a known attribute of "None"
```

**Better:**

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str

def get_user_name(users: dict[int, User], id: int) -> str:
    user = users.get(id)
    if user is None:
        raise KeyError(f"User {id} not found")
    return user.name
```

---

### Pattern: Boolean coercion for optional values

```python
class Config:
    timeout: int | None = None

def connect(cfg: Config) -> None:
    timeout = cfg.timeout or 30  # wrong: an explicit timeout of 0 becomes 30
    print(f"Connecting with timeout={timeout}s")
```

**Better:**

```python
class Config:
    timeout: int | None = None

def connect(cfg: Config) -> None:
    timeout = cfg.timeout if cfg.timeout is not None else 30  # only None replaced
    print(f"Connecting with timeout={timeout}s")
```

---

### Pattern: Deep nesting with repeated `is not None` checks

```python
from typing import Any

def get_city(obj: dict[str, Any] | None) -> str:
    if obj is not None:
        a = obj.get("a")
        if a is not None:
            b = a.get("b")
            if b is not None:
                c = b.get("c")
                if c is not None:
                    return c
    return "UNK"
```

**Better:**

```python
from typing import Any

def get_city(obj: dict[str, Any] | None) -> str:
    return (obj or {}).get("a", {}).get("b", {}).get("c", "UNK")
```

---

### Pattern: Returning `None` from every layer instead of raising

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str

def find_user(id: int) -> User | None:
    ...

# Every caller repeats the same error handling
def process_user(id: int) -> None:
    user = find_user(id)
    if user is None:
        raise KeyError(f"User {id} not found")  # duplicated at every call site
    print(user.name)
```

**Better:**

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str

def find_user(id: int) -> User:
    ...  # raises KeyError if not found

def process_user(id: int) -> None:
    user = find_user(id)  # error path centralized inside find_user
    print(user.name)
```

---

### Pattern: Using `Any` to bypass nullability checks

```python
import json
from typing import Any

def parse_json(s: str) -> Any:
    return json.loads(s)

def get_display(user: Any) -> str:
    return user.name.upper()  # no checker help — AttributeError if user is None
```

**Better:**

```python
import json
from typing import TypedDict

class UserData(TypedDict, total=False):
    name: str
    email: str

def parse_json_safe(s: str) -> UserData:
    return json.loads(s)

def get_name(data: UserData) -> str:
    return data.get("name") or "Anonymous"
```

The typed shape makes the checker enforce `None`/absence handling at every access.

---

### Pattern: Missing return annotations allowing silent `None` returns

```python
# expect-error
def compute(value: int):  # missing return annotation — inferred as int | None
    if value > 0:
        return value * 2
    # falls through, implicitly returning None

result = compute(-1)
print(result + 10)  # error: Operator "+" not supported for "None"
```

**Better:**

```python
def compute(value: int) -> int | None:
    if value > 0:
        return value * 2

result = compute(-1)
if result is not None:
    print(result + 10)
```

The explicit return type forces every caller to handle the `None` case.
