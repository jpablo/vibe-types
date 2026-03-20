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
| **Union / Literal** [-> [catalog/02](02-union-literal-types.md)] | `Union[X, Y]` and `Literal["a"]` extend basic annotations to multi-type and value-level constraints. |
| **TypeGuard / TypeIs** [-> [catalog/13](13-typeguard-typeis-narrowing.md)] | Narrowing functions refine `Optional` and `Union` annotations inside conditional branches. |
| **Gradual typing** [-> [catalog/20](20-type-inference-gradual-typing.md)] | Unannotated code defaults to `Any`, which is compatible with every type. Adding annotations is how you opt into stricter checking. |
| **Final / ClassVar** [-> [catalog/12](12-final-classvar.md)] | `Final[int]` combines a basic annotation with an immutability constraint. |
| **TypedDict** [-> [catalog/03](03-typeddict.md)] | TypedDict values are annotated with the same basic types described here. |

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

- [-> UC-01](../usecases/01-preventing-invalid-states.md) — Typing function signatures for public API contracts.
- [-> UC-02](../usecases/02-domain-modeling.md) — Catching type mismatches in data pipelines.
- [-> UC-03](../usecases/03-type-narrowing-exhaustiveness.md) — Enforcing None-safety in database query results.
- [-> UC-08](../usecases/08-error-handling-types.md) — Optional return types encode None-as-error patterns.
- [-> UC-12](../usecases/12-gradual-adoption.md) — Basic annotations as the entry point for migrating untyped codebases.

## Source anchors

- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
- [PEP 526 — Syntax for Variable Annotations](https://peps.python.org/pep-0526/)
- [PEP 604 — Allow writing union types as X | Y](https://peps.python.org/pep-0604/)
- [PEP 563 — Postponed Evaluation of Annotations](https://peps.python.org/pep-0563/)
- [typing module documentation](https://docs.python.org/3/library/typing.html)
- [mypy documentation — Built-in types](https://mypy.readthedocs.io/en/stable/builtin_types.html)
