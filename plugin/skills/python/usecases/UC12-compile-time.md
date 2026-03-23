# Compile-Time Checking (via Static Type Checkers)

## The constraint

Errors that would surface only at runtime must be caught before execution by
running a static type checker (mypy, pyright) in strict mode. The checker
acts as a compile-time pass for Python.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Strict mode (`--strict`) | Disallow implicit `Any`, untyped defs, and other holes | [-> T47](../catalog/T47-gradual-typing.md) |
| `reveal_type()` | Inspect what the checker infers at a specific expression | [-> T47](../catalog/T47-gradual-typing.md) |
| `type: ignore` | Suppress a known false positive on a single line | [-> T47](../catalog/T47-gradual-typing.md) |
| `Final` | Prevent reassignment; checker folds the value at check time | [-> T32](../catalog/T32-immutability-markers.md) |
| `assert_never` | Enforce exhaustiveness — unreachable code is a type error | [-> T34](../catalog/T34-never-bottom.md) |

## Patterns

### A — Enabling strict mode

Strict mode turns off permissive defaults. In mypy, `--strict` enables flags
like `--disallow-untyped-defs`, `--disallow-any-generics`,
`--warn-return-any`, and `--no-implicit-optional`.

```toml
# pyproject.toml — mypy strict mode
[tool.mypy]
strict = true

# pyproject.toml — pyright strict mode
[tool.pyright]
typeCheckingMode = "strict"
```

```python
# With --strict, this is an error:
def add(a, b):        # error: Function is missing type annotations
    return a + b

# Must annotate:
def add(a: int, b: int) -> int:
    return a + b
```

### B — `reveal_type()` for debugging inferred types

`reveal_type()` is a special form that the checker interprets at check time.
It prints the inferred type without affecting runtime behavior (Python 3.11+
has a built-in `reveal_type`; earlier versions need the checker's built-in).

```python
from typing import reveal_type

x = [1, 2, 3]
reveal_type(x)          # mypy: "list[int]"
                        # pyright: "list[int]"

d = {"a": 1, "b": "two"}
reveal_type(d)          # "dict[str, int | str]"

def fetch(url: str) -> bytes | None: ...

result = fetch("https://example.com")
reveal_type(result)     # "bytes | None"

if result is not None:
    reveal_type(result) # "bytes" — narrowed
```

### C — Targeted `type: ignore` for false positives

When the checker flags code you know is correct, suppress the specific error
with `type: ignore[error-code]`. Always use the error code to document *why*.

```python
import ctypes

# mypy cannot verify ctypes attribute access:
libc = ctypes.CDLL("libc.so.6")
libc.printf(b"hello\n")           # type: ignore[attr-defined]  # ctypes dynamic attr

# Suppress only the specific error — other errors on this line are still checked
from typing import cast

raw: object = "hello"
s: str = cast(str, raw)           # OK — cast is the typed escape hatch
s2: str = raw                     # error: Incompatible types
```

### D — `assert_never` for exhaustiveness at check time

`assert_never` makes the checker verify that a `match` or `if/elif` chain
handles all variants. Adding a new variant without updating the handler
becomes a check-time error.

```python
from typing import assert_never, Literal

type Direction = Literal["north", "south", "east", "west"]

def move(d: Direction) -> tuple[int, int]:
    match d:
        case "north": return (0, 1)
        case "south": return (0, -1)
        case "east":  return (1, 0)
        case "west":  return (-1, 0)
        case _ as unreachable:
            assert_never(unreachable)  # error if any case is missing
```

## Tradeoffs

| Tool | Strength | Weakness |
|---|---|---|
| **`--strict` mode** | Catches implicit `Any`, missing annotations, untyped defs | Noisy on legacy code; requires gradual migration |
| **`reveal_type()`** | Zero-cost debugging of inferred types | Clutters code if left in; some linters warn |
| **`type: ignore`** | Unblocks genuine false positives | Suppresses real errors if overused; hides rot |
| **`assert_never`** | Guarantees exhaustiveness at check time | Requires explicit unreachable branch; slight boilerplate |

## When to use which feature

- **Enable `--strict` mode** from day one on new projects. For legacy code, enable incrementally with per-module overrides.
- **Use `reveal_type()`** during development to verify the checker sees what you expect. Remove before committing.
- **Use `type: ignore[code]`** only for confirmed false positives. Always include the error code so reviewers understand the suppression.
- **Use `assert_never`** in every `match` statement over unions and `Literal` types to make adding new variants a check-time task rather than a runtime bug hunt.

## Source anchors

- [mypy — Command line: --strict](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict)
- [pyright — Configuration: typeCheckingMode](https://microsoft.github.io/pyright/#/configuration?id=typecheckingmode)
- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
- [Python docs — typing.reveal_type](https://docs.python.org/3/library/typing.html#typing.reveal_type)
- [Python docs — typing.assert_never](https://docs.python.org/3/library/typing.html#typing.assert_never)
- [mypy — Error codes](https://mypy.readthedocs.io/en/stable/error_codes.html)
