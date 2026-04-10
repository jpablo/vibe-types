# Unpack and **kwargs Typing

> **Since:** Python 3.12 (PEP 692) | **Backport:** `typing_extensions`

## What it is

`Unpack` applied to a `TypedDict` lets you specify the exact types of individual keyword arguments passed via `**kwargs`. Before PEP 692, `**kwargs: int` meant "every keyword argument is an `int`" — there was no way to say "keyword `x` is an `int` and keyword `y` is a `str`." By combining `**kwargs: Unpack[SomeTypedDict]`, each key-value pair in the TypedDict becomes a named, individually typed keyword argument.

This feature closes a long-standing gap in Python's type system: functions with heterogeneous keyword arguments can now be fully typed without resorting to `@overload` combinatorics or `Any`.

## What constraint it enforces

**Each keyword argument passed via `**kwargs` is constrained to the type declared for its corresponding key in the TypedDict, and missing/extra keys are flagged according to `Required`/`NotRequired` markers.** The checker treats the `Unpack[TD]` annotation as if the function had explicit keyword parameters matching the TypedDict's fields.

## Minimal snippet

```python
from typing import TypedDict, Unpack

class Options(TypedDict, total=False):
    timeout: int
    retries: int
    verbose: bool

def fetch(url: str, **kwargs: Unpack[Options]) -> str:
    timeout = kwargs.get("timeout", 30)      # OK — int
    return f"fetching {url}"

fetch("https://example.com", timeout=10)             # OK
fetch("https://example.com", retries=3, verbose=True) # OK
fetch("https://example.com", timeout="slow")          # error — expected int
fetch("https://example.com", unknown=42)              # error — extra key
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **TypedDict** [-> catalog/03](T31-record-types.md) | The TypedDict used with `Unpack` defines the schema for kwargs. `Required` and `NotRequired` markers control which kwargs are mandatory. |
| **@overload** [-> catalog/11](T22-callable-typing.md) | Before `Unpack`, overloads were the only way to type heterogeneous kwargs. `Unpack` replaces many overload-heavy patterns with a single signature. |
| **Annotated** [-> catalog/15](T26-refinement-types.md) | Individual TypedDict values can carry `Annotated` metadata, which flows through to the kwargs. |
| **Callable** [-> catalog/11](T22-callable-typing.md) | `Callable` signatures involving `Unpack` kwargs can be represented using `ParamSpec` [-> catalog/08](T45-paramspec-variadic.md) for forwarding. |

## Gotchas and limitations

1. **Only one `Unpack` per function.** You cannot have `**kwargs: Unpack[A]` and `**kwargs2: Unpack[B]` — Python only allows a single `**kwargs` parameter.

2. **Cannot mix `Unpack` with regular `**kwargs` typing.** If you use `**kwargs: Unpack[TD]`, every keyword argument must match a key in `TD`. You cannot have both typed and untyped keyword arguments.

3. **`total=True` means all keys are required.** If the TypedDict uses `total=True` (the default), every key becomes a mandatory keyword argument. Use `total=False` or `NotRequired` for optional kwargs.

4. **TypedDict must be a direct type, not a union.** You cannot write `Unpack[A | B]`. If you need different kwargs shapes, use `@overload`.

5. **Forwarding typed kwargs is tricky.** Passing `**kwargs` to another function that also expects `Unpack[TD]` works, but intermediate manipulation (adding/removing keys) may confuse the checker.

6. **Checker support varies.** As of early 2024, pyright has full support. mypy support landed in version 1.7+ but edge cases (inheritance, forwarding) may still have gaps.

7. **Runtime behavior is unchanged.** `Unpack` is a static-only construct. At runtime, `kwargs` is still a plain `dict[str, Any]`.

## Beginner mental model

Think of `Unpack[Options]` as "unzipping" the TypedDict into individual keyword parameters. Instead of writing:

```python
def fetch(url: str, *, timeout: int = 30, retries: int = 3, verbose: bool = False) -> str: ...
```

you define the parameters once in a TypedDict and spread them into the function signature. The checker sees the same constraints either way, but the TypedDict version is reusable across multiple functions and can be composed with other TypedDicts.

## Example A — Function with typed **kwargs via Unpack[ConfigDict]

```python
from typing import Required, NotRequired, TypedDict, Unpack

class DBConfig(TypedDict):
    host: Required[str]
    port: Required[int]
    user: NotRequired[str]
    password: NotRequired[str]
    ssl: NotRequired[bool]

def connect(**kwargs: Unpack[DBConfig]) -> str:
    host = kwargs["host"]                # OK — str, always present
    port = kwargs["port"]                # OK — int, always present
    user = kwargs.get("user", "root")    # OK — str
    use_ssl = kwargs.get("ssl", False)   # OK — bool
    return f"{user}@{host}:{port}"

# Valid calls:
connect(host="localhost", port=5432)                        # OK
connect(host="db.prod", port=5432, user="admin", ssl=True)  # OK

# Invalid calls:
connect(port=5432)                         # error — missing required "host"
connect(host="localhost", port="5432")     # error — port must be int
connect(host="localhost", port=5432, debug=True)  # error — unknown key "debug"
```

The TypedDict captures the full contract: which keys exist, which are required, and what type each value must have.

## Example B — Forwarding **kwargs while preserving types

```python
from typing import TypedDict, Unpack, NotRequired

class RenderOptions(TypedDict, total=False):
    width: int
    height: int
    quality: float
    format: str

def render_image(data: bytes, **kwargs: Unpack[RenderOptions]) -> bytes:
    """Core rendering function."""
    width = kwargs.get("width", 800)     # OK — int
    height = kwargs.get("height", 600)   # OK — int
    # ... render logic ...
    return data

def render_thumbnail(data: bytes, **kwargs: Unpack[RenderOptions]) -> bytes:
    """Renders a small version, forwarding options to render_image."""
    # Override size but forward everything else
    opts: RenderOptions = {
        "width": 128,
        "height": 128,
        **kwargs,                         # OK — merging TypedDicts
    }
    return render_image(data, **opts)     # OK — forwards typed kwargs

# The checker enforces constraints through the forwarding chain:
render_thumbnail(b"...", quality=0.8, format="png")  # OK
render_thumbnail(b"...", quality="high")              # error — float expected
render_thumbnail(b"...", color_space="sRGB")          # error — unknown key
```

The `RenderOptions` TypedDict is reused across both functions. Callers of `render_thumbnail` get the same type checking as callers of `render_image`, and the forwarding is fully typed.

## Common type-checker errors and how to read them

### mypy: `error: Unexpected keyword argument "x" for "func"`

You passed a keyword argument that does not match any key in the `Unpack`ed TypedDict. Check the TypedDict definition for the valid keys.

### pyright: `Keyword argument "x" is unknown for "Unpack[Options]"`

Same cause. pyright names the TypedDict in the error, making it easy to find the definition.

### mypy: `error: Missing named argument "host" for "connect"`

A `Required` key in the TypedDict was not provided. Either supply the argument or mark it `NotRequired` in the TypedDict.

### pyright: `Argument of type "str" cannot be assigned to parameter "port" (type "int")`

A keyword argument has the wrong type. The error message names both the actual and expected types.

### mypy: `error: Argument "**kwargs" to "func" has incompatible type`

You tried to forward a `dict` that does not match the expected TypedDict shape. Ensure the forwarded dict is typed as the correct TypedDict.

### pyright: `"**kwargs" argument type is incompatible with parameter type "Unpack[Options]"`

Same forwarding issue. The intermediate dict must be typed as the matching TypedDict, not as `dict[str, Any]`.

## Use-case cross-references

- [-> UC-09](../usecases/UC09-builder-config.md) — Configuration objects and option bags where heterogeneous kwargs are the natural API shape.

## When to use it

- **Configuration-heavy functions** where the number of options exceeds 3-4 and explicit parameters would be verbose
- **Plugin or extension APIs** where additional options may be added over time without breaking changes
- **Wrapper functions** that forward options to other functions while potentially overriding some values
- **Builder patterns** where options are accumulated and applied later

```python
from typing import TypedDict, Unpack, NotRequired

class EmailOptions(TypedDict, total=False):
    subject: str
    cc: NotRequired[list[str]]
    bcc: NotRequired[list[str]]
    priority: NotRequired[int]
    attachments: NotRequired[list[str]]

def send_email(to: str, body: str, **kwargs: Unpack[EmailOptions]) -> None:
    subject = kwargs.get("subject", "No subject")
    cc = kwargs.get("cc", [])
    # ...
    pass

send_email("user@example.com", "Hello", subject="Hi", priority=5)  # OK
```

## When NOT to use it

- **Simple functions** with 1-3 optional parameters — explicit parameters are clearer
- **When all callers need different subsets** — consider `@overload` instead
- **Public APIs with strict stability requirements** — TypedDict changes may break type checking for dependents
- **When you need runtime introspection** — `Unpack` is a static-only construct, `kwargs` is still `dict[str, Any]` at runtime

```python
# ❌ Don't use Unpack for simple functions
def greet(name: str, **kwargs: Unpack[TypedDictWithJustCaps: bool]) -> str:
    caps = kwargs.get("caps", False)
    return (name if caps else name.upper())

# ✅ Prefer explicit parameters for simplicity
def greet(name: str, caps: bool = False) -> str:
    return name if caps else name.upper()
```

## Antipatterns when using Unpack

### Antipattern 1: Using `Unpack` with `dict[str, Any]` instead of TypedDict

```python
from typing import TypedDict, Unpack, Any

# ❌ Loses all type safety
def process(**kwargs: Unpack[dict[str, Any]]) -> None:
    value = kwargs["x"]  # No type checking

# ✅ Use a TypedDict
class ProcessOptions(TypedDict, total=False):
    x: int
    y: str

def process(**kwargs: Unpack[ProcessOptions]) -> None:
    value = kwargs["x"]  # int
```

### Antipattern 2: Omitting `total=False` or `NotRequired` for optional kwargs

```python
from typing import TypedDict, Unpack

# ❌ All kwargs become required (default total=True)
class Options(TypedDict):
    debug: bool
    verbose: bool

def run(**kwargs: Unpack[Options]) -> None:
    pass

run()  # error — missing required "debug" and "verbose"

# ✅ Mark options as optional
class Options(TypedDict, total=False):
    debug: bool
    verbose: bool

def run(**kwargs: Unpack[Options]) -> None:
    pass

run()  # OK
```

### Antipattern 3: Manipulating kwargs before accessing

```python
from typing import TypedDict, Unpack

class Config(TypedDict, total=False):
    timeout: int
    retries: int

# ❌ Modifying kwargs confuses the type checker
def connect(**kwargs: Unpack[Config]) -> None:
    kwargs["timeout"] = 30  # OK
    timeout: int = kwargs["timeout"]  # May cause issues in some checkers
    pass

# ✅ Access directly or use .get()
def connect(**kwargs: Unpack[Config]) -> None:
    timeout = kwargs.get("timeout", 30)  # OK
    pass
```

## Antipatterns where Unpack provides better alternatives

### Antipattern: Overusing `@overload` for optional parameters

```python
from typing import overload

# ❌ Verbose overloads for optional params
@overload
def render(width: int) -> str: ...
@overload
def render(width: int, height: int) -> str: ...
@overload
def render(width: int, height: int, quality: float) -> str: ...
def render(width: int, height: int = 100, quality: float = 0.8) -> str:
    return f"{width}x{height}@{quality}"

# ✅ Use Unpack for optional params
from typing import TypedDict, Unpack

class RenderOptions(TypedDict, total=False):
    width: int
    height: int
    quality: float

def render(**kwargs: Unpack[RenderOptions]) -> str:
    w = kwargs.get("width", 800)
    h = kwargs.get("height", 600)
    q = kwargs.get("quality", 0.8)
    return f"{w}x{h}@{q}"
```

### Antipattern: Using `Any` or `dict` for heterogeneous options

```python
from typing import Any

# ❌ No type checking at all
def configure(options: dict[str, Any]) -> None:
    timeout = options["timeout"]  # Could be anything

configure({"timeout": "slow"})  # No error, but runtime may fail

# ✅ Typed options with Unpack
from typing import TypedDict, Unpack

class Config(TypedDict, total=False):
    timeout: int
    retries: int

def configure(**kwargs: Unpack[Config]) -> None:
    timeout = kwargs.get("timeout", 30)  # int or None

configure(timeout="slow")  # Type error caught at check time
```

### Antipattern: Creating separate parameters for related options

```python
# ❌ Scattered parameters lose cohesion
def create_user(
    name: str,
    email: str,
    send_welcome: bool = False,
    verify_email: bool = False,
    skip_notifications: bool = False,
    invite_code: str | None = None,
) -> User:
    ...

# ✅ Group related options with Unpack
from typing import TypedDict, Unpack

class UserCreateOptions(TypedDict, total=False):
    send_welcome: bool
    verify_email: bool
    skip_notifications: bool
    invite_code: str

def create_user(name: str, email: str, **kwargs: Unpack[UserCreateOptions]) -> User:
    send_welcome = kwargs.get("send_welcome", False)
    # ...
    pass
```

### Antipattern: Using `**kwargs: dict[str, Any]` and manual validation

```python
from typing import Any

# ❌ Runtime validation only
def process(
    required: str,
    **kwargs: dict[str, Any]
) -> None:
    timeout = kwargs.get("timeout", 30)
    if not isinstance(timeout, int):
        raise TypeError("timeout must be int")
    # Manual validation for each field...

process("x", timeout="slow")  # Runtime error

# ✅ Static checking with Unpack
from typing import TypedDict, Unpack

class ProcessOptions(TypedDict, total=False):
    timeout: int

def process(required: str, **kwargs: Unpack[ProcessOptions]) -> None:
    timeout = kwargs.get("timeout", 30)  # int guaranteed by type checker

process("x", timeout="slow")  # Type error at check time
```

## Source anchors

- [PEP 692 — Using TypedDict for more precise **kwargs typing](https://peps.python.org/pep-0692/)
- [typing module — Unpack](https://docs.python.org/3/library/typing.html#typing.Unpack)
- [typing_extensions backport](https://typing-extensions.readthedocs.io/en/latest/#Unpack)
- [mypy docs — TypedDict and Unpack](https://mypy.readthedocs.io/en/stable/typed_dict.html)
- [pyright docs — PEP 692 support](https://microsoft.github.io/pyright/#/)
