# TypeAlias and the `type` Statement

> **Since:** `TypeAlias` Python 3.10 (PEP 613); `type` statement Python 3.12 (PEP 695)

## What it is

Python has two mechanisms for creating explicit type aliases. The older form uses the `TypeAlias` annotation (`Vector: TypeAlias = list[float]`) to distinguish an alias from an ordinary variable assignment. The newer form uses the `type` statement (`type Vector = list[float]`), introduced alongside the new generic syntax in Python 3.12. Both tell the type checker "this name is a synonym for another type" rather than a variable that holds a type object.

The `type` statement additionally provides **lazy evaluation**: the right-hand side is not evaluated at import time, which naturally supports forward references and recursive type definitions without `from __future__ import annotations` or string quoting.

## What constraint it enforces

**Explicit alias declarations prevent the checker from confusing a type alias with a variable assignment, and enable forward references and recursive types that would otherwise be impossible or fragile.** Without an explicit marker, `X = int` is ambiguous: is `X` a type alias or a variable whose value happens to be `int`? The checker may guess wrong, producing confusing errors downstream.

## Minimal snippet

```python
# Python 3.10+ — TypeAlias annotation
from typing import TypeAlias

Vector: TypeAlias = list[float]          # OK — explicit alias

def scale(v: Vector, factor: float) -> Vector:
    return [x * factor for x in v]       # OK

# Python 3.12+ — type statement
type JSONValue = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]

def dump(val: JSONValue) -> str: ...     # OK — recursive alias works
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Generics / TypeVar** [-> catalog/07](T04-generics-bounds.md) | Generic aliases like `type Callback[T] = Callable[[T], None]` bind type parameters directly in the alias. With 3.12 syntax, the TypeVar is scoped to the alias. |
| **Any / inference** [-> catalog/20](T47-gradual-typing.md) | A bare assignment `X = SomeComplexType` may be inferred as `type[SomeComplexType]` (a variable) rather than an alias, causing `Any`-like behavior or unexpected errors. Explicit aliases prevent this. |
| **Union / Literal** [-> catalog/02](T02-union-intersection.md) | Union aliases are common: `type Result = Success | Failure`. The alias is expanded transparently by the checker. |

## Gotchas and limitations

1. **Bare assignment is ambiguous.** `X = int` could be a type alias or a variable. mypy and pyright handle this differently:
   - mypy treats bare assignments to simple types as aliases but warns on complex cases.
   - pyright is stricter and may treat it as a variable.
   Always use `TypeAlias` or `type` to be unambiguous.

2. **`TypeAlias` requires eager evaluation.** The right-hand side of `X: TypeAlias = ...` is evaluated at import time. Forward references must be quoted as strings. The `type` statement avoids this problem entirely.

3. **`type` statement requires Python 3.12+.** There is no backport of the `type` statement syntax. For older versions, use `TypeAlias`.

4. **Recursive aliases need the `type` statement (or special handling).** With `TypeAlias`, recursive types like `JSON = str | list["JSON"]` require string quoting and may not be fully supported in all checkers. The `type` statement handles recursion natively.

5. **Aliases are transparent.** A type alias does not create a new distinct type. `Vector` and `list[float]` are interchangeable — there is no nominal distinction. Use `NewType` [-> catalog/04](T03-newtypes-opaque.md) if you need a distinct type.

6. **Runtime introspection differs.** `TypeAlias`-annotated names evaluate to the right-hand side at runtime. `type`-statement aliases create a `TypeAliasType` object that delays evaluation. Libraries performing runtime type introspection may need updating for 3.12 aliases.

## Beginner mental model

Think of a type alias as a **nickname**. When you write `type UserID = int`, you are telling both the checker and other developers: "wherever you see `UserID`, read it as `int`." The nickname makes code more readable and lets you change the underlying type in one place.

The `type` statement is the modern, preferred way to create nicknames. It also handles tricky situations (forward references, recursion) that the older `TypeAlias` annotation cannot.

## Example A — Recursive JSON type with `type` statement

```python
# Python 3.12+
type JSONPrimitive = str | int | float | bool | None
type JSONArray = list[JSONValue]
type JSONObject = dict[str, JSONValue]
type JSONValue = JSONPrimitive | JSONArray | JSONObject

def get_string(val: JSONValue) -> str | None:
    if isinstance(val, str):
        return val                               # OK — narrowed to str
    return None                                  # OK

def process(data: JSONValue) -> None:
    match data:
        case str(s):
            print(f"string: {s}")                # OK
        case list(items):
            for item in items:
                process(item)                    # OK — recursive
        case dict(mapping):
            for k, v in mapping.items():
                process(v)                       # OK — recursive
        case int(n) | float(n):
            print(f"number: {n}")                # OK
        case bool(b):
            print(f"bool: {b}")                  # OK
        case None:
            print("null")                        # OK
```

Without the `type` statement, the mutually recursive aliases (`JSONValue` references `JSONArray`, which references `JSONValue`) would require quoted forward references and may not work reliably across checkers.

## Example B — Complex generic alias for callback registries

```python
# Python 3.12+
from collections.abc import Callable, Awaitable

# Generic alias: a handler takes an event of type E and returns nothing
type SyncHandler[E] = Callable[[E], None]
type AsyncHandler[E] = Callable[[E], Awaitable[None]]
type Handler[E] = SyncHandler[E] | AsyncHandler[E]

# Registry maps event names to lists of handlers
type HandlerRegistry[E] = dict[str, list[Handler[E]]]

class EventBus[E]:
    def __init__(self) -> None:
        self._handlers: HandlerRegistry[E] = {}

    def on(self, event: str, handler: Handler[E]) -> None:
        self._handlers.setdefault(event, []).append(handler)    # OK

    async def emit(self, event: str, payload: E) -> None:
        import asyncio
        for handler in self._handlers.get(event, []):
            result = handler(payload)
            if isinstance(result, Awaitable):
                await result                                     # OK

# Usage:
bus: EventBus[str] = EventBus()
bus.on("greet", lambda msg: print(msg))            # OK — SyncHandler[str]
bus.on("greet", lambda msg: None)                  # OK

# Type error: wrong payload type
bus.on("greet", lambda n: print(n + 1))            # error (if n is assumed int)
```

The layered aliases make the complex `dict[str, list[Callable[[E], None] | Callable[[E], Awaitable[None]]]]` type readable and maintainable.

## Common type-checker errors and how to read them

### mypy: `error: Type alias is invalid in runtime context`

You tried to use a `TypeAlias`-annotated name as a value at runtime (for example, calling it as a constructor). Aliases are transparent type synonyms, not classes.

### pyright: `"X" is a type alias and cannot be used as a value`

Same cause. If you need both a type and a runtime value, consider `NewType` [-> catalog/04](T03-newtypes-opaque.md) or a class.

### mypy: `error: Recursive types are not allowed`

You tried to define a recursive alias using `TypeAlias` without proper quoting, or your mypy version does not support the pattern. Upgrade to mypy 0.990+ or use the `type` statement with Python 3.12+.

### pyright: `Type alias "X" has a circular dependency`

The alias references itself in a way the checker cannot resolve lazily. This usually happens with `TypeAlias`-style definitions. Switching to the `type` statement typically resolves it.

### mypy: `error: Variable "X" is not valid as a type` / `note: did you mean to use TypeAlias?`

You wrote `X = SomeType` without the `TypeAlias` annotation, and mypy is treating `X` as a variable rather than an alias. Add `: TypeAlias` or use the `type` statement.

## Use-case cross-references


## Source anchors

- [PEP 613 — Explicit Type Aliases](https://peps.python.org/pep-0613/)
- [PEP 695 — Type Parameter Syntax](https://peps.python.org/pep-0695/)
- [typing module — TypeAlias](https://docs.python.org/3/library/typing.html#typing.TypeAlias)
- [typing module — type statement](https://docs.python.org/3/reference/simple_stmts.html#the-type-statement)
- [mypy docs — Type aliases](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#type-aliases)
