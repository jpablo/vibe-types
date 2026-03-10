# NewType

## What it is

`NewType` creates a distinct type for the type checker while being a no-op at runtime. Given `UserId = NewType("UserId", int)`, the checker treats `UserId` as a separate type from `int`: you cannot pass a bare `int` where `UserId` is expected, and you cannot interchange `UserId` with `OrderId = NewType("OrderId", int)`. At runtime, `UserId(42)` simply returns `42` — there is no wrapper class, no extra allocation, and no performance cost. This makes NewType ideal for "branded" or "tagged" primitives that prevent semantic mix-ups.

**Since:** Python 3.5.2 (PEP 484); callable form clarified in typing spec

## What constraint it enforces

**Values of the underlying type are not interchangeable with the new type; explicit wrapping is required, preventing accidental mix-ups of semantically different values that share the same base type.**

The checker enforces a one-way relationship: `UserId` is a subtype of `int` (so you can pass a `UserId` where `int` is expected), but `int` is *not* a subtype of `UserId` (so you cannot pass a bare `int` where `UserId` is expected). This asymmetry catches the most common class of bugs — passing the wrong ID, the wrong measurement, or the wrong string — while still allowing NewType values to participate in operations defined on the base type.

## Minimal snippet

```python
from typing import NewType

UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)

def get_user(uid: UserId) -> str: ...

get_user(UserId(42))   # OK — explicitly wrapped
get_user(42)           # error: Argument 1 has incompatible type "int"; expected "UserId"
get_user(OrderId(42))  # error: Argument 1 has incompatible type "OrderId"; expected "UserId"
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Basic annotations** [-> [catalog/01](01-basic-annotations-none.md)] | NewType builds directly on the annotation system — it adds a named type that wraps a base annotation. |
| **Dataclasses** [-> [catalog/06](06-dataclasses-typing.md)] | When you need methods, multiple fields, or richer behavior, a dataclass (or `@dataclass` with a single field) is a heavier but more capable alternative to NewType. |
| **Literal** [-> [catalog/02](02-union-literal-types.md)] | `Literal` constrains values; `NewType` constrains types. They address different problems: Literal restricts *which* values, NewType restricts *which meaning*. |
| **Generics** [-> [catalog/07](07-generics-typevar.md)] | You can use a NewType as a type argument: `list[UserId]` is distinct from `list[int]` to the checker. |

## Gotchas and limitations

1. **No methods or attributes.** `NewType` creates a type alias, not a class. You cannot add methods, properties, or class variables to a NewType. If you need behavior, use a class or dataclass instead.

2. **No `isinstance` / `issubclass` checks.** Because NewType vanishes at runtime, `isinstance(x, UserId)` raises `TypeError` (it is not a class). You cannot use it for runtime type dispatch.

3. **Arithmetic erases the NewType.** `UserId(1) + UserId(2)` returns `int`, not `UserId`, because `int.__add__` returns `int`. The checker tracks this correctly — the result needs re-wrapping if you want it to stay a `UserId`.

4. **mypy vs pyright divergence.** pyright treats NewType as a class-like construct and provides better IDE support (hover types, go-to-definition). mypy treats it as a callable. Errors look slightly different:

   ```
   # mypy
   error: Argument 1 to "get_user" has incompatible type "int"; expected "UserId"

   # pyright
   error: Argument of type "int" cannot be assigned to parameter "uid" of type "UserId"
   ```

5. **Cannot create NewType of NewType (mypy limitation).** `Priority = NewType("Priority", UserId)` may work in pyright but mypy historically had issues with stacked NewTypes. Check your checker's version.

6. **Serialization transparency.** Since `UserId(42)` is just `42` at runtime, JSON serialization, database queries, and other runtime operations see plain `int`. This is usually a feature (zero overhead), but means runtime validation is your responsibility.

## Beginner mental model

Think of NewType as **putting a colored sticker on a value**. A `UserId` is an `int` with a "user-id" sticker. The type checker can see the sticker and will complain if you try to use a "user-id" sticker where an "order-id" sticker is expected. At runtime, the sticker does not exist — it is purely a compile-time label. This gives you mix-up protection for free.

## Example A — UserId vs OrderId preventing mix-ups

```python
from typing import NewType

UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)


def cancel_order(order_id: OrderId, cancelled_by: UserId) -> None:
    print(f"Order {order_id} cancelled by user {cancelled_by}")


user = UserId(1001)
order = OrderId(5042)

cancel_order(order, user)    # OK — correct types in correct positions
cancel_order(user, order)    # error: arguments swapped!
# mypy:    error: Argument 1 has incompatible type "UserId"; expected "OrderId"
# pyright: error: Argument of type "UserId" cannot be assigned to parameter
#          "order_id" of type "OrderId"


# NewType values work wherever the base type is accepted:
all_ids: list[int] = [user, order]  # OK — both are subtypes of int
```

## Example B — Sanitized string type for XSS prevention

```python
from typing import NewType

# A string that has been HTML-escaped and is safe to embed in HTML.
SafeHtml = NewType("SafeHtml", str)


def render_page(title: str, body: SafeHtml) -> str:
    return f"<html><head><title>{title}</title></head><body>{body}</body></html>"


def sanitize(raw: str) -> SafeHtml:
    """Escape HTML special characters and return a SafeHtml value."""
    import html
    return SafeHtml(html.escape(raw))


user_input = "<script>alert('xss')</script>"

# Direct use is rejected:
render_page("Home", user_input)  # error: expected "SafeHtml", got "str"

# Must go through sanitization:
safe = sanitize(user_input)
render_page("Home", safe)        # OK

# Safe values still work as regular strings:
print(safe.upper())              # OK — SafeHtml is a subtype of str
log_message: str = safe          # OK — assignment to base type is allowed
```

## Common type-checker errors and how to read them

### Passing base type where NewType expected

```
# mypy
error: Argument 1 to "get_user" has incompatible type "int"; expected "UserId"

# pyright
error: Argument of type "int" cannot be assigned to parameter "uid" of type "UserId"
```

**Cause:** You passed a bare value of the underlying type without wrapping it.
**Fix:** Wrap the value: `get_user(UserId(42))`.

### Swapping two NewTypes of the same base

```
# mypy
error: Argument 1 has incompatible type "UserId"; expected "OrderId"
```

**Cause:** Two NewTypes built on the same base type are not interchangeable. You passed the wrong one.
**Fix:** Check the argument order and use the correct NewType.

### isinstance with NewType

```
TypeError: isinstance() arg 2 cannot be a parameterized generic
```

**Cause:** `isinstance(x, UserId)` fails at runtime because `UserId` is not a real class.
**Fix:** Check against the base type: `isinstance(x, int)`. If you need to distinguish NewType values at runtime, use a wrapper class or dataclass instead.

### Arithmetic result is base type, not NewType

```
# pyright
error: Type "int" is not assignable to type "UserId"
```

**Cause:** `UserId(1) + UserId(2)` returns `int`, not `UserId`.
**Fix:** Re-wrap the result: `UserId(uid1 + uid2)` if the operation is semantically meaningful.

## Use-case cross-references

- [-> UC-01](../usecases/01-preventing-invalid-states.md) — Public API signatures that distinguish semantic types.
- [-> UC-02](../usecases/02-domain-modeling.md) — Data pipeline stages where IDs and measurements must not be confused.

## Source anchors

- [PEP 484 — Type Hints (NewType section)](https://peps.python.org/pep-0484/#newtype-helper-function)
- [typing module — NewType](https://docs.python.org/3/library/typing.html#typing.NewType)
- [typing spec — NewType](https://typing.readthedocs.io/en/latest/spec/aliases.html#newtype)
- [mypy — NewType](https://mypy.readthedocs.io/en/stable/more_types.html#newtypes)
