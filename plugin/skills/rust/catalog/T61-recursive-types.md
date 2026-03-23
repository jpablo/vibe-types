# Recursive Types

> **Since:** Rust 1.0 (enum + Box for recursive types)

## What it is

A recursive type is a type whose definition refers to itself. In Rust, recursive types are defined using **enums with heap-allocated indirection**. Because Rust needs to know the size of every type at compile time, a directly recursive type like `enum List { Cons(i32, List), Nil }` is rejected -- it would have infinite size. The solution is to introduce a level of indirection via `Box<T>`, which is a fixed-size pointer to heap-allocated data.

`enum List<T> { Cons(T, Box<List<T>>), Nil }` defines a recursive linked list where each `Cons` variant contains a value and a boxed pointer to the rest of the list. The `Box` breaks the infinite-size cycle: the compiler knows `Box<List<T>>` is pointer-sized regardless of how deep the list goes.

This pattern is fundamental to trees, expression ASTs, linked lists, and any recursive data structure in Rust.

## What constraint it enforces

**The compiler requires all types to have a known size at compile time. Recursive types must use indirection (`Box`, `Rc`, `Arc`) to break the infinite-size cycle. The type system then ensures correct construction, pattern matching, and ownership through the recursive structure.**

- Direct recursion without indirection is rejected with `error[E0072]: recursive type has infinite size`.
- `Box` provides unique ownership of the recursive child.
- `Rc`/`Arc` enable shared ownership for recursive structures like DAGs or graphs.
- Exhaustive pattern matching is enforced over all recursive variants.

## Minimal snippet

```rust
enum List<T> {
    Cons(T, Box<List<T>>),
    Nil,
}

use List::*;

fn length<T>(list: &List<T>) -> usize {
    match list {
        Nil => 0,
        Cons(_, rest) => 1 + length(rest),
    }
}

fn main() {
    let list = Cons(1, Box::new(Cons(2, Box::new(Cons(3, Box::new(Nil))))));
    println!("length: {}", length(&list));  // 3
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **ADTs** [-> catalog/T01](T01-algebraic-data-types.md) | Recursive types are recursive enums -- the standard ADT mechanism in Rust. Each variant can hold different data, and pattern matching destructures them. |
| **Smart pointers** [-> catalog/T24](T24-smart-pointers.md) | `Box` is the default choice for recursive indirection (unique ownership). `Rc` enables shared recursive structures (DAGs). `Arc` adds thread safety. |
| **Ownership and moves** [-> catalog/T10](T10-ownership-moves.md) | Ownership flows through the recursive structure: dropping the root drops all children transitively. Moving a `Box<List<T>>` transfers the entire subtree. |
| **Pattern matching** [-> catalog/T14](T14-type-narrowing.md) | The compiler requires exhaustive matching over all recursive variants. Nested patterns can destructure multiple levels at once. |
| **Generics** [-> catalog/T04](T04-generics-bounds.md) | Recursive types are typically generic: `Tree<T>`, `List<T>`. Trait bounds on `T` propagate through the recursive structure. |

## Gotchas and limitations

1. **Indirection is mandatory.** Every recursive position must use `Box`, `Rc`, `Arc`, or another pointer type. Forgetting `Box` produces `error[E0072]: recursive type has infinite size`. The compiler suggests adding indirection.

2. **Stack overflow on deep structures.** Recursive functions over very deep structures (e.g., a list of 10 million elements) can overflow the stack. Use iterative algorithms or increase the stack size for deep recursion.

3. **No tail-call optimization.** Rust does not guarantee TCO. Tail-recursive functions over recursive types may still overflow the stack. Convert to iteration for guaranteed stack safety.

4. **Heap allocation cost.** Every `Box::new` allocates on the heap. For performance-critical code with many small nodes, consider arena allocation (`bumpalo`, `typed-arena`) to reduce allocator pressure.

5. **Pattern matching ergonomics.** Matching through `Box` requires dereferencing: `Cons(x, box rest)` (nightly feature) or `Cons(x, rest)` where `rest` is a `&Box<List<T>>`. The extra `*` and `&` can be noisy.

6. **Recursive type aliases are not allowed.** `type List<T> = Option<(T, Box<List<T>>)>` does not compile -- Rust does not support recursive type aliases. You must use an explicit `enum` or `struct`.

## Beginner mental model

Think of a recursive type as a **chain of boxes**. Each box contains a value and a smaller box inside it (the `Box<List<T>>`). The last box in the chain is empty (`Nil`). The outer box owns the inner box -- dropping the chain drops everything. The `Box` is needed because Rust must know how big each box is on the outside; "a box containing a box containing a box..." only works because each `Box` is pointer-sized, regardless of what is inside it.

## Example A -- Binary tree with traversal

```rust
enum Tree<T> {
    Leaf(T),
    Branch(Box<Tree<T>>, Box<Tree<T>>),
}

use Tree::*;

fn sum(tree: &Tree<i32>) -> i32 {
    match tree {
        Leaf(v) => *v,
        Branch(left, right) => sum(left) + sum(right),
    }
}

fn depth<T>(tree: &Tree<T>) -> usize {
    match tree {
        Leaf(_) => 0,
        Branch(l, r) => 1 + depth(l).max(depth(r)),
    }
}

fn main() {
    let tree = Branch(
        Box::new(Leaf(1)),
        Box::new(Branch(
            Box::new(Leaf(2)),
            Box::new(Leaf(3)),
        )),
    );
    println!("sum: {}, depth: {}", sum(&tree), depth(&tree));  // sum: 6, depth: 2
}
```

## Example B -- Expression AST with evaluation

```rust
enum Expr {
    Num(f64),
    Add(Box<Expr>, Box<Expr>),
    Neg(Box<Expr>),
}

fn eval(expr: &Expr) -> f64 {
    match expr {
        Expr::Num(v)    => *v,
        Expr::Add(l, r) => eval(l) + eval(r),
        Expr::Neg(e)     => -eval(e),
    }
}

fn main() {
    let expr = Expr::Add(
        Box::new(Expr::Num(1.0)),
        Box::new(Expr::Neg(Box::new(Expr::Num(3.0)))),
    );
    println!("{}", eval(&expr));  // -2.0
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Exhaustive matching over recursive enums ensures all structural variants are handled, catching missing cases at compile time.
- [-> UC-13](../usecases/UC13-state-machines.md) -- Recursive types can model nested or hierarchical state machines where states contain sub-state-machines.
- [-> UC-20](../usecases/UC20-ownership-apis.md) -- Ownership of recursive structures transfers the entire tree, ensuring clean resource cleanup through the recursive Drop chain.

## Source anchors

- `book/src/ch15-01-box.md` -- "Using Box<T> to Point to Data on the Heap"
- `book/src/ch15-01-box.md` -- "Enabling Recursive Types with Boxes"
- `rust-reference/src/types/enum.md`
- `rust-reference/src/items/type-aliases.md` -- recursive alias restriction
