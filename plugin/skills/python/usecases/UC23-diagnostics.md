# Diagnostics (Mypy/Pyright Error Codes)

## The constraint

Type checker diagnostics should be understood, acted upon, and selectively suppressed only with explicit justification. `reveal_type()` exposes inferred types during development, error codes identify specific violations, and `type: ignore[code]` suppresses individual diagnostics with precision.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Gradual typing | `type: ignore` and `Any` allow incremental adoption without blocking the build | [-> catalog/47](../catalog/T47-gradual-typing.md) |
| Null safety | Common errors around `None` handling and optional types | [-> catalog/13](../catalog/T13-null-safety.md) |
| Type narrowing | Understand narrowing-related diagnostics | [-> catalog/14](../catalog/T14-type-narrowing.md) |

## Patterns

### A — reveal_type for inspecting inferred types

Use `reveal_type()` to see what the checker infers at a specific point.

```python
x = [1, 2, 3]
reveal_type(x)  # mypy: Revealed type is "builtins.list[builtins.int]"

d = {"a": 1, "b": "two"}
reveal_type(d)  # mypy: Revealed type is "builtins.dict[builtins.str, builtins.int | builtins.str]"
```

Remove `reveal_type()` calls before committing — they are development-only diagnostics.

### B — Targeted type: ignore with error codes

Suppress specific diagnostics with the error code, not a blanket ignore.

```python
# Bad — blanket suppression hides all errors on this line:
x: int = "hello"  # type: ignore

# Good — suppresses only the specific assignment error:
x: int = "hello"  # type: ignore[assignment]

# Multiple codes when needed:
result = some_func()  # type: ignore[no-untyped-call, assignment]
```

### C — Common mypy error codes and their meaning

```python
from typing import Optional

# [arg-type] — wrong argument type
def greet(name: str) -> str:
    return f"Hello, {name}"

greet(42)                    # error: Argument 1 has incompatible type "int" [arg-type]

# [return-value] — wrong return type
def get_name() -> str:
    return None              # error: Incompatible return value type "None" [return-value]

# [union-attr] — accessing attribute not on all union members
def process(val: str | None) -> str:
    return val.upper()       # error: Item "None" has no attribute "upper" [union-attr]

# [override] — incompatible method override
class Base:
    def method(self, x: int) -> None: ...

class Sub(Base):
    def method(self, x: str) -> None: ...  # error: incompatible type [override]
```

### D — Pyright-specific diagnostics

Pyright uses different error code names but the same underlying checks.

```python
# Pyright strict mode enables additional checks:
# reportUnusedVariable, reportMissingTypeStubs, reportUnnecessaryTypeIgnoreComment

def example() -> None:
    unused = 42              # warning: "unused" is not accessed (reportUnusedVariable)
    x: str = "hello"
    x = "world"             # OK
    y: int = "bad"          # error: Type "str" is not assignable to type "int"
```

### E — Configuration for stricter diagnostics

Enable stricter checking progressively.

```python
# mypy.ini
# [mypy]
# strict = true
# warn_return_any = true
# warn_unused_ignores = true
# enable_error_code = truthy-bool, ignore-without-code

# pyproject.toml (pyright)
# [tool.pyright]
# typeCheckingMode = "strict"
# reportUnnecessaryTypeIgnoreComment = true
```

### Untyped Python comparison

Without a type checker, errors surface only at runtime.

```python
# No checker — errors invisible until execution
def greet(name):
    return f"Hello, {name}"

greet(42)        # runs fine — but probably a bug
greet()          # TypeError at runtime: missing argument
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| **reveal_type()** | Zero-cost exploration of inferred types | Must be removed before commit; no runtime effect |
| **type: ignore[code]** | Precise suppression; documents the exact trade-off | Over-suppression can mask real errors; stale ignores add noise |
| **--strict mode** | Catches the most errors; enforces best practices | Noisy on legacy code; requires significant annotation effort |
| **warn_unused_ignores** | Flags stale `type: ignore` comments | May cause churn when checker versions change |

## When to use which feature

- **Use `reveal_type()`** during development to understand what the checker sees — especially useful for complex generics and overloads.
- **Always use error codes** in `type: ignore` comments — `# type: ignore[assignment]` rather than bare `# type: ignore`.
- **Enable `--strict`** for new projects; adopt individual flags incrementally for existing codebases.
- **Enable `warn_unused_ignores`** so stale suppressions are flagged when the underlying issue is fixed.

## Source anchors

- [mypy — Error codes](https://mypy.readthedocs.io/en/stable/error_codes.html)
- [mypy — reveal_type](https://mypy.readthedocs.io/en/stable/common_issues.html#reveal-type)
- [mypy — type: ignore](https://mypy.readthedocs.io/en/stable/common_issues.html#silencing-type-errors)
- [pyright — Configuration](https://github.com/microsoft/pyright/blob/main/docs/configuration.md)
- [pyright — Error codes](https://github.com/microsoft/pyright/blob/main/docs/configuration.md#type-check-diagnostics-settings)
