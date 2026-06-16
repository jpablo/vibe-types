# Never and NoReturn

> **Since:** `NoReturn` Python 3.5.4 (PEP 484); `Never` Python 3.11 (typing spec — no dedicated PEP) | **Backport:** `typing_extensions`

## What it is

`Never` (and its legacy alias `NoReturn`) is the *bottom type* in Python's type system: it has no inhabitants. No value can have type `Never`. This makes it useful in two complementary roles: (1) annotating functions that never return normally — they always raise an exception, call `sys.exit()`, or loop forever — and (2) serving as the identity element in exhaustiveness proofs, where `assert_never(x)` accepts only an argument of type `Never`, proving that every variant in a union has already been handled.

`Never` and `NoReturn` are semantically identical. `NoReturn` was introduced first (PEP 484) as a return-type annotation; `Never` was added in Python 3.11 by the typing specification as a general-purpose bottom type usable in any position (parameters, variables, return types). Modern code should prefer `Never`.

## What constraint it enforces

**Functions annotated as returning `Never` must not contain any reachable `return` statement or implicit `return None`. Code after a call to such a function is unreachable, and checkers can flag it (pyright's `reportUnreachable`, mypy's `--warn-unreachable` — both opt-in). When used as a parameter type via `assert_never`, it proves that a narrowing chain is exhaustive — if the checker cannot narrow the argument to `Never`, it means a variant is unhandled.**

## Minimal snippet

```python
from typing import Never

def fail(msg: str) -> Never:
    raise RuntimeError(msg)       # never returns normally

def parse_port(raw: str) -> int:
    if not raw.isdigit():
        fail(f"not a number: {raw}")
    return int(raw)               # OK — the failing branch cannot fall through
```

And the exhaustiveness role — `assert_never` names exactly which variant you forgot:

```python
from typing import assert_never

type Shape = int | str | float

def area(s: Shape) -> float:
    if isinstance(s, int):
        return float(s * s)
    elif isinstance(s, str):
        return 0.0
    else:
        # forgot the float branch:
        assert_never(s)  # error: Argument of type "float" cannot be assigned to parameter "arg" of type "Never"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Union narrowing** [-> T02](T02-union-intersection.md) | After narrowing every member of a Union through `isinstance` or `match`/`case`, the remaining type is `Never`. Calling `assert_never` in the `else` branch proves exhaustiveness. |
| **Enum exhaustiveness** [-> T01](T01-algebraic-data-types.md) | Matching all members of an Enum in `match`/`case` or `if`/`elif` narrows the remaining type to `Never`. Adding a new member without updating all match sites causes a type error at the `assert_never` call. |
| **TypeGuard / TypeIs** [-> T14](T14-type-narrowing.md) | `TypeIs` narrows both branches, enabling the remainder to eventually reach `Never`. `TypeGuard` only narrows the positive branch, so it cannot drive exhaustiveness proofs by itself. |
| **Callable** [-> T22](T22-callable-typing.md) | `Callable[..., Never]` describes a callback that never returns — useful for error-handler registries. |

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
   from typing import Never

   def bad(flag: bool) -> Never:  # error: Function with declared return type "NoReturn" cannot return "None"
       if flag:
           raise ValueError("nope")
       # falls through — implicit return None, but declared Never
   ```

3. **`assert_never` is a runtime function.** At runtime, `assert_never` raises `AssertionError` if reached. It is not purely a static construct — it also serves as a safety net if the type checker is bypassed.

4. **`Never` is a subtype of every type.** This is the defining property of a bottom type. It means a variable of type `Never` can be assigned to anything, but no value can ever have that type. This can confuse beginners who see `Never` appear in `reveal_type` output.

5. **Unreachable-code reporting is opt-in.** pyright's `reportUnreachable` check is **off by default** — unreachable statements are merely greyed out in the editor. This repo's pyright configuration sets `reportUnreachable = "error"`, which is why code after a `Never`-returning call is reported as an error in these examples. mypy reports it only with `--warn-unreachable`. A side effect of opting in: once a narrowing chain is exhaustive, an `assert_never` guard branch is itself unreachable and gets flagged — in such a configuration, prefer letting a declared return type prove exhaustiveness (see Example A).

6. **`Never` in generic positions.** `list[Never]` is a valid type (an empty list that can never have elements added). This comes up in generic code where an empty container's element type cannot be inferred.

## Beginner mental model

`Never` means **"this can't happen."** If a function returns `Never`, it means the function will never hand control back to you — it will always crash or run forever. If a variable has type `Never` in a branch, it means the checker has proven that branch is impossible to reach. `assert_never` is your way of saying "I believe this branch is impossible — prove me right."

## Example A — exhaustive handling of a closed set

`assert_never` shines when a match is *incomplete* — the error message names the unhandled variant:

```python
from typing import assert_never
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
        case _ as unhandled:
            # BLUE is not handled:
            assert_never(unhandled)  # error: Argument of type "Literal[Color.BLUE]" cannot be assigned to parameter "arg" of type "Never"
```

Once every member is handled, the declared return type alone proves exhaustiveness — if someone adds `Color.YELLOW` later, the checker reports that `hex_code` no longer returns on all paths:

```python
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
```

Note: with `reportUnreachable` enabled (as in this repo), keeping a `case _: assert_never(...)` arm after full coverage is itself flagged as unreachable code. The explicit guard earns its keep in functions that don't return a value (`-> None`) and in configurations that don't error on unreachable code.

The same pattern with `if`/`elif`:

```python
from typing import assert_never

type Result = int | str | float

def summarize(r: Result) -> str:
    if isinstance(r, int):
        return f"integer: {r}"
    elif isinstance(r, str):
        return f"string: {r}"
    else:
        return f"float: {r}"   # r is float — nothing else left

# Forget the float branch and assert_never reports it:
def summarize_broken(r: Result) -> str:
    if isinstance(r, int):
        return f"integer: {r}"
    elif isinstance(r, str):
        return f"string: {r}"
    else:
        assert_never(r)  # error: Argument of type "float" cannot be assigned to parameter "arg" of type "Never"
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
    except json.JSONDecodeError as e:
        fatal(f"Invalid JSON in {path}: {e}")

# The checker sees that both except branches call fatal() -> Never,
# and the try branch returns dict[str, str], so the overall return
# type is dict[str, str]. No need for a fallback return.
```

Using `Never` as a callback type — and what happens to code after a `Never` call (flagged here because this repo enables `reportUnreachable`):

```python
from collections.abc import Callable
from typing import Never

type ErrorHandler = Callable[[str], Never]

def risky_operation() -> None:
    raise RuntimeError("something went wrong")

def with_error_handler(handler: ErrorHandler) -> None:
    try:
        risky_operation()
    except Exception as e:
        handler(str(e))
        print("this never prints")  # error: Type analysis indicates code is unreachable

def panic(msg: str) -> Never:
    raise SystemExit(msg)

with_error_handler(panic)  # OK — panic matches Callable[[str], Never]
```

## Common type-checker errors and how to read them

### `error: Argument 1 to "assert_never" has incompatible type "X"; expected "Never"` (mypy)

The narrowing chain above the `assert_never` call did not exhaust all variants. Type `X` is still possible. Add a branch handling `X`.

### `error: Implicit return in function which does not return` (mypy)

A function annotated `-> Never` (or `-> NoReturn`) has a code path that falls through to an implicit `return None`. Make sure every path raises, calls `sys.exit()`, or calls another `Never`-returning function. pyright's wording is `Function with declared return type "NoReturn" cannot return "None"`.

### `error: Type analysis indicates code is unreachable` (pyright with `reportUnreachable` enabled) / `note: unreachable` (mypy with `--warn-unreachable`)

Code appears after a call to a `Never`-returning function. This is usually intentional and correct — remove the dead code. If unexpected, check whether the function actually should return `Never`. Remember both checks are opt-in.

### `"Never" is not assignable to "X"` / type mismatch involving Never

This usually appears in generic contexts where the checker inferred `Never` (or `Unknown`) for a type variable — e.g., an empty list literal `[]` gives the checker nothing to infer from. Provide an explicit type annotation to guide inference: `items: list[int] = []`.

## Use-case cross-references

- [-> UC03](../usecases/UC03-exhaustiveness.md) — Validation pipelines that use `Never`-returning error functions to guarantee all branches produce valid output.
- [-> UC08](../usecases/UC08-error-handling.md) — State machines and command dispatchers that use `assert_never` to guarantee exhaustive handling of all states/commands.

## When to Use

- **Exhaustiveness checking over a closed set** — when handling every member of a `Literal` or union, a declared return type already forces coverage; `assert_never` adds an explicit, named proof where no return type anchors the check.

  ```python
  from typing import Literal

  type Status = Literal[200, 404]

  def describe(code: Status) -> str:
      if code == 200:
          return "success"
      else:
          return "not found"   # code is Literal[404] here — adding 500 to Status breaks this function visibly
  ```

- **Functions that always raise or exit** — signal that normal return is impossible.

  ```python
  from typing import Never

  def exit_on_error(msg: str) -> Never:
      raise SystemExit(msg)

  x: int = exit_on_error("stop")  # OK — Never is assignable to every type
  ```

- **Excluding union members on error paths** — a branch that raises returns `Never`, so it drops out of the inferred return type.

  ```python
  def process(value: int | str | None) -> int | str:
      if value is None:
          raise ValueError("no value")  # this branch is Never — excluded from the result
      return value  # narrowed: int | str
  ```

## When NOT to Use

- **For "no return value" on functions that normally complete** — use a `None` return type instead.

  ```python
  from typing import Never

  def log(msg: str) -> None:
      print(msg)  # OK

  def bad(msg: str) -> Never:  # error: Function with declared return type "NoReturn" cannot return "None"
      print(msg)
  ```

- **As a catch-all type for unknown values** — use `object` instead. A `Never` parameter is legal to declare but impossible to call.

  ```python
  from typing import Never

  def handle(obj: object) -> None: ...  # OK — accepts anything

  def bad(obj: Never) -> None: ...      # legal to define, impossible to call

  handle(42)  # OK
  bad(42)     # error: Argument of type "Literal[42]" cannot be assigned to parameter "obj" of type "Never"
  ```

- **With empty collections expecting specific element types** — annotate explicitly; a bare `[]` gives the checker nothing to infer the element type from (pyright infers `list[Unknown]`, mypy demands an annotation).

  ```python
  items: list[int] = []  # OK
  items.append(1)

  items2 = []
  items2.append(1)  # error: Type of "append" is partially unknown
  ```

## Antipatterns When Using `Never`

### Pattern: `assert_never` on a value that can never be narrowed

If the subject's type cannot be narrowed away — e.g. the discriminator is a plain `str` — `assert_never` errors unconditionally, not just "when a new variant is added":

```python
from dataclasses import dataclass
from typing import assert_never

@dataclass
class LooseMsg:
    kind: str   # plain str — comparisons don't narrow LooseMsg itself

def handle_bad(msg: LooseMsg) -> None:
    if msg.kind == "text":
        pass
    elif msg.kind == "ping":
        pass
    else:
        assert_never(msg)  # error: Argument of type "LooseMsg" cannot be assigned to parameter "arg" of type "Never"
```

(Only `Any` silences this — `Any` is assignable to everything, including `Never`. An `object`-typed argument still errors.)

Better: make the variants a tagged union with `Literal` discriminators, so the checker can actually narrow — and let the declared return type enforce exhaustiveness:

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class TextMsg:
    kind: Literal["text"]
    body: str

@dataclass
class PingMsg:
    kind: Literal["ping"]

type Msg = TextMsg | PingMsg

def handle_good(msg: Msg) -> str:
    match msg:
        case TextMsg(body=body):
            return body
        case PingMsg():
            return "pong"
    # adding a new variant to Msg makes this function error:
    # "must return value on all code paths"
```

### Pattern: `assert_never` without exhaustiveness coverage

```python
from typing import assert_never

type Shape = int | str | float

def area_bad(s: Shape) -> float:
    if isinstance(s, int):
        return float(s * s)
    # missing str and float handlers
    assert_never(s)  # error: Argument of type "str | float" cannot be assigned to parameter "arg" of type "Never"
```

Better: handle all cases (the final branch needs no `isinstance` — only one member remains):

```python
type Shape = int | str | float

def area_good(s: Shape) -> float:
    if isinstance(s, int):
        return float(s * s)
    elif isinstance(s, str):
        return 0.0
    else:
        return s   # s is float — the union is exhausted
```

### Pattern: silent `pass` in the fallback branch

```python
def process(value: int | str) -> str:  # error: Function with declared return type "str" must return value on all code paths
    if isinstance(value, int):
        return str(value)
    else:
        pass  # BAD: silently produces None
```

Better — cover the remaining member explicitly:

```python
def process(value: int | str) -> str:
    if isinstance(value, int):
        return str(value)
    else:
        return value   # value is str here
```

## Antipatterns with Other Techniques

### Pattern: Silent fallback instead of an exhaustive match

```python
from enum import Enum

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

def rgb(c: Color) -> tuple[int, int, int]:
    if c == Color.RED:
        return (255, 0, 0)
    if c == Color.GREEN:
        return (0, 255, 0)
    return (0, 0, 0)  # BAD: silent fallback — BLUE gets black, and no warning if a member is added
```

Better — match every member, with no fallback to hide behind:

```python
from enum import Enum

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

def rgb(c: Color) -> tuple[int, int, int]:
    match c:
        case Color.RED:
            return (255, 0, 0)
        case Color.GREEN:
            return (0, 255, 0)
        case Color.BLUE:
            return (0, 0, 255)
    # adding Color.YELLOW now errors: "must return value on all code paths"
```

### Pattern: Manual runtime assertions instead of `assert_never`

A hand-rolled `raise AssertionError` only fires at runtime. When someone widens the union, the checker stays silent:

```python
def process_runtime(value: int | str | bytes) -> None:
    if isinstance(value, int):
        print(value * 2)
    elif isinstance(value, str):
        print(value.upper())
    else:
        raise AssertionError("unreachable")  # BAD: bytes slips through to a runtime crash
```

Better with `assert_never` — the unhandled variant is caught at type-check time:

```python
from typing import assert_never

def process_static(value: int | str | bytes) -> None:
    if isinstance(value, int):
        print(value * 2)
    elif isinstance(value, str):
        print(value.upper())
    else:
        assert_never(value)  # error: Argument of type "bytes" cannot be assigned to parameter "arg" of type "Never"
```

### Pattern: Returning `None` on error paths instead of raising

```python
def parse_id(s: str) -> int | None:
    try:
        return int(s)
    except ValueError:
        return None  # BAD: caller must check for None

id_val = parse_id("x")
if id_val is not None:
    print(id_val * 2)  # extra checks everywhere
```

Better with a raising (`Never`) error path:

```python
def parse_id_or_fail(s: str) -> int:
    try:
        return int(s)
    except ValueError:
        raise ValueError(f"Invalid id: {s}")  # this branch is Never

id_val = parse_id_or_fail("123")  # directly int, no checks needed
```

## Source anchors

- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/) — `NoReturn`
- [typing spec — Never and NoReturn](https://typing.readthedocs.io/en/latest/spec/special-types.html#never) — `Never` was added in Python 3.11 via the typing spec; it has no dedicated PEP
- [mypy docs — NoReturn](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#the-noreturn-type)
- [Python docs — typing.Never](https://docs.python.org/3/library/typing.html#typing.Never)
- [Python docs — typing.assert_never](https://docs.python.org/3/library/typing.html#typing.assert_never)
