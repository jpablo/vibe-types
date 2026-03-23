# Generics and Where Clauses

## What it is

Generic type parameters let you write functions, structs, enums, and trait implementations that work with *many* types instead of one concrete type. A parameter like `<T>` is a placeholder: every call site fills it with a specific type, and the compiler verifies that the chosen type satisfies all required constraints. Generic code is checked at definition time against its declared bounds — a stark contrast with C++ templates, which are unchecked until instantiation.

When the compiler generates machine code it performs *monomorphization*: for each concrete type a generic is instantiated with, Rust emits a fully specialized copy. `fn foo<T>(x: T)` called with `i32` and `String` produces two independent functions, each as efficient as hand-written code. This is Rust's zero-cost abstraction promise — no runtime indirection, no vtable, no boxing. The trade-off is that many instantiations increase binary size.

Trait bounds (`T: Display`, `T: Clone + Debug`) state what a type parameter *must* be capable of. Without a bound, `T` is fully opaque. Bounds are the key difference from C++ templates (duck typing — any operation compiles if the substituted type supports it) and from Java/C# generics (explicit bounds but type-erased at runtime, losing monomorphization). Multiple bounds are joined with `+`, lifetime bounds (`T: 'a`) constrain reference validity, and higher-ranked trait bounds (`for<'a> F: Fn(&'a str)`) express constraints that must hold for *all* lifetimes.

`where` clauses provide a more readable way to express the same bounds, especially when constraints are numerous or involve complex type expressions like `Option<T>: Debug`. The `where` syntax also enables constraints impossible to express inline. It changes nothing semantically — it is purely a readability tool.

Finally, `impl Trait` in argument position (`fn foo(x: impl Display)`) is syntactic sugar for a generic parameter with a bound. In return position, `impl Trait` means something different — an opaque type chosen by the function body, not the caller.

## What constraint it enforces

**Generic code compiles only when every operation in the body is justified by declared bounds, and callers compile only when the concrete type satisfies those bounds.**

- **Bounds are contracts.** `T: Display` guarantees every substituted type implements `Display`. Callers that pass a non-`Display` type are rejected at compile time.
- **Nothing is implicit.** You cannot call a method on `T` unless a bound explicitly permits it. Errors surface at the generic's definition, not at each instantiation.
- **Monomorphization produces specialized code.** A dedicated copy per concrete type means zero runtime overhead.
- **Bounds propagate.** If `Wrapper<T: Clone>` appears in another generic function, that function must also require `T: Clone` or avoid `Clone`-dependent operations.

## Minimal snippet

```rust
use std::fmt::Display;

fn log_value<T>(label: &str, value: T)
where
    T: Display,
{
    println!("[{label}] {value}");
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Trait definitions** [-> T05](T05-type-classes.md) | Traits provide the bounds generics reference. `T: Iterator` only permits methods from the `Iterator` trait. |
| **Associated types** [-> T49](T49-associated-types.md) | Reduce type parameters. `I: Iterator<Item = u32>` constrains both the iterator and its output without a second parameter. |
| **Lifetimes** [-> T48](T48-lifetimes.md) | `T: 'a` means `T` contains no references shorter than `'a` — essential for storing borrowed data in generic structs. |
| **Trait objects** [-> T36](T36-trait-objects.md) | `dyn Trait` is the dynamic-dispatch counterpart. Generics monomorphize; trait objects use vtables. Conversion requires object safety. |
| **Smart pointers** [-> T24](T24-smart-pointers.md) | `Box<T>`, `Rc<T>`, `Arc<T>` are generic types. Bounds on `T` compose with pointer semantics (e.g., `Arc<T>` needs `T: Send + Sync`). |
| **Send and Sync** [-> T50](T50-send-sync.md) | Generic types auto-implement `Send`/`Sync` if all type parameters do. Explicit `T: Send` is needed when spawning threads. |

## Gotchas and limitations

1. **Over-constraining reduces flexibility.** Bounds you never use (`T: Clone + Debug + Display` when the body only calls `clone()`) force callers to satisfy unnecessary traits. Keep bounds minimal.

2. **Under-constraining gives confusing errors.** A missing bound surfaces as "method not found" inside the body. Read the error, find the missing trait, add it.
   ```rust
   fn print_it<T>(x: T) {
       println!("{x}");  // error: `T` doesn't implement `Display`
   }
   // Fix: fn print_it<T: std::fmt::Display>(x: T)
   ```

3. **`Debug` is not `Display`.** `T: Debug` gives `{:?}` but not `{}`. Mixing them up is a common `E0277` source.

4. **Generic functions and object safety.** You cannot pass `dyn Trait` for `T` unless `T: ?Sized`, and the trait must be object-safe (no `Self: Sized` methods, no generic methods).

5. **Turbofish (`::<Type>`) for disambiguation.** When inference fails, use `"42".parse::<i32>()`. Forgetting it yields `E0282`. Turbofish attaches to the function name, not the arguments.

6. **`Sized` is implicit — opt out with `?Sized`.** Every `T` is implicitly `Sized`. To accept `str`, `[u8]`, or `dyn Trait`, add `?Sized` and take `T` by reference.
   ```rust
   fn accepts_unsized<T: ?Sized + std::fmt::Display>(x: &T) {
       println!("{x}");
   }
   ```

7. **Monomorphization can cause binary bloat.** A function called with 20 types produces 20 copies. Type-erased inner functions or `dyn Trait` can mitigate this.

8. **`impl Trait` in return position is not a generic.** `fn foo() -> impl Display` always returns the same hidden type; the caller cannot choose it.

## Beginner mental model

Think of `<T>` as a **blank on a form** the caller fills in. Trait bounds are the **fine print**: "must implement Display", "must be Cloneable." The compiler is a strict clerk — it rejects the form if the value does not meet the requirements, and the function body can only do things the fine print guarantees.

The `where` clause moves the fine print to a separate, readable section — it changes nothing about what is allowed. Read it as a bulleted list of contracts: "T can be displayed, U can be compared, lifetime 'a outlives 'b." Satisfy every contract and your type fits.

## Example A — Simple generic function with a single bound

```rust
use std::fmt::Display;

fn announce<T: Display>(value: T) {
    println!("The value is: {value}");
}

fn main() {
    announce(42);            // T = i32
    announce("hello");       // T = &str
    // announce(vec![1, 2]); // error: Vec<i32> doesn't implement Display
}
```

## Example B — Multiple bounds and `where` clause

```rust
use std::fmt::{Debug, Display};

fn debug_and_display<T>(value: T)
where
    T: Debug + Display,
{
    println!("Display: {value}");
    println!("Debug:   {value:?}");
}

fn main() {
    debug_and_display(42);          // i32 implements both
    // debug_and_display(vec![1]);  // Vec: Debug yes, Display no
}
```

## Example C — Generic struct with bounds

```rust
use std::fmt::Display;

struct Labeled<T: Display> {
    label: String,
    value: T,
}

impl<T: Display> Labeled<T> {
    fn print(&self) {
        println!("{}: {}", self.label, self.value);
    }
}

fn main() {
    let item = Labeled { label: "score".into(), value: 100 };
    item.print();  // "score: 100"
}
```

Placing bounds on the struct forces *every* use to satisfy them. A common alternative is to bound only the `impl` block.

## Example D — `impl Trait` as argument sugar vs explicit generic

```rust
use std::fmt::Display;

fn show_sugar(value: impl Display) { println!("{value}"); }
fn show_explicit<T: Display>(value: T) { println!("{value}"); }

fn main() {
    show_sugar(42);
    show_explicit(42);
    // Key difference:
    // fn compare<T: Display + PartialOrd>(a: T, b: T) — both args same type
    // fn compare(a: impl Display, b: impl Display)    — could be different types!
}
```

With `impl Trait`, each parameter gets its own anonymous type parameter. Use the explicit form when two arguments must share a type.

## Example E — Turbofish syntax for disambiguation

```rust
fn main() {
    // let n = "42".parse();  // error[E0282]: type annotations needed
    let n = "42".parse::<i32>().unwrap();   // turbofish on method
    let m: f64 = "3.14".parse().unwrap();   // or annotate the binding

    fn identity<T>(x: T) -> T { x }
    let s = identity::<&str>("turbofish");  // turbofish on free function
    println!("{n}, {m}, {s}");
}
```

## Example F — `?Sized` bound for references to unsized types

```rust
use std::fmt::Display;

fn print_ref<T: ?Sized + Display>(value: &T) {
    println!("{value}");
}

fn main() {
    print_ref("dynamically sized");     // T = str  (unsized)
    print_ref(&42);                     // T = i32  (sized)
    let d: &dyn Display = &3.14;
    print_ref(d);                       // T = dyn Display (unsized)
}
```

Without `?Sized`, passing `&str` would fail because `str` does not implement `Sized`.

## Common compiler errors and how to read them

### `error[E0277]: the trait bound 'Type: Trait' is not satisfied`

```
error[E0277]: `Vec<i32>` doesn't implement `std::fmt::Display`
 --> src/main.rs:8:14
  |
8 |     announce(vec![1, 2, 3]);
  |              ^^^^^^^^^^^^^ `Vec<i32>` cannot be formatted with the default formatter
  |
  = help: the trait `Display` is not implemented for `Vec<i32>`
```

**How to fix:** Pass a type that implements the trait, add a manual `impl` if you own the type, or relax the bound (e.g., `Debug` instead of `Display`).

### `error[E0599]: no method named 'clone' found for type parameter 'T'`

```
error[E0599]: no method named `clone` found for type parameter `T`
 --> src/main.rs:2:17
  |
1 | fn dup<T>(x: T) -> (T, T) {
  |        - method `clone` not found for this type parameter
2 |     (x.clone(), x)
  |         ^^^^^ method not found in `T`
  |
help: the following trait defines an item `clone`:
  |
1 | fn dup<T: Clone>(x: T) -> (T, T) {
```

**How to fix:** Add the missing trait bound (`T: Clone`) to the signature.

### `error[E0282]: type annotations needed`

```
error[E0282]: type annotations needed
 --> src/main.rs:2:9
  |
2 |     let x = "42".parse().unwrap();
  |         ^ consider giving `x` a type
```

**How to fix:** Annotate the binding (`let x: i32 = ...`) or use turbofish (`"42".parse::<i32>()`).

### `error[E0107]: missing generics for struct 'HashMap'`

```
error[E0107]: missing generics for struct `HashMap`
 --> src/main.rs:3:10
  |
3 |     let m: HashMap = HashMap::new();
  |            ^^^^^^^ expected 2 generic arguments
```

**How to fix:** Supply type arguments (`HashMap<String, i32>`) or let inference fill them from context.

## Use-case cross-references

- [-> UC-03](../usecases/UC04-generic-constraints.md) — Reusable data-processing pipelines where input and output types vary but share trait contracts.
- [-> UC-06](../usecases/UC22-conversions.md) — Generic functions using `Into`, `From`, and `AsRef` bounds to accept multiple input types while making conversions explicit.
- [-> UC-08](../usecases/UC18-type-arithmetic.md) — Generic type parameters and const generics encoding sizes, dimensions, or capacities so mismatches are caught at compile time.

## Source anchors

- `book/src/ch10-01-syntax.md`
- `book/src/ch10-02-traits.md` (trait bounds and `where` clauses)
- `rust-by-example/src/generics.md`
- `rust-by-example/src/generics/bounds.md`
- `rust-by-example/src/generics/where.md`
- `reference/src/items/generics.md`
