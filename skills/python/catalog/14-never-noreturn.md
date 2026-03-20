# Never and NoReturn

> **Since:** `NoReturn` Python 3.5.4 (PEP 484); `Never` Python 3.11 (PEP 655) | **Backport:** `typing_extensions`

## What it is

`Never` (and its legacy alias `NoReturn`) is the *bottom type* in Python's type system: it has no inhabitants. No value can have type `Never`. This makes it useful in two complementary roles: (1) annotating functions that never return normally — they always raise an exception, call `sys.exit()`, or loop forever — and (2) serving as the identity element in exhaustiveness proofs, where `assert_never(x)` accepts only an argument of type `Never`, proving that every variant in a union has already been handled.

`Never` and `NoReturn` are semantically identical. `NoReturn` was introduced first as a return-type annotation; `Never` was added later as a general-purpose bottom type usable in any position (parameters, variables, return types). Modern code should prefer `Never`.

## What constraint it enforces

**Functions annotated as returning `Never` must not contain any reachable `return` statement or implicit `return None`. Any code after a call to such a function is flagged as unreachable. When used as a parameter type via `assert_never`, it proves that a narrowing chain is exhaustive — if the checker cannot narrow the argument to `Never`, it means a variant is unhandled.**

## Minimal snippet

```python
from typing import Never, assert_never

def fail(msg: str) -> Never:
    raise RuntimeError(msg)

x = fail("boom")
print("after fail")    # error — statement is unreachable

type Shape = int | str

def area(s: Shape) -> float:
    if isinstance(s, int):
        return float(s * s)
    elif isinstance(s, str):
        return 0.0
    else:
        assert_never(s)   # OK — s is narrowed to Never here
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Union narrowing** [-> catalog/02](02-union-literal-types.md) | After narrowing every member of a Union through `isinstance` or `match`/`case`, the remaining type is `Never`. Calling `assert_never` in the `else` branch proves exhaustiveness. |
| **Enum exhaustiveness** [-> catalog/05](05-enums-typing.md) | Matching all members of an Enum in `match`/`case` or `if`/`elif` narrows the remaining type to `Never`. Adding a new member without updating all match sites causes a type error at the `assert_never` call. |
| **TypeGuard / TypeIs** [-> catalog/13](13-typeguard-typeis-narrowing.md) | `TypeIs` narrows both branches, enabling the remainder to eventually reach `Never`. `TypeGuard` only narrows the positive branch, so it cannot drive exhaustiveness proofs by itself. |
| **Callable** [-> catalog/11](11-callable-types-overload.md) | `Callable[..., Never]` describes a callback that never returns — useful for error-handler registries. |

## Gotchas and limitations

1. **`NoReturn` vs `Never` — same semantics, different eras.** `NoReturn` was designed only as a return-type annotation; `Never` is the generalized bottom type. Some older codebases and libraries still use `NoReturn`. The two are interchangeable in return-type position, but only `Never` is appropriate as a parameter or variable type.

   ```python
   from typing import NoReturn, Never

   def old_style() -> NoReturn: ...   # OK — legacy
   def new_style() -> Never: ...      # OK — preferred

   x: Never   # OK
   y: NoReturn # OK technically, but Never is clearer in this position
   ```

2. **A function returning `Never` must not have any reachable `return`.** An implicit `return None` at the end of the function body is also a return. The checker will flag it.

   ```python
   def bad(flag: bool) -> Never:
       if flag:
           raise ValueError("nope")
       # error — implicit return None, but declared Never
   ```

3. **`assert_never` is a runtime function.** At runtime, `assert_never` raises `AssertionError` if reached. It is not purely a static construct — it also serves as a safety net if the type checker is bypassed.

4. **`Never` is a subtype of every type.** This is the defining property of a bottom type. It means a variable of type `Never` can be assigned to anything, but no value can ever have that type. This can confuse beginners who see `Never` appear in `reveal_type` output.

5. **Checkers may differ on unreachable-code reporting.** pyright flags unreachable code after a `Never`-returning call as an error by default; mypy issues a note or warning depending on configuration (`--warn-unreachable`).

6. **`Never` in generic positions.** `list[Never]` is a valid type (an empty list that can never have elements added). This comes up in generic code where an empty container's element type cannot be inferred.

## Beginner mental model

`Never` means **"this can't happen."** If a function returns `Never`, it means the function will never hand control back to you — it will always crash or run forever. If a variable has type `Never` in a branch, it means the checker has proven that branch is impossible to reach. `assert_never` is your way of saying "I believe this branch is impossible — prove me right."

## Example A — assert_never for exhaustive Union handling

```python
from typing import Never, assert_never
from enum import Enum

class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

def hex_code(c: Color) -> str:
    match c:
        case Color.RED:
            return "#ff0000"
        case Color.GREEN:
            return "#00ff00"
        case Color.BLUE:
            return "#0000ff"
        case _ as unreachable:
            assert_never(unreachable)   # OK — all cases covered

# Now add a new color without updating hex_code:
# class Color(Enum):
#     RED = "red"
#     GREEN = "green"
#     BLUE = "blue"
#     YELLOW = "yellow"    # new member
#
# hex_code will now error:
#   error: Argument of type "Color" is not assignable to "Never"
#   (because Color.YELLOW is unhandled)
```

The same pattern with `if`/`elif`:

```python
type Result = int | str | float

def summarize(r: Result) -> str:
    if isinstance(r, int):
        return f"integer: {r}"
    elif isinstance(r, str):
        return f"string: {r}"
    elif isinstance(r, float):
        return f"float: {r}"
    else:
        assert_never(r)   # OK — r is Never

# Forget the float branch:
def summarize_broken(r: Result) -> str:
    if isinstance(r, int):
        return f"integer: {r}"
    elif isinstance(r, str):
        return f"string: {r}"
    else:
        assert_never(r)   # error — r is float, not Never
```

## Example B — NoReturn for error-raising utility functions

```python
from typing import Never
import sys

def fatal(message: str, code: int = 1) -> Never:
    """Print an error message and terminate the program."""
    print(f"FATAL: {message}", file=sys.stderr)
    sys.exit(code)

def load_config(path: str) -> dict[str, str]:
    import json
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        fatal(f"Config file not found: {path}")
        # No return needed — checker knows fatal() never returns.
        # Any code here would be flagged as unreachable.
    except json.JSONDecodeError as e:
        fatal(f"Invalid JSON in {path}: {e}")

# The checker sees that both except branches call fatal() -> Never,
# and the try branch returns dict[str, str], so the overall return
# type is dict[str, str]. No need for a fallback return.
```

Using `Never` as a callback type:

```python
from collections.abc import Callable
from typing import Never

type ErrorHandler = Callable[[str], Never]

def with_error_handler(handler: ErrorHandler) -> None:
    try:
        risky_operation()
    except Exception as e:
        handler(str(e))
        # Checker knows this line is unreachable because handler returns Never
        print("this never prints")  # error — unreachable

def panic(msg: str) -> Never:
    raise SystemExit(msg)

with_error_handler(panic)  # OK — panic matches Callable[[str], Never]
```

## Common type-checker errors and how to read them

### `error: Argument 1 to "assert_never" has incompatible type "X"; expected "Never"` (mypy)

The narrowing chain above the `assert_never` call did not exhaust all variants. Type `X` is still possible. Add a branch handling `X`.

### `error: Implicit return in function which does not return` (mypy)

A function annotated `-> Never` (or `-> NoReturn`) has a code path that falls through to an implicit `return None`. Make sure every path raises, calls `sys.exit()`, or calls another `Never`-returning function.

### `error: Statement is unreachable` (pyright) / `note: unreachable` (mypy with `--warn-unreachable`)

Code appears after a call to a `Never`-returning function. This is usually intentional and correct — remove the dead code. If unexpected, check whether the function actually should return `Never`.

### `"Never" is not assignable to "X"` / type mismatch involving Never

This usually appears in generic contexts where the checker inferred `Never` for a type variable (e.g., an empty list literal `[]` has type `list[Never]`). Provide an explicit type annotation to guide inference: `items: list[int] = []`.

## Use-case cross-references

- [-> UC-03](../usecases/03-type-narrowing-exhaustiveness.md) — Validation pipelines that use `Never`-returning error functions to guarantee all branches produce valid output.
- [-> UC-08](../usecases/08-error-handling-types.md) — State machines and command dispatchers that use `assert_never` to guarantee exhaustive handling of all states/commands.

## Source anchors

- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/) — `NoReturn`
- [PEP 655 — Marking individual TypedDict items as required or potentially-missing](https://peps.python.org/pep-0655/) — introduced `Never` as the bottom type (in the broader typing spec update)
- [typing spec — Never and NoReturn](https://typing.readthedocs.io/en/latest/spec/special-types.html#never)
- [mypy docs — NoReturn](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#the-noreturn-type)
- [Python docs — typing.Never](https://docs.python.org/3/library/typing.html#typing.Never)
