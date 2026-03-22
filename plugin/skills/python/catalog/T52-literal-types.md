# Literal Types

> **Since:** Python 3.8 (PEP 586) | `typing_extensions.Literal` backports to 3.7

## What it is

`Literal` types restrict a value to one or more specific literal values rather than an entire type. `Literal["GET", "POST"]` means the value must be exactly `"GET"` or `"POST"` — not just any `str`. This lets the type checker verify that only valid values are passed, catch typos at check time, and enable return-type narrowing through `@overload` dispatch.

Literal types work with `int`, `str`, `bytes`, `bool`, `enum` members, and `None`. They compose naturally with `Union`, `@overload`, and `TypeGuard` to build precise, value-aware APIs.

## What constraint it enforces

**A value must be exactly one of the declared literal values. The checker rejects any value outside the literal set and can narrow return types based on which literal was passed.**

- `Literal["red", "green", "blue"]` rejects `"yellow"` and rejects a plain `str` variable (since it could be anything).
- `Literal[True]` and `Literal[False]` are distinct types, enabling boolean-discriminated overloads.
- Passing a widened `str` where `Literal[...]` is expected is an error — the checker cannot prove the value is in the set.

## Minimal snippet

```python
from typing import Literal

def set_color(color: Literal["red", "green", "blue"]) -> None: ...

set_color("red")     # OK
set_color("green")   # OK
# set_color("yellow")  # error: Argument of type "Literal['yellow']" cannot be
#                       #        assigned to parameter of type "Literal['red', 'green', 'blue']"

name: str = "red"
# set_color(name)      # error: "str" is not assignable to "Literal['red', 'green', 'blue']"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Union types** [-> catalog/T02](T02-union-intersection.md) | `Literal["a", "b"]` is equivalent to `Literal["a"] \| Literal["b"]`. Union and Literal are often used together: `Union[Literal["ok"], Literal["error"]]` for tagged results. |
| **Type narrowing** [-> catalog/T14](T14-type-narrowing.md) | `if x == "GET":` narrows `x` from `Literal["GET", "POST"]` to `Literal["GET"]` in the true branch. `match`/`case` works similarly. |
| **Callable typing / overloads** [-> catalog/T22](T22-callable-typing.md) | `@overload` with `Literal` parameters enables return-type narrowing: different literal arguments yield different return types. |
| **TypedDict** [-> catalog/T31](T31-record-types.md) | Literal types serve as discriminator fields in tagged TypedDict unions: `{"kind": Literal["circle"], "radius": float}`. |
| **Never / exhaustiveness** [-> catalog/T34](T34-never-bottom.md) | After narrowing all Literal branches, the residual type is `Never`. `assert_never()` proves completeness. |

## Gotchas and limitations

1. **Literals widen on assignment.** Assigning a `Literal["GET"]` to a `str`-annotated variable widens it, losing the literal information. To preserve it, annotate explicitly:
   ```python
   verb: Literal["GET"] = "GET"   # stays Literal["GET"]
   verb2: str = "GET"             # widened to str — cannot pass to Literal param
   ```

2. **Only certain types are allowed.** `Literal` accepts `int`, `str`, `bytes`, `bool`, `enum` members, and `None`. You cannot write `Literal[3.14]`, `Literal[(1, 2)]`, or `Literal[some_variable]`.

3. **`Literal[True]` and `Literal[1]` overlap.** Since `bool` is a subclass of `int` in Python, `True == 1` at runtime. Type checkers treat `Literal[True]` and `Literal[1]` as distinct types, but this can cause subtle issues in value comparisons.

4. **Checker divergence on Literal enums.** mypy and pyright differ in how aggressively they infer literal enum types. pyright narrows `MyEnum.A` to `Literal[MyEnum.A]` more often than mypy does.

5. **String literals are case-sensitive.** `Literal["GET"]` does not match `"get"`. If your domain is case-insensitive, you need to handle normalization before the Literal boundary.

6. **No computed Literals.** You cannot programmatically generate a `Literal` type from a list of values at check time. The values must be hard-coded in the annotation.

## Beginner mental model

Think of `Literal` as a **guest list at a door**. The type `str` is "anyone with a name can enter." `Literal["Alice", "Bob"]` is "only Alice and Bob may enter — everyone else is turned away." The checker is the bouncer who verifies the name before letting you through.

## Example A — Overload dispatch with Literal

```python
from typing import Literal, overload

@overload
def open_file(mode: Literal["r"]) -> str: ...
@overload
def open_file(mode: Literal["rb"]) -> bytes: ...

def open_file(mode: Literal["r", "rb"]) -> str | bytes:
    if mode == "r":
        return "text content"
    return b"binary content"

text = open_file("r")     # inferred: str
data = open_file("rb")    # inferred: bytes
# open_file("w")          # error: No overload matches "Literal['w']"
```

## Example B — Boolean discrimination with Literal[True] / Literal[False]

```python
from typing import Literal, overload

@overload
def fetch(url: str, *, raw: Literal[True]) -> bytes: ...
@overload
def fetch(url: str, *, raw: Literal[False] = ...) -> str: ...

def fetch(url: str, *, raw: bool = False) -> str | bytes:
    content = b"<html>..."
    return content if raw else content.decode()

page = fetch("https://example.com")              # inferred: str
blob = fetch("https://example.com", raw=True)     # inferred: bytes
```

## Example C — TypeGuard with Literal

```python
from typing import Literal, TypeGuard

Color = Literal["red", "green", "blue"]

def is_color(value: str) -> TypeGuard[Color]:
    return value in ("red", "green", "blue")

def paint(c: Color) -> None: ...

user_input = input("Color: ")
if is_color(user_input):
    paint(user_input)   # OK — narrowed to Color
else:
    print("Invalid color")
```

## Common type-checker errors and how to read them

### Literal mismatch

```
# mypy:    error: Argument 1 to "f" has incompatible type "str";
#                 expected "Literal['a', 'b']"
# pyright: error: "str" cannot be assigned to type "Literal['a', 'b']"
```

**Cause:** A plain `str` was passed where a specific literal was required.
**Fix:** Pass a literal value directly, or annotate the variable with the `Literal` type.

### No matching overload

```
# mypy:    error: No overload variant of "open_file" matches argument type "Literal['w']"
# pyright: error: No overloads for "open_file" match the provided arguments
```

**Cause:** The literal value does not match any `@overload` signature.
**Fix:** Add an overload for that value, or widen the accepted Literal set.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Restrict function inputs to known-valid values.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Model domain constants as closed Literal sets.
- [-> UC-03](../usecases/UC03-exhaustiveness.md) — Exhaustive matching on Literal branches.
- [-> UC-07](../usecases/UC07-callable-contracts.md) — Overload dispatch keyed on Literal parameters.
- [-> UC-29](../usecases/UC29-typed-records.md) — Discriminated unions with Literal tag fields.

## Source anchors

- [PEP 586 — Literal Types](https://peps.python.org/pep-0586/)
- [typing spec — Literal types](https://typing.readthedocs.io/en/latest/spec/literal.html)
- [mypy — Literal types](https://mypy.readthedocs.io/en/stable/literal_types.html)
- [pyright — Literal types](https://microsoft.github.io/pyright/#/configuration?id=reportunnecessarycomparison)
- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
