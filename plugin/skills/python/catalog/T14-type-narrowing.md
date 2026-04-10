# TypeGuard, TypeIs, and Type Narrowing

> **Since:** `TypeGuard` Python 3.10 (PEP 647); `TypeIs` Python 3.13 (PEP 742); built-in narrowing (`isinstance`, `assert`) all versions | **Backport:** `typing_extensions`

## What it is

Type narrowing is the process by which a type checker learns that a variable has a more specific type inside a conditional branch. Python's checkers automatically narrow after `isinstance()`, `issubclass()`, `is None`, `is not None`, `assert`, and `match`/`case`. When built-in narrowing is not expressive enough, `TypeGuard` and `TypeIs` let you write custom boolean functions that the checker trusts as narrowing predicates. The critical difference: `TypeGuard` narrows only in the `if True` branch, while `TypeIs` narrows in both the `if True` and `if False` branches, enabling exhaustiveness checking.

## What constraint it enforces

**The type checker restricts a variable's type inside conditional branches based on narrowing predicates, rejecting operations that are invalid for the narrowed type and enabling exhaustive branch analysis when all variants are covered.**

## Minimal snippet

```python
from typing import TypeGuard, TypeIs

def is_str_list(val: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in val)

def check(data: list[object]) -> None:
    if is_str_list(data):
        print(data[0].upper())    # OK — narrowed to list[str]
    else:
        print(data[0].upper())    # error — still list[object], no .upper()
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Optional / None** [-> catalog/01](T13-null-safety.md) | `if x is not None` narrows `X \| None` to `X`. This is the most common built-in narrowing pattern. |
| **Union / Literal** [-> catalog/02](T02-union-intersection.md) | `isinstance` and `match`/`case` narrow Union types branch by branch. `TypeIs` enables exhaustive narrowing of discriminated unions. |
| **Enum** [-> catalog/05](T01-algebraic-data-types.md) | Matching on all enum members with `match`/`case` or `if`/`elif` chains gives exhaustiveness when combined with `assert_never`. |
| **Never / NoReturn** [-> catalog/14](T34-never-bottom.md) | `assert_never()` accepts only `Never` — if the checker can prove a branch is unreachable, the argument type narrows to `Never` and the call is accepted. If any variant is unhandled, the argument type is not `Never` and the checker flags an error. |

## Gotchas and limitations

1. **`TypeGuard` narrows only the positive branch.** In the `else` branch, the original type is unchanged. This is the most common surprise.

   ```python
   def is_int(x: int | str) -> TypeGuard[int]:
       return isinstance(x, int)

   def f(val: int | str) -> None:
       if is_int(val):
           reveal_type(val)   # int
       else:
           reveal_type(val)   # int | str  (NOT str!)
   ```

2. **`TypeIs` narrows both branches but requires the narrowed type to be a subtype of the input type.** You cannot use `TypeIs[list[str]]` to narrow `list[object]` because `list[str]` is not a subtype of `list[object]` (lists are invariant). Use `TypeGuard` for such cases.

3. **Custom narrowing functions are trusted, not verified.** The checker does not prove that your `TypeGuard` or `TypeIs` function actually returns `True` only for the declared type. A wrong implementation silently produces unsound narrowing.

4. **`isinstance` with generics is limited.** You cannot write `isinstance(x, list[str])` at runtime — generic aliases are not valid for `isinstance`. Use a `TypeGuard` function instead.

5. **Narrowing does not persist across function calls.** If you call a function between the `isinstance` check and the use of the variable, the checker may widen the type back because the function could mutate the variable.

6. **pyright is more aggressive with narrowing than mypy.** pyright narrows in more contexts (e.g., after `assert isinstance(...)` inside comprehensions). Code that type-checks with pyright may produce errors under mypy.

## Beginner mental model

Narrowing is the checker's ability to **zoom in on a type** inside an `if` branch. If you ask "is this a string?" and the answer is yes, the checker knows it is a `str` inside that branch. `TypeGuard` is a way to teach the checker new "yes" questions — but only for the "yes" branch. `TypeIs` teaches both the "yes" and "no" sides, so the checker can confirm you handled every possibility.

## Example A — Custom TypeGuard for validating JSON shapes

```python
from typing import Any, TypeGuard

# Raw JSON data comes in as dict[str, Any]
type JsonDict = dict[str, Any]

class UserRecord:
    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age

def is_user_json(data: JsonDict) -> TypeGuard[dict[str, str | int]]:
    """Validate that the dict has the shape expected for a UserRecord."""
    return (
        isinstance(data.get("name"), str)
        and isinstance(data.get("age"), int)
    )

def process(raw: JsonDict) -> str:
    if is_user_json(raw):
        # Narrowed — checker knows "name" is str, "age" is int
        return f"User: {raw['name']}, age {raw['age']}"
    raise ValueError("Invalid user JSON")

# In practice, pair with Pydantic or similar for runtime validation.
# TypeGuard bridges the gap between "I validated this at runtime"
# and "the checker should trust me."
```

## Example B — TypeIs for discriminated union narrowing with exhaustiveness

```python
from typing import TypeIs, assert_never

class Dog:
    sound = "woof"
class Cat:
    sound = "meow"
class Fish:
    sound = "blub"

type Pet = Dog | Cat | Fish

def is_dog(pet: Pet) -> TypeIs[Dog]:
    return isinstance(pet, Dog)

def is_cat(pet: Pet) -> TypeIs[Cat]:
    return isinstance(pet, Cat)

def describe(pet: Pet) -> str:
    if is_dog(pet):
        return f"Dog says {pet.sound}"      # OK — narrowed to Dog
    elif is_cat(pet):
        return f"Cat says {pet.sound}"      # OK — narrowed to Cat
    else:
        # TypeIs narrows the else branch: pet is now Fish
        reveal_type(pet)                     # Fish
        return f"Fish says {pet.sound}"

# Exhaustiveness with assert_never — catches missing branches
def describe_strict(pet: Pet) -> str:
    if is_dog(pet):
        return "dog"
    elif is_cat(pet):
        return "cat"
    # If we forget Fish, the else branch has type Fish, not Never
    else:
        assert_never(pet)  # error — argument of type "Fish" is not "Never"
```

Using `match`/`case` for the same pattern (Python 3.10+):

```python
def describe_match(pet: Pet) -> str:
    match pet:
        case Dog():
            return "dog"
        case Cat():
            return "cat"
        case Fish():
            return "fish"
        # No default needed — checker knows all cases are covered
```

## Common type-checker errors and how to read them

### `error: Argument 1 to "assert_never" has incompatible type "X"; expected "Never"` (mypy)

You have an unhandled variant `X` in your narrowing chain. Add a branch for `X` before the `assert_never` call.

### `error: "X" has no attribute "y"` after narrowing

The narrowing did not produce the type you expected. Common causes: (a) using `TypeGuard` and checking in the `else` branch where narrowing does not apply, (b) the `isinstance` check used a base class instead of the specific class.

### `Narrowed type "X" is not a subtype of input type "Y"` (pyright, with TypeIs)

`TypeIs` requires the narrowed type to be a proper subtype of the parameter type. If you are narrowing `list[object]` to `list[str]`, use `TypeGuard` instead (lists are invariant, so `list[str]` is not a subtype of `list[object]`).

### `error: Condition is always true / always false`

The checker determined that a narrowing condition can never fail (or always fails), which suggests the type annotation upstream is too narrow or too wide.

### `Statement is unreachable` (pyright)

A branch after exhaustive narrowing is flagged as dead code. This is usually correct and means your narrowing is complete. If unexpected, check whether the union has fewer members than you thought.

## Use-case cross-references

- [-> UC-03](../usecases/UC03-exhaustiveness.md) — Parsing and validation pipelines that narrow raw input into domain types.
- [-> UC-08](../usecases/UC08-error-handling.md) — Exhaustive handling of command/event unions in state machines.

## Source anchors

- [PEP 647 — User-Defined Type Guards](https://peps.python.org/pep-0647/) — `TypeGuard`
- [PEP 742 — Narrowing types with TypeIs](https://peps.python.org/pep-0742/) — `TypeIs`
- [typing spec — Type narrowing](https://typing.readthedocs.io/en/latest/spec/narrowing.html)
- [mypy docs — Type narrowing](https://mypy.readthedocs.io/en/stable/type_narrowing.html)
- [mypy docs — TypeGuard](https://mypy.readthedocs.io/en/stable/type_narrowing.html#user-defined-type-guards)

## When to Use It

- **Handling discriminated unions**: Use `match`/`case` or `TypeIs` guards to safely access variant-specific attributes.

  ```python
  from typing import TypeIs

  class Add:
      def __init__(self, a: int, b: int):
          self.a, self.b = a, b

  class Mul:
      def __init__(self, a: int, b: int):
          self.a, self.b = a, b

  def is_add(op: Add | Mul) -> TypeIs[Add]:
      return isinstance(op, Add)

  def evaluate(op: Add | Mul) -> int:
      if is_add(op):
          return op.a + op.b
      return op.a * op.b
  ```

- **Validating external data**: Use `TypeGuard` or `TypeIs` to transition from `dict[str, Any]` to known structures.

  ```python
  from typing import Any, TypeGuard

  def is_user(data: dict[str, Any]) -> TypeGuard[dict[str, str]]:
      return isinstance(data.get("id"), str)

  def load(raw: dict[str, Any]) -> str:
      if is_user(raw):
          return raw["id"]
  ```

- **Ensuring exhaustiveness**: Use `TypeIs` with `assert_never` to catch missing cases at typing time.

  ```python
  from typing import TypeIs, assert_never

  type Status = "idle" | "loading" | "done"

  def is_idle(s: Status) -> TypeIs["idle"]:
      return s == "idle"

  def render(s: Status) -> str:
      if is_idle(s):
          return "Idle"
      elif s == "loading":
          return "Loading…"
      elif s == "done":
          return "Done"
      else:
          assert_never(s)
  ```

- **Guarding Optional values**: Use `is not None` or truthiness to remove `None` from unions.

  ```python
  def first_char(s: str | None) -> str:
      if s is not None:
          return s[0]
      return " "
  ```

- **Filtering collections by type**: Use `TypeGuard` to filter heterogeneous lists.

  ```python
  from typing import TypeGuard

  def is_str(x: int | str) -> TypeGuard[str]:
      return isinstance(x, str)

  def filter_strs(items: list[int | str]) -> list[str]:
      return [x for x in items if is_str(x)]
  ```

## When Not to Use It

- **Inside closures or async after a `let`-like variable**: Narrowing is lost; use a `const` copy or `match` instead.

  ```python
  def render(value: str | None) -> None:
      if value is not None:
          import threading
          threading.Timer(0, lambda: print(len(value))).start()
          # mypy/pyright may warn: value could be reassigned
  ```

- **Overengineering simple open-ended data**: Exhaustiveness is overkill for open string values.

  ```python
  def color_to_hex(c: "red" | "blue" | str) -> str:
      # Using TypeIs here would be overkill
      # because the union is intentionally open-ended
      if c == "red":
          return "#f00"
      if c == "blue":
          return "#00f"
      return "#000"  # Fallback is fine
  ```

- **When using `TypeGuard` where `TypeIs` is needed for exhaustiveness**: If you need both branches narrowed, use `TypeIs`.

  ```python
  from typing import TypeGuard

  # Wrong: TypeGuard doesn't narrow the else branch
  def is_int(x: int | str) -> TypeGuard[int]:
      return isinstance(x, int)

  def process(val: int | str) -> None:
      if is_int(val):
          val + 1  # OK
      else:
          reveal_type(val)  # int | str, NOT str
  ```

## Antipatterns When Using Type Narrowing

### 1. Truthiness narrowing for `0`, `""`, or `False`

```python
# Bad: loses valid 0/""/False values
def process(n: int | None) -> None:
    if n:
        print(n + 1)  # Misses n == 0

# Good: explicit None check
def process_fixed(n: int | None) -> None:
    if n is not None:
        print(n + 1)
```

### 2. Redundant narrowing checks

```python
# Bad: redundant checks
def describe(x: str | int) -> None:
    if isinstance(x, str):
        if isinstance(x, str):  # Redundant
            print(x.upper())

# Good: single check
def describe_fixed(x: str | int) -> None:
    if isinstance(x, str):
        print(x.upper())
```

### 3. Type guard on a non-discriminative attribute

```python
# Bad: attribute exists on all variants
class Cat:
    def __init__(self, name: str):
        self.name = name

class Dog:
    def __init__(self, name: str):
        self.name = name

def is_cat_wrong(p: Cat | Dog) -> TypeGuard[Cat]:
    return hasattr(p, "name")  # Always True, never narrows

# Good: use unique attribute or isinstance
def is_cat_right(p: Cat | Dog) -> TypeGuard[Cat]:
    return isinstance(p, Cat)
```

### 4. TypeGuard without runtime validation

```python
# Bad: no actual validation
def is_str_list(data: list[object]) -> TypeGuard[list[str]]:
    return True  # Claims it's list[str] but doesn't check

# Good: explicit validation
def is_str_list_valid(data: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in data)
```

### 5. Assertion-like guard without raising on failure

```python
# Bad: should use TypeIs/TypeGuard properly
def guard_user(data: dict[str, Any]) -> TypeGuard[dict[str, str | int]]:
    if "name" not in data:
        pass  # Nothing happens, but guard returns False
        # This is actually OK for TypeGuard
    return isinstance(data.get("name"), str) and isinstance(data.get("age"), int)

# The real antipattern: trusting without actual checking
def dangerous(data: dict[str, Any]) -> TypeGuard[dict[str, str]]:
    return True  # Checker trusts you, runtime doesn't
```

## Antipatterns Fixed by Type Narrowing

### 1. Type casting with `cast()` instead of guards

```python
from typing import cast

# Bad: unsafe cast, no runtime check
def parse_user(json_str: str) -> str:
    import json
    raw = json.loads(json_str)
    u = cast(dict[str, str], raw)  # No runtime validation
    return u["id"]

# Good: guard with validation
def parse_user_fixed(json_str: str) -> str:
    import json
    from typing import Any, TypeGuard

    def is_user(d: Any) -> TypeGuard[dict[str, str]]:
        return (
            isinstance(d, dict)
            and "id" in d
            and isinstance(d["id"], str)
        )

    raw = json.loads(json_str)
    if is_user(raw):
        return raw["id"]
    raise ValueError("invalid user")
```

### 2. Using `Any` for external data

```python
from typing import Any

# Bad: loses all type safety
def render(api: Any) -> str:
    return f"{api['status']}: {api['data']}"  # No check

# Good: typed union + narrowing
from typing import TypeIs

type ApiResult = {"status": str, "data": str}

def render_fixed(api: ApiResult) -> str:
    return f"{api['status']}: {api['data']}"
```

### 3. Runtime `isinstance` without narrowing

```python
# Bad: manual check without using the narrowing benefit
def describe(x: str | int) -> None:
    if isinstance(x, str):
        tmp = x  # Now has type str | int
        print(tmp.upper())  # Error!

# Good: trust the narrowing
def describe_fixed(x: str | int) -> None:
    if isinstance(x, str):
        print(x.upper())  # x is str
```

### 4. Partial `match` without exhaustiveness

```python
# Bad: silently ignores new variants
type Message = {"type": "a"} | {"type": "b"} | {"type": "c"}

def handle(msg: Message) -> None:
    match msg:
        case {"type": "a"}:
            pass
        # Missing "b" and "c"
        # Python won't complain at runtime if "type" is always "a"
        case _:
            pass  # Silent fallback

# Good: exhaustive with assert_never
from typing import assert_never

def handle_fixed(msg: Message) -> None:
    match msg:
        case {"type": "a"}:
            pass
        case {"type": "b"}:
            pass
        case {"type": "c"}:
            pass
        case _:
            assert_never(msg)  # Caught at type-check time
```

### 5. Manual type checking without guards

```python
# Bad: manual checks everywhere, no reuse
def process1(data: list[object]) -> None:
    if all(isinstance(x, str) for x in data):
        for x in data:
            print(x.upper())  # Still list[object] in loop

def process2(data: list[object]) -> None:
    if all(isinstance(x, str) for x in data):
        for x in data:
            print(x.upper())  # Same duplication

# Good: reusable TypeGuard
def is_str_list(val: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in val)

def process_clean(data: list[object]) -> None:
    if is_str_list(data):
        for x in data:
            print(x.upper())  # data is list[str]
```
