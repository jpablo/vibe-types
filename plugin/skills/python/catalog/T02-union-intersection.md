# Union and Literal Types

## What it is

`Union[X, Y]` (or the shorthand `X | Y` from Python 3.10) declares that a value may be any one of several types. The type checker requires you to narrow the union before performing type-specific operations. `Literal["a", "b"]` (PEP 586, Python 3.8) narrows the *value space* rather than the *type space*: a `Literal["GET", "POST"]` parameter accepts only those two specific string values, not any `str`. Together, Union and Literal types let you model sum types and closed value sets that the checker can verify exhaustively.

**Since:** `Union` — Python 3.5 (PEP 484); `Literal` — Python 3.8 (PEP 586); `X | Y` syntax — Python 3.10 (PEP 604)

## What constraint it enforces

**A value must belong to one of the declared types (Union) or equal one of the declared literal values (Literal); the checker rejects values outside the set and requires narrowing before type-specific access.**

For Unions, calling a method that only exists on one branch without an `isinstance` check is an error. For Literals, passing a string that is not in the declared set is an error. When combined with exhaustiveness checking [-> [catalog/14](T34-never-bottom.md)], the checker can prove that all cases are handled.

## Minimal snippet

```python
from typing import Literal, Union


def area(shape: Union[str, int]) -> str:
    return shape.upper()  # error: Item "int" of "str | int" has no attribute "upper"


def method(verb: Literal["GET", "POST"]) -> None: ...

method("GET")      # OK
method("DELETE")   # error: Argument 1 has incompatible type "str"; expected "Literal['GET', 'POST']"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Basic annotations** [-> [catalog/01](T13-null-safety.md)] | `Optional[X]` is `Union[X, None]`. Every Union builds on the basic annotation layer. |
| **Enums** [-> [catalog/05](T01-algebraic-data-types.md)] | Enums provide a named, closed set of values — often a better alternative to `Literal` for domain concepts that need methods or rich behavior. |
| **TypeGuard / narrowing** [-> [catalog/13](T14-type-narrowing.md)] | `isinstance`, `is`, and custom type guards narrow Union members inside branches. |
| **Never / exhaustiveness** [-> [catalog/14](T34-never-bottom.md)] | After narrowing every branch of a Union, the remaining type is `Never`. An `assert_never()` call proves all cases are covered. |
| **TypedDict** [-> [catalog/03](T31-record-types.md)] | `Literal` types are often used as discriminator fields in tagged-union patterns with TypedDicts. |

## Gotchas and limitations

1. **`Union[X, Y]` is not a tagged union.** Python does not attach a tag; you must use `isinstance()`, `type()`, or structural checks to narrow. This is more verbose than Rust `enum` or TypeScript discriminated unions.

2. **`Literal` types widen silently.** Assigning a `Literal["GET"]` to a `str` variable widens it to `str`, losing the literal information. To preserve it, annotate explicitly:

   ```python
   verb: Literal["GET"] = "GET"    # OK — stays Literal["GET"]
   verb2: str = "GET"              # widened to str
   ```

3. **`Literal` only works with `int`, `str`, `bytes`, `bool`, `enum` members, and `None`.** You cannot write `Literal[3.14]` or `Literal[(1, 2)]`.

4. **Exhaustiveness is not enforced by default.** mypy does not flag unhandled Union branches unless you explicitly use `assert_never()` or enable the `warn_unreachable` option. pyright's `reportMatchNotExhaustive` setting controls this for `match` statements.

5. **`X | Y` syntax requires Python 3.10 at runtime.** For earlier versions, use `Union[X, Y]` or add `from __future__ import annotations` for annotation-only contexts.

6. **Checker divergence on `Literal` enums.** mypy and pyright differ slightly in how they handle `Literal[MyEnum.A]` — pyright infers literal enum types more aggressively.

## Beginner mental model

Think of `Union[A, B]` as a **package that could contain either item A or item B** — you must open it and check which one you got before using it. `Literal["GET", "POST"]` is like a **combo lock that only accepts specific codes** — anything else is rejected immediately. Together, they give you the ability to say "this value is one of a known set" and have the checker verify it.

## Example A — Union type with isinstance narrowing

```python
def double(value: int | str) -> int | str:
    if isinstance(value, int):
        return value * 2         # OK — narrowed to int
    else:
        return value + value     # OK — narrowed to str


result = double(5)               # OK
result = double("ab")            # OK
result = double([1, 2])          # error: Argument 1 has incompatible type "list[int]"
```

Without the `isinstance` check, calling `value * 2` would be an error because `str.__mul__` and `int.__mul__` have different semantics.

## Example B — Literal type for restricted string values

```python
from typing import Literal
import urllib.request


HttpMethod = Literal["GET", "POST", "PUT", "DELETE"]


def fetch(url: str, method: HttpMethod) -> bytes:
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req) as resp:
        return resp.read()                              # OK


fetch("https://example.com", "GET")      # OK
fetch("https://example.com", "POST")     # OK
fetch("https://example.com", "PATCH")    # error
# mypy:    error: Argument 2 has incompatible type "str"; expected
#          "Literal['GET', 'POST', 'PUT', 'DELETE']"
# pyright: error: Argument of type "Literal['PATCH']" cannot be assigned
#          to parameter "method" of type "Literal['GET', 'POST', 'PUT', 'DELETE']"


# Exhaustive handling with match/case (Python 3.10+)
from typing import assert_never

def describe(method: HttpMethod) -> str:
    match method:
        case "GET":
            return "Read"
        case "POST":
            return "Create"
        case "PUT":
            return "Update"
        case "DELETE":
            return "Remove"
        case _ as unreachable:
            assert_never(unreachable)   # proves all cases covered
```

## Common type-checker errors and how to read them

### Attribute access on Union without narrowing

```
# mypy
error: Item "int" of "str | int" has no attribute "upper"

# pyright
error: "upper" is not a known attribute of "int"
```

**Cause:** You accessed an attribute that exists on one Union member but not the other.
**Fix:** Add an `isinstance` check or use a common protocol. Only access attributes shared by all members, or narrow first.

### Literal mismatch

```
# mypy
error: Argument 1 to "f" has incompatible type "str";
       expected "Literal['a', 'b']"

# pyright
error: Argument of type "Literal['c']" cannot be assigned
       to parameter of type "Literal['a', 'b']"
```

**Cause:** The value passed is not one of the allowed literals.
**Fix:** Pass one of the declared values, or widen the `Literal` type to include the new value.

### Incompatible return in Union function

```
# mypy
error: Incompatible return value type (got "float", expected "int | str")

# pyright
error: Type "float" is not assignable to type "int | str"
```

**Cause:** The returned value does not match any member of the Union return type.
**Fix:** Return a value of a type included in the Union, or add the new type to the return annotation.

### Missing narrowing for None in Union

```
# mypy
error: Item "None" of "int | None" has no attribute "__add__"

# pyright
error: Operator "+" not supported for types "int | None" and "int"
```

**Cause:** `None` is one of the Union members and was not narrowed away.
**Fix:** Check `if value is not None:` before the operation. This is the same pattern as `Optional` narrowing from [-> [catalog/01](T13-null-safety.md)].

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Typing function signatures with precise input/output types.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Data validation pipelines where inputs may be multiple types.
- [-> UC-03](../usecases/UC03-exhaustiveness.md) — Database results that may return None.
- [-> UC-08](../usecases/UC08-error-handling.md) — Union result types encode success/error alternatives in return types.

## When to Use It

**Use `Union` types when:**
- Modeling mutually exclusive states (`Result[T, E]`, `Status = Literal["loading", "success", "error"]`)
- A function can accept multiple distinct types
- You need exhaustive handling via `assert_never()`
- Representing optional values (`T | None`)
- Encoding return types that may produce different shapes

**Use `Literal` types when:**
- Restricting parameters to a specific set of values (`HttpMethod = Literal["GET", "POST"]`)
- Creating type-safe string/number constants that the checker verifies
- Building discriminated unions with TypedDicts
- You need compile-time rejection of invalid enum-like values

## When Not to Use It

**Avoid `Union` types when:**
- Members share common structure — use a base protocol instead
- You have more than ~5 members — the type becomes unwieldy to narrow
- All members have the same properties — just use the common type
- You're modeling hierarchical relationships — consider dataclasses or inheritance

**Avoid `Literal` types when:**
- The set of values is open-ended — use `str`, `int`, or a custom class
- Values need methods or behavior — use enums or dataclasses instead
- The literal set grows frequently — maintenance becomes tedious
- You need to serialize/deserialize — `Literal` is a type-checking tool only

## Antipatterns When Using It

### Union: Union of Unions Without Discriminant

```python
# ❌ Narrowing requires checking every variant
class A(TypedDict):
    kind: Literal["a"]
    x: int

class B(TypedDict):
    kind: Literal["b"]
    y: str

class C(TypedDict):
    kind: Literal["c"]
    z: bool

type Shape = A | B | C  # 3 variants to narrow

def process(s: Shape) -> None:
    if s["kind"] == "a":
        ...  # OK
    elif s["kind"] == "b":
        ...  # OK
    elif s["kind"] == "c":
        ...  # OK
    else:
        assert_never(s["kind"])  # required for exhaustiveness
```

The manual `else` branch is verbose; Python's `match` with `assert_never` is preferred (Example B above).

### Union: Overly Broad Member Types

```python
# ❌ Common properties don't exist
type BadResponse = dict | list | str

def handle(r: BadResponse) -> None:
    r.get("msg")  # error: Item "list" of "dict | list | str" has no attribute "get"
```

**Fix:** Use TypedDicts with a common discriminator:

```python
type StatusResponse = TypedDict("StatusResponse", {"type": Literal["status"], "code": int})
type ErrorResponse = TypedDict("ErrorResponse", {"type": Literal["error"], "msg": str})

type Response = StatusResponse | ErrorResponse
```

### Union: Missing Narrowing Before Access

```python
# ❌ Attribute access without narrowing
def double(value: int | str) -> int | str:
    return value * 2  # OK for both
    return value.upper()  # error: Item "int" has no attribute "upper"
```

**Fix:** Always narrow with `isinstance` before accessing type-specific attributes (Example A above).

### Literal: Widening Without Explicit Annotation

```python
# ❌ Literal information is lost
verb = "GET"  # inferred as str, not Literal["GET"]
method(verb)  # error: expected Literal["GET", "POST"]
```

**Fix:** Annotate explicitly or use `const`-like patterns:

```python
verb: Literal["GET"] = "GET"  # OK — stays Literal["GET"]
```

### Literal: Using Literal for Complex Values

```python
# ❌ Literal only works with int, str, bytes, bool, enum, None
type Invalid = Literal[3.14]           # error: Invalid literal type
type Invalid2 = Literal[(1, 2)]        # error: Invalid literal type
type Invalid3 = Literal[{"key": "val"]} # error: Invalid literal type
```

**Fix:** Use a dataclass or TypedDict for complex literal-like structures.

### Literal: Large Literal Sets

```python
# ❌ Tedious to maintain, hard to read
type AllStates = Literal[
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL",
    "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA",
    # ... continues for 50 states
]
```

**Fix:** Use an enum or a dataclass with validation:

```python
from enum import Enum

class State(str, Enum):
    AL = "AL"
    AK = "AK"
    # ...
```

## Antipatterns with Other Techniques

### Using `Any` Instead of Unions

```python
# ❌ No type safety
def process(x: Any) -> None:
    if isinstance(x, str):
        print(x.upper())
    # Type checker can't help; errors may slip through
```

**Fix:** Use explicit unions with narrowing:

```python
def process(x: str | int) -> None:
    if isinstance(x, str):
        print(x.upper())
    else:
        print(x * 2)
```

### Using `Optional` When `None` Semantics Are Unclear

```python
# ❌ Silent failures, unclear intent
type SearchResult = Optional[str]  
# Could mean: not found, error, or empty result — ambiguous
```

**Fix:** Use a union that captures the semantics:

```python
type SearchResult = str | None | Literal["not_found"]
# Explicitly captures: found, cancelled, not_found
```

### Using Nested Optional/Union When a Result Type Fits

```python
# ❌ Hard to read, nested None checks
def divide(a: float, b: float) -> Optional[Optional[float]]:
    if b == 0:
        return None
    ...
```

**Fix:** Use a Result-like union type:

```python
type DivideResult = Literal[{"ok": True, "value": float}] | Literal[{"ok": False, "error": str}]

def divide(a: float, b: float) -> DivideResult:
    if b == 0:
        return {"ok": False, "error": "division by zero"}
    return {"ok": True, "value": a / b}
```

### Using Base Class Instead of Union for Mutually Exclusive States

```python
# ❌ Inheritance doesn't express mutual exclusivity
class Response:
    ...

class SuccessResponse(Response):
    def __init__(self, value): ...

class ErrorResponse(Response):
    def __init__(self, error): ...

# Both can exist at runtime; type checker can't prove exhaustiveness
```

**Fix:** Use a union of TypedDicts for compile-time exhaustiveness:

```python
type Response = SuccessResponse | ErrorResponse

def handle(r: Response) -> None:
    if r["type"] == "success":
        ...  # narrowed to SuccessResponse
    else:
        assert_never(r["type"])  # proves all cases covered
```

### Using Optional Properties Instead of Union

```python
# ❌ Silent failures, unclear intent
type Bad = TypedDict("Bad", {
    "value": int,
    "error": Optional[str],
    total=False  # both can exist, or neither — unclear semantics
})
```

**Fix:** Use a union for explicit one-or-the-other semantics:

```python
type Good = TypedDict("Good", {"type": Literal["ok"], "value": int}) | \
            TypedDict("Good", {"type": Literal["error"], "error": str})
# Exactly one variant must exist — enforced by the type checker
```

### Using Runtime Checks Instead of Literal Types

```python
# ❌ Runtime errors possible
def http_verb(v: str) -> None:
    if v not in ("GET", "POST", "PUT", "DELETE"):
        raise ValueError(f"Invalid verb: {v}")
    ...
```

**Fix:** Use `Literal` for compile-time safety:

```python
type HttpMethod = Literal["GET", "POST", "PUT", "DELETE"]

def http_verb(v: HttpMethod) -> None:
    ...  # No runtime check needed; invalid values rejected at compile time
```

## Source anchors

- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/) — Union
- [PEP 586 — Literal Types](https://peps.python.org/pep-0586/)
- [PEP 604 — Allow writing union types as X | Y](https://peps.python.org/pep-0604/)
- [typing spec — Union types](https://typing.readthedocs.io/en/latest/spec/concepts.html#union-types)
- [typing spec — Literal types](https://typing.readthedocs.io/en/latest/spec/literal.html)
- [mypy — Literal types](https://mypy.readthedocs.io/en/stable/literal_types.html)
