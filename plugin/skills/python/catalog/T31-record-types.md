# TypedDict

## What it is

`TypedDict` lets you declare the shape of a dictionary: which keys must or may exist, and what type each value must have. Unlike a regular `dict[str, Any]`, a TypedDict annotation gives the type checker per-key type information, catching missing keys, extra keys, and wrong value types at check time. Python 3.8 (PEP 589) introduced the basic form; Python 3.11 (PEP 655) added `Required` and `NotRequired` markers for fine-grained control over individual keys; Python 3.13 (PEP 705) added `ReadOnly` for immutable fields.

**Since:** Python 3.8 (PEP 589); `Required`/`NotRequired` — Python 3.11 (PEP 655); `ReadOnly` — Python 3.13 (PEP 705)

## What constraint it enforces

**Dictionary keys, value types, and required/optional presence are verified statically; accessing an undeclared key or assigning a wrong-typed value is an error.**

The checker treats a TypedDict as a structural type: it knows exactly which keys exist, what types they hold, and whether each key is required or optional. This prevents the class of bugs where a key is misspelled, forgotten, or given a value of the wrong type — all of which would silently succeed with a plain `dict`.

## Minimal snippet

```python
from typing import TypedDict


class Point(TypedDict):
    x: float
    y: float


p: Point = {"x": 1.0, "y": 2.0}       # OK
p2: Point = {"x": 1.0}                  # error: Missing key "y"
p3: Point = {"x": 1.0, "y": 2.0, "z": 3.0}  # error: Extra key "z"
p["x"] = "hello"                        # error: Value of "x" has incompatible type "str"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Literal types** [-> [catalog/02](T02-union-intersection.md)] | `Literal` values often serve as discriminator keys in tagged-union patterns: `Union[SuccessResponse, ErrorResponse]` where each TypedDict has a `Literal["ok"]` or `Literal["error"]` type field. |
| **Annotated** [-> [catalog/15](T26-refinement-types.md)] | `Annotated[str, MaxLen(100)]` can be used as a TypedDict value type to carry runtime validation metadata alongside the static type. |
| **Unpack / **kwargs** [-> [catalog/19](T46-kwargs-typing.md)] | `**kwargs: Unpack[MyTypedDict]` (PEP 692) lets you type individual keyword arguments via a TypedDict. |
| **Union** [-> [catalog/02](T02-union-intersection.md)] | TypedDicts are commonly used as members of a Union for structured variant types (e.g., different API response shapes). |
| **Protocol** [-> [catalog/09](T07-structural-typing.md)] | TypedDict is itself a form of structural typing for dicts — it shares the "shape over name" philosophy with Protocols. |

## Gotchas and limitations

1. **TypedDicts are not classes at runtime.** They are regular `dict` instances. You cannot add methods, use `isinstance` checks (unless you use `typing.is_typeddict` from 3.12+), or use inheritance for logic.

2. **`total=True` is the default.** All keys are required unless you use `total=False` (which makes *all* keys optional) or use per-key `Required`/`NotRequired` markers (3.11+). Mixing the two models is a common source of confusion.

3. **No recursive TypedDicts (limited support).** Defining a TypedDict that references itself (e.g., a tree node) requires forward references and has uneven checker support. mypy has partial support; pyright handles it better.

4. **Structural compatibility is loose.** A plain `dict[str, Any]` is *not* automatically compatible with a TypedDict, but a TypedDict *is* compatible with `Mapping[str, object]`. This asymmetry catches people off guard when passing dicts to functions that expect TypedDicts.

5. **Extra keys handling varies.** mypy rejects extra keys in TypedDict literals. pyright also rejects them in direct construction but may be more lenient in some assignment contexts. Neither checker prevents extra keys at runtime.

6. **Inheritance.** TypedDicts support inheritance to extend shapes, but multiple inheritance from TypedDicts with overlapping keys of different types is an error.

## Beginner mental model

Think of a TypedDict as a **form with labeled fields**. Each field has a name (the key), a required type for the value, and may be marked optional. The type checker acts like a form validator: it ensures every required field is filled in, no unknown fields are added, and every value has the correct type. At runtime, though, it is still just a regular Python dict — the form is a compile-time overlay.

## Example A — API response with required and optional fields

```python
from typing import NotRequired, TypedDict


class UserResponse(TypedDict):
    id: int
    username: str
    email: str
    bio: NotRequired[str]          # optional — may be absent
    avatar_url: NotRequired[str]   # optional


def display_user(user: UserResponse) -> str:
    # Required keys are always safe to access
    header = f"{user['username']} (#{user['id']})"     # OK

    # Optional keys need a .get() or `in` check
    bio = user.get("bio", "No bio provided")           # OK
    # Direct access without check:
    # user["bio"]  # OK for the checker, but may raise KeyError at runtime
    #              # (checkers trust the TypedDict shape, not runtime presence)

    return f"{header}: {bio}"


# Construction
valid: UserResponse = {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
}  # OK — NotRequired fields can be omitted

invalid: UserResponse = {
    "id": 1,
    "username": "alice",
}  # error: Missing key "email"
```

## Example B — Configuration dict with NotRequired and defaults

```python
from typing import NotRequired, Required, TypedDict


class DBConfig(TypedDict, total=False):
    """All keys optional by default (total=False), except those marked Required."""
    host: Required[str]
    port: int                    # optional because total=False
    database: Required[str]
    timeout_seconds: int         # optional
    ssl: bool                    # optional


def connect(config: DBConfig) -> str:
    host = config["host"]                             # OK — Required
    port = config.get("port", 5432)                   # OK — has default
    db = config["database"]                           # OK — Required
    timeout = config.get("timeout_seconds", 30)       # OK — has default
    use_ssl = config.get("ssl", True)                 # OK — has default
    return f"{host}:{port}/{db}?timeout={timeout}&ssl={use_ssl}"


# Valid: only required keys
c1: DBConfig = {"host": "localhost", "database": "mydb"}  # OK

# Valid: all keys
c2: DBConfig = {
    "host": "localhost",
    "port": 5433,
    "database": "mydb",
    "timeout_seconds": 10,
    "ssl": False,
}  # OK

# Invalid: missing required key
c3: DBConfig = {"host": "localhost"}  # error: Missing key "database"
```

## Common type-checker errors and how to read them

### Missing key

```
# mypy
error: Missing key "email" for TypedDict "UserResponse"

# pyright
error: "email" is missing from "UserResponse"
```

**Cause:** A required key was not provided in the TypedDict literal.
**Fix:** Add the missing key, or mark it `NotRequired` if it should be optional.

### Extra key

```
# mypy
error: Extra key "z" for TypedDict "Point"

# pyright
error: "z" is not a valid key in "Point"
```

**Cause:** You included a key that is not declared in the TypedDict.
**Fix:** Remove the extra key, or add it to the TypedDict definition if it is intentional.

### Wrong value type

```
# mypy
error: Incompatible types (expression has type "str", TypedDict item "x" has type "float")

# pyright
error: Type "str" is not assignable to type "float"
```

**Cause:** The value assigned to a key does not match the declared type.
**Fix:** Fix the value or update the type annotation.

### TypedDict not compatible with dict

```
# mypy
error: Argument 1 to "f" has incompatible type "dict[str, int]";
       expected "MyTypedDict"

# pyright
error: "dict[str, int]" is not assignable to "MyTypedDict"
```

**Cause:** A plain dict cannot be assigned to a TypedDict parameter because the checker cannot verify its keys.
**Fix:** Construct the TypedDict explicitly, or cast with `cast(MyTypedDict, d)` if you are confident about the shape. Prefer explicit construction.

## Use-case cross-references

- [-> UC-02](../usecases/UC02-domain-modeling.md) — Typed data pipelines: ensuring dict shapes through transformation stages.
- [-> UC-09](../usecases/UC09-builder-config.md) — API response typing for REST clients.

## Source anchors

- [PEP 589 — TypedDict: Type Hints for Dictionaries with a Fixed Set of Keys](https://peps.python.org/pep-0589/)
- [PEP 655 — Marking individual TypedDict items as required or potentially-missing](https://peps.python.org/pep-0655/)
- [PEP 705 — TypedDict: Read-only items](https://peps.python.org/pep-0705/)
- [typing spec — TypedDict](https://typing.readthedocs.io/en/latest/spec/typeddict.html)
- [mypy — TypedDict](https://mypy.readthedocs.io/en/stable/typed_dict.html)
