# Recursive Types (via Forward References and Recursive Aliases)

> **Since:** `from __future__ import annotations` Python 3.7 (PEP 563); `type` statement Python 3.12 (PEP 695); recursive `TypeAlias` Python 3.10 (PEP 613)

## What it is

A recursive type is a type whose definition refers to itself. Python does not natively have algebraic data types, but recursive type definitions are possible through **forward references** (string annotations or `from __future__ import annotations`), **recursive type aliases** (using `TypeAlias` or the `type` statement), and **dataclass hierarchies** that reference the enclosing type.

Since Python 3.12, the `type` statement enables clean recursive type aliases: `type Tree[A] = Leaf[A] | Branch[A]` with `@dataclass class Branch[A]: left: Tree[A]; right: Tree[A]`. Prior to 3.12, recursive types require `from __future__ import annotations` to defer annotation evaluation, avoiding `NameError` from forward references.

Type checkers (mypy, pyright) understand recursive types and can verify exhaustive pattern matching through union discrimination, though enforcement varies by checker version.

## What constraint it enforces

**The type checker ensures that values assigned to recursive type positions match the declared recursive structure. Pattern matching (via `isinstance` or `match`) must handle all variants of the recursive union to satisfy exhaustiveness checks.**

- Forward references allow types to name themselves before being fully defined.
- Type checkers verify that recursive construction is type-consistent.
- `match` statements with type guards enable structural decomposition of recursive values.

## Minimal snippet

```python
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Leaf[A]:
    value: A

@dataclass
class Branch[A]:
    left: Tree[A]
    right: Tree[A]

type Tree[A] = Leaf[A] | Branch[A]

def depth(tree: Tree[int]) -> int:
    match tree:
        case Leaf(_):
            return 0
        case Branch(left, right):
            return 1 + max(depth(left), depth(right))

tree = Branch(Leaf(1), Branch(Leaf(2), Leaf(3)))
print(depth(tree))   # 2
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **ADTs / Union types** [-> catalog/T02](T02-union-intersection.md) | Recursive types in Python are union types where variants reference the union. `Tree = Leaf | Branch` with `Branch` containing `Tree` fields. |
| **Type narrowing** [-> catalog/T14](T14-type-narrowing.md) | `match` and `isinstance` narrow recursive unions to specific variants, enabling safe recursive decomposition. |
| **Dataclasses** [-> catalog/T31](T31-record-types.md) | `@dataclass` provides the product type for each variant. Recursive fields are typed with the parent union alias. |
| **Generics** [-> catalog/T04](T04-generics-bounds.md) | Generic recursive types (`Tree[A]`) parameterize the recursion, ensuring type consistency through the recursive structure. |
| **Type aliases** [-> catalog/T23](T23-type-aliases.md) | The `type` statement (3.12+) or `TypeAlias` annotation enables recursive type alias definitions. Without these, recursive aliases may confuse type checkers. |

## Gotchas and limitations

1. **Forward reference required before 3.12.** Without `from __future__ import annotations` or string annotations, defining `class Branch: left: Tree` before `Tree` is defined causes a `NameError` at runtime. The `type` statement (3.12+) solves this for aliases.

2. **Type checker support varies.** mypy and pyright handle recursive types differently in edge cases. Deeply nested recursive types or recursive types with complex generics may produce false positives in some checker versions.

3. **No exhaustiveness guarantee at runtime.** `match` statements can check types, but Python does not enforce at runtime that a `Tree` is only `Leaf | Branch`. Any object can be passed where `Tree` is expected -- the type checker catches mismatches statically, not at runtime.

4. **Performance of deeply recursive structures.** Python has a default recursion limit of 1000. Deeply nested recursive data structures require `sys.setrecursionlimit()` or iterative traversal to avoid `RecursionError`.

5. **Recursive TypeAlias before 3.12.** Before the `type` statement, recursive type aliases using `TypeAlias` require careful ordering and explicit annotation: `Tree: TypeAlias = "Leaf[A] | Branch[A]"` with string quoting. This is fragile and error-prone.

6. **No structural pattern matching on generics.** `match` can match on class identity (`case Leaf(value=v)`) but cannot match on type parameters. `Leaf[int]` and `Leaf[str]` are indistinguishable at runtime due to type erasure.

## Beginner mental model

Think of a recursive type as a **family tree** definition. A person is either a "leaf" (no children recorded) or a "branch" (a person with left and right children, who are themselves persons). The definition is circular -- a `Tree` contains `Tree`s -- but every actual tree is finite. In Python, you define each case as a dataclass and tie them together with a `type` alias that unions the cases.

## Example A -- Recursive JSON value type

```python
from __future__ import annotations

type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]

def summarize(val: JsonValue) -> str:
    match val:
        case None:              return "null"
        case bool() as b:      return str(b).lower()
        case int() | float():  return str(val)
        case str() as s:       return f'"{s}"'
        case list() as arr:    return f"[{', '.join(summarize(v) for v in arr)}]"
        case dict() as obj:    return f"{{{', '.join(f'{k}: {summarize(v)}' for k, v in obj.items())}}}"

data: JsonValue = {"name": "Alice", "scores": [95, 87, None]}
print(summarize(data))   # {name: "Alice", scores: [95, 87, null]}
```

## Example B -- Expression tree with evaluation

```python
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Num:
    value: float

@dataclass
class Add:
    left: Expr
    right: Expr

@dataclass
class Mul:
    left: Expr
    right: Expr

@dataclass
class Neg:
    inner: Expr

type Expr = Num | Add | Mul | Neg

def evaluate(expr: Expr) -> float:
    match expr:
        case Num(v):
            return v
        case Add(l, r):
            return evaluate(l) + evaluate(r)
        case Mul(l, r):
            return evaluate(l) * evaluate(r)
        case Neg(e):
            return -evaluate(e)

expr = Add(Num(1), Mul(Num(2), Neg(Num(3))))
print(evaluate(expr))   # -5.0
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Recursive unions with exhaustive matching ensure all structural variants are handled, catching missing cases statically.
- [-> UC-02](../usecases/UC02-domain-modeling.md) -- Domain models with recursive structure (trees, nested configs, ASTs) are naturally expressed as recursive type unions.

## When to Use It

**Use recursive types when your domain has inherently self-referential structure:**

- Tree structures (DOM, file systems, org charts, syntax trees)
- Nested configs where values can be primitives or further nested configs
- ASTs, expression evaluators, or any data that references itself
- Schemas where an object's properties can be the same type as the object

```python
# File system nodes
type Node = TextNode | ElemNode

@dataclass
class TextNode:
    text: str

@dataclass
class ElemNode:
    tag: str
    children: list[Node]
```

## When Not to Use It

**Avoid recursive types when:**

- Your data has a known, fixed depth (use nested dataclasses instead)
- You're modeling flat or shallow structures (simple dataclasses suffice)
- The recursion is artificial or adds unnecessary complexity
- You need to handle very deep structures (Python's recursion limit of ~1000)

```python
# Anti: recursive type for fixed depth
@dataclass
class Address:
    street: str
    city: str
    parent: Address | None  # Only 1-2 levels ever used? Don't recurse

# GOOD: explicit nesting for fixed depth
@dataclass
class Address:
    street: str
    city: str
    state: str | None  # Max depth known upfront
```

## Antipatterns When Using Recursive Types

### Antipattern A: Unbounded recursion without depth consideration

```python
# Anti: recursive function on user-controlled depth
def count_nodes(node: Node) -> int:
    if isinstance(node, TextNode):
        return 1
    return sum(count_nodes(child) for child in node.children)  # RecursionError on deep trees

# Better: iterative with explicit stack
def count_nodes(node: Node) -> int:
    stack = [node]
    count = 0
    while stack:
        n = stack.pop()
        if isinstance(n, TextNode):
            count += 1
        else:
            stack.extend(n.children)
    return count
```

### Antipattern B: Using `Any` to terminate recursion

```python
from typing import Any

# Anti: defeats type safety
@dataclass
class BadNode:
    value: Any  # Lose type safety entirely
    children: list[BadNode] | None

# Better: explicit union with primitive termination
@dataclass
class GoodNode:
    value: int | str
    children: list[GoodNode] | None
```

### Antipattern C: Mixed recursive and non-recursive APIs

```python
# Anti: Inconsistent leaf representation
@dataclass
class ValueNode:
    data: Any  # Non-recursive leaf

@dataclass  
class BranchNode:
    children: list[Node]  # Recursive

type Node = ValueNode | BranchNode  # Can't enforce uniform leaf types

# Better: consistent structure
@dataclass
class Leaf:
    value: str  # Always a string

@dataclass
class Branch:
    children: list[Tree]

type Tree = Leaf | Branch  # Clear, uniform
```

## Antipatterns Where Recursive Types Are Better

### Antipattern A: Manual enumeration of fixed depths

```python
# Anti: copy-paste types for each level
@dataclass
class Folder1:
    id: str
    children: list[Folder2] | None

@dataclass
class Folder2:
    id: str
    children: list[Folder3] | None

@dataclass
class Folder3:
    id: str
    children: None  # Hard limited to 3 levels

# Better: single recursive type
@dataclass
class Folder:
    id: str
    children: list[Folder] | None  # Works at any depth
```

### Antipattern B: Using `list[Any]` for children

```python
from typing import Any

# Anti: lose type safety
@dataclass
class Component:
    name: str
    children: list[Any]  # What's in here?

# Better: recursive type preserves structure
@dataclass
class Component:
    name: str
    children: list[Component]  # Type-safe nesting
```

### Antipattern C: Runtime validation instead of types

```python
# Anti: validate at runtime
@dataclass
class LooseTree:
    value: int
    left: "LooseTree | None" = None
    right: "LooseTree | None" = None

def validate(node: any) -> bool:  # Runtime checks needed
    if not isinstance(node, LooseTree):
        return False
    return validate(node.left) and validate(node.right)

# Better: rely on types, no runtime validation
@dataclass
class StrictTree:
    value: int
    left: "StrictTree | None" = None
    right: "StrictTree | None" = None

# Type checker catches errors at static analysis time
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Recursive unions with exhaustive matching ensure all structural variants are handled, catching missing cases statically.
- [-> UC-02](../usecases/UC02-domain-modeling.md) -- Domain models with recursive structure (trees, nested configs, ASTs) are naturally expressed as recursive type unions.

## Source anchors

- [PEP 563 -- Postponed Evaluation of Annotations](https://peps.python.org/pep-0563/)
- [PEP 695 -- Type Parameter Syntax (type statement)](https://peps.python.org/pep-0695/)
- [PEP 613 -- TypeAlias](https://peps.python.org/pep-0613/)
- [mypy -- Recursive types](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#recursive-types)
- [pyright -- Recursive type aliases](https://microsoft.github.io/pyright/#/configuration?id=recursive-type-aliases)
