# Escape Hatches

## The constraint

When the type system cannot express a correct program, escape hatches allow the developer to selectively bypass checking. Python's gradual type system provides `Any`, `cast()`, `type: ignore`, and permissive checker flags. Each escape hatch trades static safety for flexibility, and should be used with documented justification.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Gradual typing | `Any` and `type: ignore` allow partial typing without blocking the build | [-> catalog/47](../catalog/T47-gradual-typing.md) |
| Conversions | `cast()` asserts a type without runtime check | [-> catalog/18](../catalog/T18-conversions-coercions.md) |

## Patterns

### A — type: ignore with error codes

Suppress a specific diagnostic on a single line.

```python
import json

data: dict[str, str] = json.loads('{"a": 1}')  # type: ignore[assignment]
# json.loads returns Any; we assert the shape here.
# The error code documents *why* the ignore is needed.
```

Always prefer `type: ignore[code]` over bare `type: ignore` to prevent masking unrelated errors on the same line.

### B — Any for untyped boundaries

Use `Any` at boundaries with untyped libraries or dynamic data.

```python
from typing import Any

def call_external_api(payload: dict[str, Any]) -> Any:
    """Wraps an untyped third-party client."""
    import third_party  # type: ignore[import-untyped]
    return third_party.post(payload)

# Narrow the Any as soon as possible:
raw: Any = call_external_api({"key": "value"})
if isinstance(raw, dict):
    name: str = raw.get("name", "unknown")  # narrowed from Any
```

### C — cast() for asserting types without runtime cost

`cast()` tells the checker to treat a value as a specific type. No runtime check is performed.

```python
from typing import cast

def get_config_value(config: dict[str, object], key: str) -> str:
    value = config[key]
    # We know this key always holds a string, but the dict is typed as object
    return cast(str, value)

# cast() is zero-cost at runtime — it is the identity function.
# Use it when you have knowledge the checker cannot infer.
```

### D — type: ignore[override] for intentional LSP violations

Suppress Liskov Substitution Principle violations when the design intentionally narrows.

```python
from typing import Sequence

class Base:
    def process(self, items: Sequence[int]) -> None: ...

class Strict(Base):
    def process(self, items: list[int]) -> None:  # type: ignore[override]
        # Intentionally narrows parameter from Sequence to list
        items.sort()  # needs list, not Sequence
```

### E — Permissive checker flags for gradual adoption

Relax strictness during migration.

```python
# mypy.ini — per-module overrides for legacy code
# [mypy-legacy_module.*]
# ignore_errors = True
# disallow_untyped_defs = False

# pyright — per-file override
# pyright: reportGeneralTypeIssues=false

# Command-line escape hatch:
# mypy --no-strict-optional legacy_code/
```

### F — object as a safe escape from Any

Prefer `object` over `Any` when you want to accept anything but still get method-level checking.

```python
from typing import Any

def log_any(value: Any) -> None:
    value.nonexistent_method()   # no error — Any disables all checking

def log_object(value: object) -> None:
    # value.nonexistent_method()  # error — object has no such method
    print(str(value))             # OK — object has __str__
```

### Untyped Python comparison

Without a type checker, there is no need for escape hatches — but also no safety net.

```python
# No types — everything is implicitly Any
def process(data):
    return data["key"].upper()   # KeyError or AttributeError at runtime

process(42)  # TypeError at runtime — no static warning
```

## Tradeoffs

| Escape hatch | Strength | Weakness |
|---|---|---|
| **type: ignore[code]** | Precise, per-line suppression; documents the exact trade-off | Stale ignores add noise; can mask new errors if code changes |
| **Any** | Maximum flexibility; untyped code integrates without friction | Disables all checking for that value; errors propagate silently |
| **cast()** | Zero runtime cost; explicit type assertion | No runtime verification — incorrect casts cause silent bugs |
| **--no-strict / per-module ignore** | Enables gradual adoption of typing | Easy to forget to tighten later; large ignore regions become permanent |
| **object** | Safer than `Any`; still accepts all types | Only `object` methods available; explicit narrowing always required |

## When to use which feature

- **Use `type: ignore[code]`** for isolated lines where the checker is wrong or the type system cannot express the correct type.
- **Use `Any`** at boundaries with untyped code — third-party libraries, dynamic deserialization — and narrow it as soon as possible.
- **Use `cast()`** when you have external proof that a value is a specific type and the checker cannot infer it.
- **Use per-module relaxation** during migration; set a deadline to remove each override.
- **Prefer `object` over `Any`** when you need to accept anything but want method-level checking to remain active.

## Source anchors

- [PEP 484 — The Any type](https://peps.python.org/pep-0484/#the-any-type)
- [PEP 484 — Casts](https://peps.python.org/pep-0484/#casts)
- [mypy — Common issues and solutions](https://mypy.readthedocs.io/en/stable/common_issues.html)
- [mypy — type: ignore](https://mypy.readthedocs.io/en/stable/common_issues.html#silencing-type-errors)
- [mypy — Per-module config](https://mypy.readthedocs.io/en/stable/config_file.html#per-module-and-global-options)
