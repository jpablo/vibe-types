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

## Source anchors

- [PEP 484 — Optional type](https://peps.python.org/pep-0484/#union-types)
- [PEP 604 — X | Y syntax](https://peps.python.org/pep-0604/)
- [mypy — Optional types and None](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#optional-types-and-the-none-type)
- [mypy — Strict optional](https://mypy.readthedocs.io/en/stable/config_file.html#confval-strict_optional)
