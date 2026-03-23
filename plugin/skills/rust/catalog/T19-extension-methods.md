# Extension Methods (via Trait Implementations)

Since: Rust 1.0

## What it is

Rust does not have extension methods as a dedicated language feature (like Kotlin's `fun String.isEmail()` or Scala's `extension` keyword). Instead, it achieves the same constraint through **trait implementations on existing types**. By defining a trait with the desired methods and then implementing it for a foreign type, you effectively "add" methods to types you do not own.

The **extension trait pattern** is idiomatic Rust: define a trait (often named `FooExt`), implement it for the target type, and bring the trait into scope with `use`. Callers can then invoke the new methods with regular dot syntax. The standard library uses this pattern extensively -- `Iterator` and its many adaptor methods are the most prominent example.

The **orphan rule** limits this: you can only implement a foreign trait for a local type, or a local trait for a foreign type. You cannot implement a foreign trait for a foreign type without a newtype wrapper [-> catalog/T03](T03-newtypes-opaque.md).

## What constraint it enforces

**New methods on existing types must be declared through explicit trait implementations and are only available when the trait is in scope.**

- Extension methods do not modify the original type. They are purely additive.
- The trait must be imported (`use`) before the methods become callable. This prevents name collision surprises.
- The orphan rule ensures global coherence: no two crates can provide conflicting implementations.

## Minimal snippet

```rust
trait StrExt {
    fn is_blank(&self) -> bool;
}

impl StrExt for str {
    fn is_blank(&self) -> bool {
        self.trim().is_empty()
    }
}

fn main() {
    println!("{}", "  ".is_blank());    // true
    println!("{}", "hi".is_blank());    // false
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Traits** [-> catalog/T05](T05-type-classes.md) | Extension methods *are* trait methods. The entire mechanism is built on Rust's trait system. |
| **Coherence / orphan rules** [-> catalog/T25](T25-coherence-orphan.md) | The orphan rule limits which types you can extend. You cannot impl a foreign trait for a foreign type. |
| **Newtypes** [-> catalog/T03](T03-newtypes-opaque.md) | When the orphan rule blocks a direct extension, wrap the type in a newtype and implement the trait on the wrapper. |
| **Encapsulation** [-> catalog/T21](T21-encapsulation.md) | Extension traits cannot access private fields of the types they extend. They can only use the type's public API. |
| **Callable typing** [-> catalog/T22](T22-callable-typing.md) | Extension traits can add higher-order methods to existing types: `fn then<F: Fn(Self) -> R>(&self, f: F) -> R`. |

## Gotchas and limitations

1. **Trait must be in scope.** If you define `trait VecExt` and implement it for `Vec<T>`, callers must `use your_crate::VecExt;` before calling the new methods. Forgetting the import produces "no method named `foo` found."

2. **Name collisions are possible.** If two traits in scope define the same method name for the same type, the call is ambiguous. Use fully qualified syntax (`<Vec<i32> as VecExt>::method(...)`) to disambiguate.

3. **Cannot add inherent methods to foreign types.** `impl String { fn foo(&self) {} }` is not allowed -- you can only add methods through trait impls.

4. **Orphan rule prevents some extensions.** You cannot `impl Display for Vec<MyType>` because both `Display` and `Vec` are foreign. Wrap in a newtype first.

5. **Extension traits pollute the method namespace.** Blanket impls like `impl<T: Display> MyExt for T` add methods to *every* `Display` type. Use narrow bounds to avoid surprising callers.

6. **No access to private internals.** Extension methods work through the public API only. If you need internal access, the method belongs in the original crate.

## Beginner mental model

Think of extension traits as **stickers** you can put on someone else's toolbox. The tools inside (private fields) do not change, but the sticker adds a new label (method) that anyone with the sticker set (`use MyExt;`) can read. If you forget to hand out the sticker set, the label is invisible. And the toolbox owner (original crate) can always add stickers of their own that might conflict with yours.

## Example A -- Extension trait for iterators

```rust
trait IterExt: Iterator {
    fn sum_positive(self) -> i64
    where
        Self: Iterator<Item = i64>,
        Self: Sized,
    {
        self.filter(|&x| x > 0).sum()
    }
}

impl<I: Iterator> IterExt for I {}

fn main() {
    let data = vec![10, -3, 5, -1, 8];
    let total = data.into_iter().sum_positive();
    println!("{total}");  // 23
}
```

## Example B -- Extension trait with blanket impl for Display types

```rust
use std::fmt;

trait Logging: fmt::Display {
    fn log(&self) {
        println!("[LOG] {self}");
    }

    fn log_prefixed(&self, prefix: &str) {
        println!("[{prefix}] {self}");
    }
}

impl<T: fmt::Display> Logging for T {}

fn main() {
    "server started".log();              // [LOG] server started
    42.log_prefixed("COUNT");            // [COUNT] 42
    3.14_f64.log_prefixed("METRIC");     // [METRIC] 3.14
}
```

Any type implementing `Display` automatically gains `.log()` and `.log_prefixed()` methods when the `Logging` trait is in scope.

## Use-case cross-references

- [-> UC-14](../usecases/UC14-extensibility.md) -- Extension traits let downstream crates add behavior to upstream types without modifying them.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Blanket extension traits constrained by bounds apply to entire families of types.
- [-> UC-22](../usecases/UC22-conversions.md) -- Extension methods can provide convenient conversion helpers (`.to_foo()`) without modifying the original type.

## Source anchors

- `book/src/ch10-02-traits.md`
- `rust-reference/src/items/implementations.md`
- `api-guidelines/src/naming.md` -- C-EXT naming convention
- `rust-by-example/src/trait.md`
