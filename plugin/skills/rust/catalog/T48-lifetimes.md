# Lifetimes

## What it is

Every reference in Rust has a *lifetime* — a region of code for which the reference is guaranteed to be valid. Most of the time the compiler infers lifetimes automatically. When it cannot, you add explicit annotations (`'a`) to tell the compiler how input and output references relate.

Lifetimes prevent **dangling references**. If a reference outlived its data, reading through it would be undefined behavior. Garbage-collected languages (Java, Go, Python) avoid this because the GC keeps objects alive while references exist. C and C++ leave it to the programmer, producing use-after-free bugs. Rust proves at compile time that every reference is used only while the data is alive.

A critical distinction: a lifetime annotation does **not** create, extend, or shorten the time a value lives. It is a *name* the compiler uses to relate borrow scopes. `fn foo<'a>(x: &'a str) -> &'a str` says "the returned reference lives at most as long as `x`" — a constraint, not a duration.

Rust has three *lifetime elision rules* that fill in annotations for common patterns, which is why `fn first(s: &str) -> &str` compiles without `'a`. When multiple inputs make the output ambiguous, explicit annotations are required.

## What constraint it enforces

**A reference cannot outlive the data it borrows, and when lifetimes are ambiguous the programmer must annotate how input and output references relate.**

- **No dangling references.** The compiler rejects any path where a reference could be used after the pointed-to value is dropped.
- **Output borrows must derive from inputs.** A function cannot return a reference to a local variable; the return must tie to an input reference (or `'static` data).
- **Structs holding references must declare lifetimes.** A `&T` field requires a lifetime parameter on the struct so the compiler enforces it does not outlive the borrowed data.
- **Lifetime bounds propagate through generics.** Types and trait objects containing references require bounds (`T: 'a`, `dyn Trait + 'a`).

## Minimal snippet

```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() >= y.len() { x } else { y }
}
```

Both inputs share `'a`; the compiler infers it as the *shorter* of the two actual lifetimes at each call site.

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Borrowing** [→ T11](T11-borrowing-mutability.md) | Every `&T` and `&mut T` carries a lifetime. Lifetimes annotate the scope over which the borrow is valid. |
| **Ownership** [→ T10](T10-ownership-moves.md) | The owner must outlive all borrows. Lifetimes encode this "outlives" relationship in signatures. |
| **Generics and Traits** [→ T04](T04-generics-bounds.md) | Type parameters can carry lifetime bounds (`T: 'a`). Trait objects require them (`dyn Trait + 'a`). |
| **Structs and Enums** [→ T01](T01-algebraic-data-types.md) | Structs storing references become generic over a lifetime, tying validity to the borrowed data. |
| **Smart Pointers** [→ T24](T24-smart-pointers.md) | Owned pointers (`Box<T>`, `Rc<T>`) eliminate lifetime annotations. `&'a T` vs `Box<T>` is often an ergonomics trade-off. |

## Gotchas and limitations

1. **The three elision rules — and when they fail.** (1) Each input reference gets its own lifetime, (2) if there is exactly one input lifetime it is assigned to all outputs, (3) if an input is `&self`/`&mut self`, that lifetime is assigned to all outputs. When none resolve the output you must annotate.

2. **`'static` does not mean "allocated in static memory."** It means the reference is valid for the *entire program*. String literals are `'static`; leaked data (`Box::leak`) is too. It only requires the data will never be freed.

3. **You cannot return a reference to a local variable.** Locals are dropped at function exit, so any reference to them would dangle (`error[E0515]`).
   ```rust
   fn bad() -> &str {
       let s = String::from("local");
       &s  // error[E0515]
   }
   ```

4. **Lifetime bounds on trait objects.** `dyn Trait` without an explicit lifetime defaults to `'static` in some contexts and a contextual lifetime in others. When in doubt, be explicit: `Box<dyn Trait + 'a>`.

5. **Structs holding references need lifetime parameters.** Forgetting the parameter produces `error[E0106]`.

6. **Over-constraining lifetimes.** Giving two inputs the same `'a` forces the compiler to use the shorter scope. Use separate parameters when references are independent.
   ```rust
   fn first_over<'a>(x: &'a str, y: &'a str) -> &'a str { x } // over-constrained
   fn first_free<'a>(x: &'a str, y: &str) -> &'a str { x }     // better
   ```

7. **A named lifetime does not create or extend a lifetime.** `'a` is a label for an existing scope. If the data is dropped, no annotation can save it.

8. **NLL (Non-Lexical Lifetimes).** Since Rust 2018, borrows end when last used, not at the enclosing scope boundary. Older blog posts may show now-unnecessary workarounds.

## Beginner mental model

Think of a lifetime as a **library due-date stamp** on a borrowed book. The stamp does not change how long the library owns the book — it records how long *your loan* is valid. If you read the book after the due date, the librarian (compiler) stops you. `fn borrow<'a>(book: &'a str) -> &'a str` means "the loan I hand out expires no later than the one I received."

When two inputs share `'a`, the compiler picks the shortest due date — the result is valid only as long as *both* inputs are. If only one input matters for the return value, give the other a separate lifetime to avoid over-constraining callers.

## Example A — Function with lifetime annotation: the `longest` pattern

```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() >= y.len() { x } else { y }
}

fn main() {
    let a = String::from("long string");
    {
        let b = String::from("hi");
        println!("{}", longest(&a, &b));  // OK — both alive in this scope
    }
    // longest(&a, &b) can't be used here — b was dropped
}
```

## Example B — Lifetime elision: when you don't need annotations

```rust
fn first_word(s: &str) -> &str {   // desugars to fn first_word<'a>(s: &'a str) -> &'a str
    let bytes = s.as_bytes();
    for (i, &b) in bytes.iter().enumerate() {
        if b == b' ' { return &s[..i]; }
    }
    s
}

fn main() {
    let sentence = String::from("hello world");
    println!("{}", first_word(&sentence));  // "hello"
}
```

## Example C — Struct holding a reference

```rust
struct Excerpt<'a> { text: &'a str }

impl<'a> Excerpt<'a> {
    fn announce(&self, ann: &str) -> &str {  // rule #3: output tied to &self
        println!("Attention: {ann}");
        self.text
    }
}

fn main() {
    let novel = String::from("Call me Ishmael. Some years ago...");
    let first = novel.split('.').next().expect("has a '.'");
    let e = Excerpt { text: first };   // e cannot outlive novel
    println!("{}", e.announce("news"));
}
```

## Example D — Multiple lifetime parameters

```rust
fn first_of<'a, 'b>(x: &'a str, y: &'b str) -> &'a str { x }

fn main() {
    let result;
    let outer = String::from("outer");
    {
        let inner = String::from("inner");
        result = first_of(&outer, &inner);  // result depends only on outer
    }
    println!("{result}");  // Safe — outer is still alive
}
```

If both parameters shared `'a`, the final `println!` would be rejected because `inner` was dropped.

## Example E — `'static` references and string literals

```rust
fn needs_static(val: &'static str) { println!("{val}"); }

fn main() {
    needs_static("literal");          // OK — string literals are 'static
    let owned = String::from("heap");
    // needs_static(&owned);           // error — owned String is not 'static
    let leaked: &'static str = Box::leak(owned.into_boxed_str());
    needs_static(leaked);              // OK — leaked data lives forever
}
```

## Example F — Lifetime bounds on generic types

```rust
use std::fmt::Display;

fn announce_and_return<'a, T: Display>(x: &'a str, ann: T) -> &'a str {
    println!("Announcement: {ann}");
    x
}

struct Wrapper<'a, T: Display + 'a> {   // T's references must outlive 'a
    value: &'a T,
}

fn main() {
    let num = 42;
    let w = Wrapper { value: &num };
    println!("wrapped: {}", w.value);
}
```

## Common compiler errors and how to read them

### `error[E0515]: cannot return reference to local variable`

```
error[E0515]: cannot return reference to local variable `s`
  |
3 |     &s
  |     ^^ returns a reference to data owned by the current function
```

**How to fix:** Return an owned value (`String` instead of `&str`), or accept data from the caller as a reference.

### `error[E0597]: does not live long enough`

```
error[E0597]: `short` does not live long enough
  |
6 |     result = longest(&a, &short);
  |                           ^^^^^^ borrowed value does not live long enough
7 | }   // `short` dropped here while still borrowed
```

**How to fix:** Extend the owner's scope, clone the data, or move the use into the scope where the owner is alive.

### `error[E0106]: missing lifetime specifier`

```
error[E0106]: missing lifetime specifier
  |
1 | fn pick(x: &str, y: &str) -> &str {
  |            ----     ----      ^ expected named lifetime parameter
  = help: the signature does not say whether it is borrowed from `x` or `y`
```

**How to fix:** Add a lifetime parameter: `fn pick<'a>(x: &'a str, y: &'a str) -> &'a str`.

### `error[E0621]: explicit lifetime required`

```
error[E0621]: explicit lifetime required in the type of `x`
  |
1 | fn foo(x: &i32) -> &'static i32 {
3 |     x
  |     ^ lifetime `'static` required
```

**How to fix:** Relax the output lifetime (`fn foo<'a>(x: &'a i32) -> &'a i32`), or ensure the input truly is `'static`.

## Use-case cross-references

- [→ UC-02](../usecases/UC20-ownership-apis.md) — Lifetime annotations encode borrowing contracts that callers cannot violate.
- [→ UC-05](../usecases/UC21-concurrency.md) — Thread-safety often requires `'static` bounds so data sent across threads cannot dangle.

## Source anchors

- `book/src/ch10-03-lifetime-syntax.md`
- `rust-by-example/src/scope/lifetime.md`
- `rust-by-example/src/scope/lifetime/struct.md`
- `rust-by-example/src/scope/lifetime/static_lifetime.md`
