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
| **Basic annotations** [-> [catalog/01](T13-null-safety.md)] | NewType builds directly on the annotation system — it adds a named type that wraps a base annotation. |
| **Dataclasses** [-> [catalog/06](T06-derivation.md)] | When you need methods, multiple fields, or richer behavior, a dataclass (or `@dataclass` with a single field) is a heavier but more capable alternative to NewType. |
| **Literal** [-> [catalog/02](T02-union-intersection.md)] | `Literal` constrains values; `NewType` constrains types. They address different problems: Literal restricts *which* values, NewType restricts *which meaning*. |
| **Generics** [-> [catalog/07](T04-generics-bounds.md)] | You can use a NewType as a type argument: `list[UserId]` is distinct from `list[int]` to the checker. |

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

- [-> UC-01](../usecases/UC01-invalid-states.md) — Public API signatures that distinguish semantic types.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Data pipeline stages where IDs and measurements must not be confused.

## Source anchors

- [PEP 484 — Type Hints (NewType section)](https://peps.python.org/pep-0484/#newtype-helper-function)
- [typing module — NewType](https://docs.python.org/3/library/typing.html#typing.NewType)
- [typing spec — NewType](https://typing.readthedocs.io/en/latest/spec/aliases.html#newtype)
- [mypy — NewType](https://mypy.readthedocs.io/en/stable/more_types.html#newtypes)

## When to Use

Use `NewType` when you need compile-time separation of semantically distinct values that share the same runtime type:

```python
from typing import NewType

# Different semantic meanings for same runtime type
UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)
GroupId = NewType("GroupId", int)


def assign_user_to_group(user: UserId, group: GroupId) -> None:
    pass


def transfer_order(user: UserId, order: OrderId) -> None:
    pass


# The type checker catches swapped arguments:
assign_user_to_group(UserId(1), OrderId(2))  # error: expected GroupId


# Use for units and measurements:
Meters = NewType("Meters", float)
Seconds = NewType("Seconds", float)


def velocity(distance: Meters, time: Seconds) -> float:
    return distance / time


velocity(Seconds(10.0), Meters(2.0))  # error: arguments swapped by unit
```

**Guiding principle:** When swapping two arguments of the same base type would cause bugs that are hard to catch in testing, use NewType to make those bugs compile-time errors.

## When Not to Use

**Don't use** for values that don't need compile-time enforcement. Simple type aliases are clearer:

```python
# Bad: overkill for simple naming
StreetAddress = NewType("StreetAddress", str)
City = NewType("City", str)


def mail_to(address: StreetAddress, city: City) -> None:
    pass


# Good: runtime validation when needed
def mail_to(address: str, city: str) -> None:
    if not address:
        raise ValueError("Address required")
    if not city:
        raise ValueError("City required")
```

**Don't use** when the semantic difference is trivial and errors are easily caught:

```python
# Unnecessary: obvious from context
ButtonLabel = NewType("ButtonLabel", str)
InputLabel = NewType("InputLabel", str)


def render_ui(button: ButtonLabel, input_label: InputLabel) -> str:
    return f"<button>{button}</button><label>{input_label}</label>"
```

Swapping "Click" and "Name" is obvious in tests and code review; NewType adds boilerplate without value.

## Antipatterns When Using NewType

### Antipattern 1: Scattered wrapper calls

```python
from typing import NewType

Price = NewType("Price", float)


def calculate_total(items: list[Price]) -> Price:
    total = 0.0
    for item in items:
        # ❌ Each arithmetic operation loses the type
        total = Price(total + item)  # verbose, error-prone
    return Price(total)


# ✅ Collect then wrap once
def calculate_total(items: list[Price]) -> Price:
    return Price(sum(item for item in items))
```

**Problem:** Repeated wrapping obscures the logic and is tedious. It also creates a false sense of safety — the typechecker accepts `Price(x + y)` even if `x + y` is semantically invalid.

### Antipattern 2: Using NewType for runtime validation

```python
from typing import NewType

Email = NewType("Email", str)


def send_email(recipient: Email, message: str) -> None:
    pass


# ❌ NewType doesn't validate at runtime
send_email(Email("not-an-email"), "Hello")  # compiles, but invalid!
```

**Problem:** Developers may assume NewType validates, but `Email("anything")` always succeeds at runtime. Use NewType to force the *act* of validation elsewhere, not as validation itself.

**Fix:** Combine with a separate function whose contract is validation:

```python
def validate_email(raw: str) -> Email:
    import re
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", raw):
        raise ValueError(f"Invalid email: {raw}")
    return Email(raw)


send_email(validate_email("user@example.com"), "Hello")  # OK
```

### Antipattern 3: Overusing NewType for trivial distinctions

```python
from typing import NewType

FirstName = NewType("FirstName", str)
LastName = NewType("LastName", str)
MiddleName = NewType("MiddleName", str)
Email = NewType("Email", str)
Phone = NewType("Phone", str)
Address = NewType("Address", str)
City = NewType("City", str)
State = NewType("State", str)
ZipCode = NewType("ZipCode", str)
Country = NewType("Country", str)


def create_user(
    first: FirstName, last: LastName, middle: MiddleName, email: Email,
    phone: Phone, address: Address, city: City, state: State,
    zip_: ZipCode, country: Country
) -> None:
    pass
```

**Problem:** Excessive NewTypes create tedious call sites without proportional safety benefits. A dataclass with runtime validation is clearer:

```python
from dataclasses import dataclass


@dataclass
class Address:
    street: str
    city: str
    state: str
    zip_code: str
    country: str

    def __post_init__(self) -> None:
        if not self.street:
            raise ValueError("Street required")
        # ...


@dataclass
class User:
    first_name: str
    last_name: str
    middle_name: str | None
    email: str
    phone: str
    address: Address

    def __post_init__(self) -> None:
        self._validate()


def _validate(self) -> None:
    import re
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", self.email):
        raise ValueError("Invalid email")
```

### Antipattern 4: Forgetting arithmetic erases the type

```python
from typing import NewType

Minutes = NewType("Minutes", int)


def add_times(a: Minutes, b: Minutes) -> Minutes:
    # ❌ This returns int, not Minutes
    return a + b  # type: ignore needed


# ✅ Wrap the result
def add_times(a: Minutes, b: Minutes) -> Minutes:
    return Minutes(a + b)
```

**Problem:** Arithmetic operations on NewType values return the base type, not the NewType. Forgetting to re-wrap leads to downstream type errors.

## Antipatterns Where NewType Fixes Them

### Antipattern: Function with ambiguous integer parameters

```python
from typing import NewType


# ❌ Easy to swap arguments — both are int
def set_pagination(page: int, per_page: int) -> list[str]:
    return [f"page_{page}_{per_page}"]


set_pagination(20, 2)   # intended: page=2, per_page=20
set_pagination(2, 20)   # easy to mix up


# ✅ NewType makes them distinct
PageNumber = NewType("PageNumber", int)
PageSize = NewType("PageSize", int)


def set_pagination(page: PageNumber, per_page: PageSize) -> list[str]:
    return [f"page_{page}_{per_page}"]


set_pagination(PageNumber(2), PageSize(20))  # OK
# set_pagination(PageSize(20), PageNumber(2))  # error: expected PageNumber
```

### Antipattern: Magic numbers without units

```python
from typing import NewType


# ❌ What units? Milliseconds? Seconds?
def set_timeout(delay: int) -> None:
    pass


set_timeout(1000)  # 1 second? 1000 seconds?


# ✅ NewType encodes units
Milliseconds = NewType("Milliseconds", int)


def set_timeout(delay: Milliseconds) -> None:
    pass


set_timeout(Milliseconds(1000))  # clear: 1000ms
# set_timeout(1000)  # error: expected Milliseconds
```

### Antipattern: Unvalidated string passing between layers

```python
from typing import NewType


# ❌ Raw string flows freely — validation is easy to skip
def render_template(template: str, user_input: str) -> str:
    return f"<div>{user_input}</div>"  # XSS risk


render_template("home", "<script>alert('xss')</script>")


# ✅ NewType forces explicit sanitization step
SafeString = NewType("SafeString", str)


def sanitize_html(raw: str) -> SafeString:
    import html
    return SafeString(html.escape(raw))


def render_template(template: str, user_input: SafeString) -> str:
    return f"<div>{user_input}</div>"  # type system ensures escaping


render_template("home", "<script>alert('xss')</script>")  # error: expected SafeString
render_template("home", sanitize_html("<script>alert('xss')</script>"))  # OK
```

### Antipattern: Confusing semantically distinct IDs

```python
from typing import NewType


# ❌ Database IDs are all int or str — easy to pass wrong ID
def delete_user(user_id: int) -> None:
    pass


def delete_order(order_id: int) -> None:
    pass


def assign_order_to_user(user_id: int, order_id: int) -> None:
    pass


user_id_from_request = 1001
order_id_from_request = 5042

# All of these compile — only tests catch the bug:
delete_user(order_id_from_request)  # BUG: deleting order instead of user
assign_order_to_user(order_id_from_request, user_id_from_request)  # args swapped


# ✅ NewType distinguishes the IDs
UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)


def delete_user(user_id: UserId) -> None:
    pass


def delete_order(order_id: OrderId) -> None:
    pass


def assign_order_to_user(user_id: UserId, order_id: OrderId) -> None:
    pass


user_id = UserId(user_id_from_request)
order_id = OrderId(order_id_from_request)

delete_user(user_id)  # OK
# delete_user(order_id)  # error: incompatible type
# assign_order_to_user(order_id, user_id)  # error: arguments swapped
```

### Antipattern: Enum strings passed to unrelated functions

```python
from typing import NewType


# ❌ Any string accepted — invalid currency values compile
def convert_amount(amount: float, currency: str) -> float:
    rates = {"USD": 1.0, "EUR": 0.85, "GBP": 0.73}
    return amount * rates[currency]  # KeyError at runtime


convert_amount(100, "BTC")  # compile, runtime error


# ✅ NewType + validation function as single entry point
CurrencyCode = NewType("CurrencyCode", str)


VALID_CURRENCIES = frozenset({"USD", "EUR", "GBP"})


def make_currency(code: str) -> CurrencyCode:
    if code not in VALID_CURRENCIES:
        raise ValueError(f"Invalid currency: {code}")
    return CurrencyCode(code)


def convert_amount(amount: float, currency: CurrencyCode) -> float:
    rates = {"USD": 1.0, "EUR": 0.85, "GBP": 0.73}
    return amount * rates[currency]


convert_amount(100, "BTC")  # error: expected CurrencyCode
convert_amount(100, make_currency("USD"))  # OK
# convert_amount(100, make_currency("BTC"))  # ValueError at construction
```
