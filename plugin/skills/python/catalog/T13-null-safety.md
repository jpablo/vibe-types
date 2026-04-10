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
    return 42  # error: Incompatible return value type (got "int", expected "str")

x: int = "hello"  # error: Incompatible types in assignment (got "str", expected "int")

def maybe(val: str | None) -> int:
    return len(val)  # error: Argument 1 to "len" has incompatible type "str | None"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Union / Literal** [-> [catalog/02](T02-union-intersection.md)] | `Union[X, Y]` and `Literal["a"]` extend basic annotations to multi-type and value-level constraints. |
| **TypeGuard / TypeIs** [-> [catalog/13](T14-type-narrowing.md)] | Narrowing functions refine `Optional` and `Union` annotations inside conditional branches. |
| **Gradual typing** [-> [catalog/20](T47-gradual-typing.md)] | Unannotated code defaults to `Any`, which is compatible with every type. Adding annotations is how you opt into stricter checking. |
| **Final / ClassVar** [-> [catalog/12](T32-immutability-markers.md)] | `Final[int]` combines a basic annotation with an immutability constraint. |
| **TypedDict** [-> [catalog/03](T31-record-types.md)] | TypedDict values are annotated with the same basic types described here. |

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
    return "unknown"             # error

# mypy:    error: Incompatible return value type (got "str", expected "int")
# pyright: error: Type "str" is not assignable to type "int"
```

The fix depends on intent. If "unknown" is a valid case, change the return type to `int | str` or raise an exception instead.

## Example B — Optional parameter requiring None check

```python
from __future__ import annotations


def first_char(text: str | None) -> str:
    # Without narrowing, the checker rejects attribute access:
    # return text[0]  # error: Value of type "str | None" is not indexable

    if text is None:
        return ""                # OK — early return handles the None case
    return text[0]               # OK — type narrowed to str after None check


# Alternative: assert-based narrowing
def first_char_v2(text: str | None) -> str:
    assert text is not None      # narrows type to str
    return text[0]               # OK
```

## Common type-checker errors and how to read them

### Incompatible return value type

```
# mypy
error: Incompatible return value type (got "int", expected "str")

# pyright
error: Type "int" is not assignable to type "str"
```

**Cause:** The value you return does not match the declared `-> T` annotation.
**Fix:** Either change the return value or broaden the return annotation.

### Incompatible types in assignment

```
# mypy
error: Incompatible types in assignment (got "str", expected "int")

# pyright
error: Type "str" is not assignable to type "int"
```

**Cause:** You assigned a value that does not match the variable's declared type.
**Fix:** Change the assignment or the annotation. If the variable should accept multiple types, use a `Union`.

### Item of Optional has no attribute

```
# mypy
error: Item "None" of "str | None" has no attribute "upper"

# pyright
error: "upper" is not a known member of "None"
```

**Cause:** You accessed an attribute on a value that might be `None`.
**Fix:** Narrow the type first with `if x is not None:`, `assert x is not None`, or use a default: `(x or "").upper()`.

### Missing return statement

```
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
  from typing import Optional

  @dataclass
  class User:
      name: str
      email: Optional[str]

  def get_user(id: int) -> Optional[User]:
      ...
  ```

- **Database queries** — lookups that may return no result.
  ```python
  def find_user(id: int) -> Optional[User]:
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
  ```

- **Deep nested access** — chain of lookups where intermediate values may be absent.
  ```python
  def get_city(address: Optional[dict]) -> str:
      country = address.get("country") if address else None
      city = country.get("city") if country else None
      return city or "Unknown"
  ```

- **Defaulting absent values** — using `or` for falsy-absent semantics, or explicit checks for true null-only defaults.
  ```python
  value = maybe_int() or 42  # 0, "", False become 42
  value = maybe_int() if maybe_int() is not None else 42  # only None becomes 42
  ```

## When not to use it

- **When absence is an error** — failing fast is clearer than propagating `None`.
  ```python
  # Instead of:
  def get_admin() -> Optional[User]:
      ...

  admin = get_admin() or default_admin()  # hides the error

  # Use:
  def get_admin() -> User:
      ...

  admin = get_admin()  # raises KeyError/NotFound if missing
  ```

- **When a discrimininated union is more expressive** — `None` loses intent and context.
  ```python
  # Instead of:
  def parse(s: str) -> int | None:
      ...

  # Use:
  from dataclasses import dataclass

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
  # Instead of:
  class User:
      tags: list[str] | None = None

  # Use:
  class User:
      tags: list[str] = []  # empty list is meaningful and safe
  ```

- **When using `is not None` assertions without proof** — Python has no non-null assertion operator, but silent assumptions are dangerous.
  ```python
  # Don't:
  def render(name: str | None) -> str:
      return f"<h1>{name.upper()}</h1>"  # crashes if name is None

  # Do:
  def render(name: str | None) -> str:
      if name is None:
          return ""
      return f"<h1>{name.upper()}</h1>"
  ```

## Antipatterns when using null safety

### Pattern: Calling `.get()` without handling `None` return

```python
def get_user_name(users: dict[int, User], id: int) -> str:
    user = users.get(id)
    return user.name  # type error: "None" has no attribute "name"
```

**Better:**

```python
def get_user_name(users: dict[int, User], id: int) -> str:
    user = users.get(id)
    if user is None:
        raise KeyError(f"User {id} not found")
    return user.name
```

---

### Pattern: Boolean coercion for optional params

```python
class Config:
    timeout: int | None = None

def connect(cfg: Config) -> None:
    timeout = cfg.timeout or 30  # wrong: 0 treated as absent
```

**Better:**

```python
def connect(cfg: Config) -> None:
    timeout = cfg.timeout if cfg.timeout is not None else 30  # only None replaced
```

---

### Pattern: Deep nesting with repeated `is not None` checks

```python
def get_city(obj: dict | None) -> str:
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
def get_city(obj: dict | None) -> str:
    return (obj or {}).get("a", {}).get("b", {}).get("c", "UNK")
```

---

### Pattern: Mixing `None` and exceptions inconsistently

```python
def find_user(id: int) -> User | None:
    ...

def process_user(id: int) -> None:
    user = find_user(id)
    if user is None:
        raise RuntimeError(f"User {id} not found")
    # duplicate error handling everywhere
```

**Better:**

```python
def find_user(id: int) -> User:
    ...  # raises KeyError if not found

def process_user(id: int) -> None:
    user = find_user(id)  # error path centralized
```

---

### Pattern: Using `Any` to bypass nullability checks

```python
from typing import Any

def parse_json(s: str) -> Any:
    import json
    return json.loads(s)

def get_name(data: Any) -> str:
    return data["name"]  # no type checking at all
```

**Better:**

```python
from typing import TypedDict

class UserData(TypedDict, total=False):
    name: str
    email: str

def parse_json(s: str) -> UserData:
    import json
    return json.loads(s)

def get_name(data: UserData) -> str:
    return data.get("name") or "Anonymous"
```

## Antipatterns where null safety fixes code

### Pattern: Silent failures with untyped code

```python
# Python without type annotations
def get_display(user):
    return user.name.upper()  # AttributeError if user is None
```

**Better with null safety:**

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str

def get_display(user: User | None) -> str:
    return user.name.upper() if user else "Anonymous"
```

The type checker ensures you handle `None` at every call site.

---

### Pattern: Defensive `is not None` checks scattered across code

```python
def render_profile(user: dict | None) -> str:
    if user is None:
        return "No user"
    profile = user.get("profile")
    if profile is None:
        return "No profile"
    avatar = profile.get("avatar")
    if avatar is None:
        return "No avatar"
    return avatar["url"]
```

**Better with null safety:**

```python
def render_profile(user: dict | None) -> str:
    return user.get("profile", {}).get("avatar", {}).get("url", "No avatar")
```

Nullability is expressed through types, not scattered guards.

---

### Pattern: Implicit `None` propagation in method chains

```python
class Parser:
    def parse(self, s: str) -> list[dict] | None:
        ...

    def first_name(self, s: str) -> str:
        items = self.parse(s)
        return items[0]["name"]  # IndexError or TypeError at runtime
```

**Better with null safety:**

```python
class Parser:
    def parse(self, s: str) -> list[dict]:
        ...  # empty list instead of None

    def first_name(self, s: str) -> str:
        items = self.parse(s)
        return items[0].get("name") if items else "Unknown"
```

Empty collections are preferred over `None` for collections.

---

### Pattern: Missing return types allowing silent `None` returns

```python
def compute(value: int):
    if value > 0:
        return value * 2
    # implicit None returned

result = compute(-1)
print(result + 10)  # TypeError at runtime
```

**Better with null safety:**

```python
def compute(value: int) -> int | None:
    if value > 0:
        return value * 2

result = compute(-1)
if result is not None:
    print(result + 10)
```

The return type forces handling of the `None` case.
