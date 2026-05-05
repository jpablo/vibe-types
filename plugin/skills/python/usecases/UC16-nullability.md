# Nullability and None Safety

## The constraint

`None` is a distinct value with type `None`. A variable that might be `None` must be annotated as `Optional[T]` (or `T | None`), and the checker enforces that `None` is handled before the value is used as `T`. With `--strict-optional`, mypy rejects implicit `None` coercion.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Null safety / Optional | `T \| None` distinguishes nullable from non-nullable types | [-> catalog/13](../catalog/T13-null-safety.md) |
| Type narrowing | `isinstance`, `is not None`, and `assert` narrow `T \| None` to `T` | [-> catalog/14](../catalog/T14-type-narrowing.md) |
| Union types | `T \| None` is sugar for `Union[T, None]` | [-> catalog/02](../catalog/T02-union-intersection.md) |

## Patterns

### A — Explicit Optional annotation

Annotate nullable parameters and returns with `T | None`.

```python
def find_user(user_id: int) -> str | None:
    if user_id == 1:
        return "Alice"
    return None

name = find_user(1)
# name.upper()       # error: "str | None" has no attribute "upper"

if name is not None:
    name.upper()     # OK — narrowed to str
```

### B — Guard clauses and early return

Narrow `None` away with an early return, allowing the rest of the function to work with the unwrapped type.

```python
def greet(name: str | None) -> str:
    if name is None:
        return "Hello, stranger"
    # From here, name is str
    return f"Hello, {name.upper()}"
```

### C — Default values with `or` pattern

Provide fallback values inline.

```python
def get_timeout(config: dict[str, int]) -> int:
    raw: int | None = config.get("timeout")
    return raw if raw is not None else 30

# Or more concisely with dict.get default:
def get_timeout_v2(config: dict[str, int]) -> int:
    return config.get("timeout", 30)
```

### D — assert for narrowing in strict contexts

Use `assert` to narrow `None` when you know the value is present.

```python
from dataclasses import dataclass

@dataclass
class Response:
    data: str | None
    error: str | None

def unwrap_response(resp: Response) -> str:
    assert resp.data is not None, "Expected data in response"
    return resp.data.strip()   # OK — narrowed to str
```

### E — Strict optional with mypy

With `--strict-optional` (default in `--strict` mode), mypy treats `None` as incompatible with any non-`None` type.

```python
# mypy --strict-optional
def process(value: str) -> str:
    return value.upper()

x: str | None = "hello"
# process(x)            # error: Argument 1 has incompatible type "str | None"; expected "str"

if x is not None:
    process(x)          # OK — narrowed
```

### Untyped Python comparison

Without type annotations, `None` errors surface only at runtime.

```python
# No types
def find_user(user_id):
    if user_id == 1:
        return "Alice"
    # implicit return None

name = find_user(99)
name.upper()    # AttributeError: 'NoneType' object has no attribute 'upper'
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| **T \| None** | Explicit nullability; checker enforces handling | Requires narrowing at every use site; adds verbosity |
| **Guard clause / early return** | Clean control flow; narrows for the rest of the function | Multiple early returns can reduce readability in long functions |
| **assert narrowing** | Concise; communicates invariant | Assertions can be disabled with `-O`; not suitable for untrusted input |
| **--strict-optional** | Catches all implicit None coercion | Requires annotating every nullable value; can be noisy during gradual adoption |

## When to use which feature

- **Always annotate nullability** — use `T | None` rather than bare `T` when `None` is possible. This is the most impactful single typing practice.
- **Use guard clauses** to narrow early and keep the main code path None-free.
- **Use `assert`** only for internal invariants, never for external input validation.
- **Enable `--strict-optional`** (or full `--strict`) in mypy/pyright for new projects; adopt incrementally for existing codebases.

## When to Use It

Use nullability with `T | None` when:

- Values may genuinely be absent (API responses, optional fields, lookups)
- You want static guarantees that absence is handled before use
- Distinguishing between "no value" (`None`) and "empty" (`[]`, `""`, `0`) matters
- A sentinel/dummy value is semantically inappropriate

```python
# API response may be missing data
from dataclasses import dataclass

@dataclass
class ApiResponse:
    user: str | None

def render_user(data: ApiResponse) -> str:
    if data.user is None:
        return "<LoginPrompt />"
    return f"<UserProfile user={data.user} />"  # user is str here
```

---

## When Not to Use It

Avoid explicit nullability when:

- The value always exists by design (use `T`, not `T | None`)
- You can use empty collections instead of `None` for "no items"
- A sentinel/dummy value is more appropriate than `None`
- The domain doesn't conceptually include "absence"

```python
# Bad: None when structure guarantees presence
def get_user_name(user: dict[str, str]) -> str | None:
    return user["name"] or None  # user["name"] always exists if user is valid


# Good: return the actual type
def get_user_name(user: dict[str, str]) -> str:
    return user["name"]  # type is str


# Bad: None array
tags: list[str] | None = None


# Good: empty list
tags: list[str] = []


# Good: empty dict for "no extras"
def get_config() -> dict[str, int]:
    return {}  # no extras
```

---

## Antipatterns When Using It

### 1. Using `or None` to annotate non-nullable returns

```python
# Bad: function never returns None but type lies
def get_count(items: list[int]) -> int | None:
    return len(items) or None  # len() never returns None


# Good: return the actual type
def get_count(items: list[int]) -> int:
    return len(items)  # type is int


# Bad: or None with falsy check loses valid values
def get_value(x: int) -> int | None:
    return x or None  # x = 0 → None (wrong!)


# Good: only return None for genuine absence
def get_value(x: int | None) -> int | None:
    return x  # preserves 0
```

### 2. Using `or` instead of explicit None check with defaults

```python
# Bad: 0, "", False all become default
count = input_count or 10  # input_count = 0 → 10 (wrong!)
name = input_name or "Anonymous"  # "" → "Anonymous" (wrong!)


# Good: only None triggers default
count = input_count if input_count is not None else 10  # 0 → 0 (correct)
name = input_name if input_name is not None else "Anonymous"  # "" → "" (correct)
```

### 3. Deep nesting with `assert` on each level

```python
# Bad: no safety, runtime crash if assertion fails
def get_zip(user: User | None) -> str:
    assert user is not None, "User required"
    assert user.address is not None, "Address required"
    assert user.address.city is not None, "City required"
    return user.address.city.zip  # crashes if any assertion fails


# Good: guard clause with clear error
def get_zip(user: User | None) -> str | None:
    if user is None:
        return None
    if user.address is None:
        return None
    if user.address.city is None:
        return None
    return user.address.city.zip
```

### 4. Using `typing.Any` to escape nullability

```python
# Bad: loses all type safety
from typing import Any


def get_data() -> Any:
    return fetch_data() or None  # Any | None → Any


# Good: preserve the type
def get_data() -> Data | None:
    return fetch_data() or None
```

---

## Antipatterns Where Nullability Helps

### 1. Default parameters that hide contracts

```python
# Bad: default hides the fact that user may be absent
def greet(user: dict[str, str] = {"name": "Guest"}) -> str:
    return f"Hello, {user['name']}"


# Good: absence is explicit
def greet(user: dict[str, str] | None) -> str:
    name = user.get("name") if user is not None else "Guest"
    return f"Hello, {name}"
```

### 2. Throwing for absence instead of returning `None`

```python
# Bad: caller needs try/except for normal absence
USERS = [{"id": "u1", "name": "Alice"}]


def find_user(id: str) -> dict[str, str]:
    user = next((u for u in USERS if u["id"] == id), None)
    if user is None:
        raise ValueError("Not found")
    return user


def render(id: str) -> str:
    try:
        user = find_user(id)
        return f"<Profile user={user} />"
    except ValueError:
        return "<NotFound />"


# Good: type expresses absence; caller chooses handling
def find_user(id: str) -> dict[str, str] | None:
    return next((u for u in USERS if u["id"] == id), None)


def render(id: str) -> str:
    user = find_user(id)
    if user is None:
        return "<NotFound />"
    return f"<Profile user={user} />"
```

### 3. Accessing attributes without checking for None

```python
# Bad: downstream code crashes at runtime
class Order:
    def __init__(self, shipping_address: "Address | None"):
        self.shipping_address = shipping_address


class Address:
    def __init__(self, city: str):
        self.city = city


order = Order(shipping_address=Address(city="NYC"))
city = order.shipping_address.city
document_title = city.upper()  # OK here

# But if shipping_address is None:
order = Order(shipping_address=None)
city = order.shipping_address.city  # AttributeError at runtime!
```

With type checking:

```python
# Good: type forces handling
from __future__ import annotations

class Order:
    def __init__(self, shipping_address: Address | None) -> None:
        self.shipping_address = shipping_address


order: Order | None = Order(shipping_address=Address(city="NYC"))
if order is not None and order.shipping_address is not None:
    city = order.shipping_address.city  # safe
    document_title = city.upper()
else:
    city = "Unknown"
    document_title = city.upper()
```

### 4. Mutating optionals without checks

```python
# Bad: crashes at runtime if title is None
class Draft:
    def __init__(self, title: str | None) -> None:
        self.title = title


draft = Draft(title=None)
draft.title = draft.title.upper()  # AttributeError: 'NoneType' object has no attribute 'upper'


# Good: type checker catches it before runtime
def capitalize_title(draft: Draft) -> None:
    if draft.title is None:
        return
    draft.title = draft.title.upper()  # safe
```

---

## Source anchors

- [PEP 484 — Optional type](https://peps.python.org/pep-0484/#union-types)
- [PEP 604 — X | Y syntax](https://peps.python.org/pep-0604/)
- [mypy — Optional types and None](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#optional-types-and-the-none-type)
- [mypy — Strict optional](https://mypy.readthedocs.io/en/stable/config_file.html#confval-strict_optional)
