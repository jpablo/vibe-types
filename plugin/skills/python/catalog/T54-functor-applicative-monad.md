# Functor, Applicative, and Monad (via Generator Expressions and Optional Chaining)

> **Since:** Generator expressions Python 2.4 (PEP 289); list comprehensions Python 2.0 (PEP 202); `returns` library 0.14+; `Optional` chaining patterns since Python 3.10+

## What it is

Python has no native Functor, Applicative, or Monad type classes, but several built-in features implement the same patterns. **List comprehensions** are the list monad: `[f(x) for x in xs]` is `map` (Functor), and `[f(x) for x in xs for y in ys]` is monadic bind (`flatMap`) over lists. **Generator expressions** provide lazy monadic sequencing. `map()` and `filter()` are built-in Functor operations over iterables.

For `Option`-like monadic chaining, Python 3.10 added **structural pattern matching**, and common patterns use short-circuit `and`/`or` or the walrus operator (`:=`). The **`returns`** library by dry-python provides explicit `Maybe`, `Result`, `IO`, and `Future` monads with `map`, `bind`, and `lash` (error recovery) methods, as well as a `@pipeline` decorator for chaining.

## What constraint it enforces

**List comprehensions enforce that transformations produce lists (the comprehension context is fixed). The `returns` library's container types enforce that monadic operations stay within their context (`Maybe` remains `Maybe`, `Result` remains `Result`), and the type checker rejects mixing containers of different types.**

## Minimal snippet

```python
# List monad via comprehension
pairs = [(x, y) for x in [1, 2] for y in ["a", "b"]]
# [(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')]  -- cartesian = monadic bind

# Optional chaining pattern
from typing import Optional

def parse_int(s: str) -> Optional[int]:
    try:
        return int(s)
    except ValueError:
        return None

def double_parsed(s: str) -> Optional[int]:
    if (n := parse_int(s)) is not None:
        return n * 2
    return None
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Generator expressions** | `(f(x) for x in xs)` is a lazy Functor map. Nested generators `(... for x in xs for y in ys)` are monadic bind. |
| **List/set/dict comprehensions** | Comprehensions are the strict list/set/dict monad. Conditions (`if`) act as `guard` (MonadPlus). |
| **Itertools** | `itertools.chain`, `itertools.starmap`, `itertools.product` are Functor and Applicative operations over iterables. |
| **Optional / None patterns** [-> T13](T13-null-safety.md) | Walrus operator (`:=`) combined with `is not None` checks provides manual monadic bind for `Optional`. |
| **Type narrowing** [-> T14](T14-type-narrowing.md) | `if x is not None` narrows `Optional[T]` to `T`, enabling safe "unwrapping" after a monadic check. |
| **Structural pattern matching** | `match` statements (Python 3.10+) can destructure `Some`/`None`-like patterns for monadic dispatch. |

## Gotchas and limitations

1. **No unified abstraction.** There is no `Monad` protocol in Python's type system. You cannot write a function generic over "any monad." Each monadic type (list, Optional, `returns.Maybe`) has its own API.

2. **List comprehensions are strict.** Unlike Haskell's list monad, Python list comprehensions eagerly evaluate the entire result. For lazy evaluation, use generator expressions, but generators are single-use.

3. **No do-notation.** Python has no syntactic sugar for monadic chaining beyond comprehensions (which only work for iterables). The `returns` library's `@pipeline` and `flow` helpers provide partial alternatives.

4. **Optional chaining is verbose.** Without a `?` operator or do-notation, chaining `Optional` values requires repeated `if x is not None` checks or walrus operator patterns that quickly become unwieldy.

5. **`returns` library typing limitations.** While `returns` provides proper monadic types, Python's type system cannot fully express higher-kinded types, so generic monadic code requires `@overload` or plugin support (e.g., `returns` mypy plugin).

6. **Comprehension scope.** Variables assigned in comprehensions leak into the enclosing scope in Python 2 but not in Python 3. Generator expression variables never leak. This is a common source of confusion but not a monadic concern per se.

## Beginner mental model

Think of list comprehensions as monadic assembly lines: `[step(x) for x in inputs]` runs `step` on every input (Functor/map), and `[combine(x, y) for x in xs for y in ys]` runs the inner loop for every outer value (monadic bind / cartesian product). For `Optional` values, the pattern is manual: check for `None`, proceed if present, bail out otherwise. Python makes you write the plumbing explicitly, whereas languages with do-notation (Scala, Lean, Haskell) provide syntactic sugar.

## Example A -- List monad: Pythagorean triples

```python
triples = [
    (a, b, c)
    for c in range(1, 20)
    for b in range(1, c)
    for a in range(1, b)
    if a * a + b * b == c * c
]
# [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (9, 12, 15)]
```

## Example B -- Optional chaining with returns library

```python
from returns.maybe import Maybe, Some, Nothing

def parse(s: str) -> Maybe[int]:
    try:
        return Some(int(s))
    except ValueError:
        return Nothing

def halve(n: int) -> Maybe[int]:
    return Some(n // 2) if n % 2 == 0 else Nothing

result = parse("42").bind(halve)   # Some(21)
failed = parse("abc").bind(halve)  # Nothing -- short-circuits
odd    = parse("7").bind(halve)    # Nothing -- halve fails
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Optional chaining and `Maybe`/`Result` monads prevent operating on absent or invalid values.
- [-> UC-08](../usecases/UC08-error-handling.md) -- `returns.Result` provides monadic error handling with `map`, `bind`, and `lash` for recovery.

## Source anchors

- [PEP 289 -- Generator Expressions](https://peps.python.org/pep-0289/)
- [PEP 202 -- List Comprehensions](https://peps.python.org/pep-0202/)
- [returns library documentation](https://returns.readthedocs.io/)
- [Python docs -- List comprehensions](https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions)
- [Python docs -- itertools](https://docs.python.org/3/library/itertools.html)
