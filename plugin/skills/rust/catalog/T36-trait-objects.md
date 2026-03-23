# Trait Objects and `dyn`

## What it is

Rust favors *static dispatch* — when you write `fn draw<T: Draw>(item: &T)`, the compiler generates a specialized copy for every concrete `T`. This is called monomorphization: fast, inlineable code, but the concrete type must be known at compile time.

`dyn Trait` provides *runtime polymorphism*. Writing `&dyn Draw` or `Box<dyn Draw>` tells the compiler "I don't know the concrete type — dispatch method calls through a vtable at runtime." The concrete type is *erased*; the caller only sees the trait's interface. This is the same idea as virtual dispatch in C++ (explicit `virtual`) or Java/C# (virtual by default), but in Rust you opt in explicitly with `dyn`.

A trait object is a *fat pointer*: one machine-word pointer to the data and one to the *vtable*, a compiler-generated table of function pointers for every method the trait declares. Because the concrete type's size is unknown (`dyn Trait` is `!Sized`), trait objects must always live behind a pointer — `&dyn Trait`, `Box<dyn Trait>`, `Arc<dyn Trait>`, etc.

Not every trait qualifies. Rust enforces *object safety* rules: every method must be callable through a vtable without knowing `Self`'s size. If a trait returns `Self`, has generic methods, or otherwise depends on compile-time type information, the compiler rejects `dyn Trait` with `error[E0038]`.

## What constraint it enforces

**Only traits that satisfy object safety rules can be used as `dyn Trait`, and every method call goes through vtable indirection.**

- **No `Self` in return position.** `fn clone(&self) -> Self` is forbidden — the caller cannot allocate space for an unknown-sized return value.
- **No generic methods.** `fn convert<U>(&self, val: U)` would need infinite vtable entries, one per `U`.
- **All methods must be dispatchable.** The receiver must be `&self`, `&mut self`, or `self: Box<Self>`.
- **`where Self: Sized` opts a method out.** The method is removed from the vtable; the trait stays object-safe.
- **No non-auto trait combinations.** `dyn Draw + Send` is fine (`Send` is auto), but `dyn Draw + Debug` is not — only one non-auto trait is allowed.

## Minimal snippet

```rust
trait Draw { fn draw(&self); }

struct Circle;
impl Draw for Circle { fn draw(&self) { println!("circle"); } }

fn render(item: &dyn Draw) {
    item.draw(); // dispatched through the vtable at runtime
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Generics / `impl Trait`** [-> catalog/05, 06] | Generics give static dispatch (monomorphized, inlineable). `dyn Trait` gives dynamic dispatch (flexible, smaller binary). Choose generics when performance matters; choose `dyn` for heterogeneous collections or plugin-style extensibility. |
| **Lifetimes** [-> T48](T48-lifetimes.md) | Trait objects carry a lifetime bound: `dyn Trait + 'a`. `Box<dyn Trait>` defaults to `'static`; `&dyn Trait` inherits the reference's lifetime. Mismatched defaults are a common source of confusion. |
| **Smart Pointers** [-> T24](T24-smart-pointers.md) | `Box<dyn Trait>` gives owned heap storage. `Rc<dyn Trait>` and `Arc<dyn Trait>` add shared ownership. Each carries the fat pointer (data + vtable). |
| **Send and Sync** [-> T50](T50-send-sync.md) | `dyn Trait + Send` ensures the erased type can cross thread boundaries. Auto traits compose freely with the single non-auto trait. |
| **Enums** [-> T01](T01-algebraic-data-types.md) | Enums are the closed-set alternative: variants known at compile time, dispatch via `match`. Use enums for fixed sets; use `dyn Trait` for open/extensible sets. |

## Gotchas and limitations

1. **Object safety violations are the #1 surprise.** `Clone`, `Iterator` (`fn collect<B>`), and many other standard traits are not object-safe. You find out only when you write `dyn Clone` and get `error[E0038]`.

2. **Cannot downcast without `Any`.** Once erased, the concrete type is gone. Recovery requires the trait to extend `Any` plus `downcast_ref::<Concrete>()`, which adds complexity.

3. **Lifetime defaults can surprise you.** `Box<dyn Trait>` is implicitly `Box<dyn Trait + 'static>`, rejecting types with non-`'static` borrows. Write `Box<dyn Trait + 'a>` explicitly when needed.

4. **`dyn Trait` is `!Sized`.** It must always be behind a pointer. Forgetting this produces `error[E0277]`.

5. **Dynamic dispatch prevents inlining.** The compiler cannot see through a vtable call. In tight loops, profile before committing to `dyn`.

6. **Cannot combine multiple non-auto traits.** `dyn Read + Write` fails. The workaround is a super-trait:
   ```rust
   trait ReadWrite: std::io::Read + std::io::Write {}
   impl<T: std::io::Read + std::io::Write> ReadWrite for T {}
   fn process(stream: &mut dyn ReadWrite) { /* ... */ }
   ```

7. **Trait upcasting is new.** `dyn SubTrait` to `dyn SuperTrait` was stabilized in Rust 1.76. Older compilers need a manual `as_base()` helper.

## Beginner mental model

Think of a trait object as a **universal adapter plug**. You don't know whether the appliance behind it is a lamp, a fan, or a toaster — you only know it satisfies "can receive power." The vtable is the wiring diagram glued to the plug telling the socket which wires to use. You cannot do appliance-specific things (downcast) unless there is a special inspection hatch (`Any`).

The key tradeoff: **generics let the compiler see the concrete type and optimize aggressively; `dyn Trait` hides the type and pays a small runtime cost for flexibility.** Reach for `dyn` when you truly need a heterogeneous collection, a plugin boundary, or when generic type parameters would cascade through your entire API.

## Example A — Basic trait object with `&dyn Trait`

```rust
trait Greet {
    fn hello(&self) -> String;
}
struct English;
struct Spanish;
impl Greet for English { fn hello(&self) -> String { "Hello!".into() } }
impl Greet for Spanish { fn hello(&self) -> String { "Hola!".into() } }

fn print_greeting(g: &dyn Greet) {
    println!("{}", g.hello()); // vtable dispatch
}

fn main() {
    print_greeting(&English); // "Hello!"
    print_greeting(&Spanish); // "Hola!"
}
```

## Example B — Heterogeneous collection with `Vec<Box<dyn Trait>>`

```rust
trait Shape { fn area(&self) -> f64; }

struct Circle { r: f64 }
struct Rect   { w: f64, h: f64 }

impl Shape for Circle { fn area(&self) -> f64 { std::f64::consts::PI * self.r * self.r } }
impl Shape for Rect   { fn area(&self) -> f64 { self.w * self.h } }

fn main() {
    let shapes: Vec<Box<dyn Shape>> = vec![
        Box::new(Circle { r: 2.0 }),
        Box::new(Rect { w: 3.0, h: 4.0 }),
    ];
    for s in &shapes { println!("area = {:.2}", s.area()); }
}
```

## Example C — Object safety violation and the fix

```rust
// NOT object-safe: `clone_self` returns `Self`
trait Widget {
    fn name(&self) -> &str;
    fn clone_self(&self) -> Self; // prevents `dyn Widget`
}

// Fix: opt the problematic method out of the vtable
trait WidgetSafe {
    fn name(&self) -> &str;
    fn clone_self(&self) -> Self where Self: Sized; // unavailable via dyn
}

struct Button;
impl WidgetSafe for Button {
    fn name(&self) -> &str { "Button" }
    fn clone_self(&self) -> Self { Button }
}

fn print_name(w: &dyn WidgetSafe) {
    println!("{}", w.name()); // OK
    // w.clone_self();        // error: method requires `Self: Sized`
}
```

## Example D — `Box<dyn Trait>` for owned trait objects

```rust
trait Logger { fn log(&self, msg: &str); }

struct FileLogger { path: String }
impl Logger for FileLogger {
    fn log(&self, msg: &str) { println!("[{}] {msg}", self.path); }
}

struct App { logger: Box<dyn Logger> }

fn main() {
    let app = App { logger: Box::new(FileLogger { path: "/var/log/app.log".into() }) };
    app.logger.log("started"); // dynamic dispatch through Box
}
```

## Example E — Trait objects with lifetimes

```rust
trait Summarize { fn summary(&self) -> &str; }

struct Article<'a> { headline: &'a str }
impl<'a> Summarize for Article<'a> {
    fn summary(&self) -> &str { self.headline }
}

// Explicit lifetime: the trait object may borrow non-'static data
fn print_summary<'a>(item: &(dyn Summarize + 'a)) {
    println!("{}", item.summary());
}

fn main() {
    let text = String::from("Rust 2024 Edition Released");
    let article = Article { headline: &text };
    print_summary(&article);
}
// Box<dyn Summarize> defaults to 'static — use Box<dyn Summarize + 'a> instead.
```

## Example F — Static vs dynamic dispatch side-by-side

```rust
trait Render { fn render(&self) -> String; }
struct Png;
struct Svg;
impl Render for Png { fn render(&self) -> String { "PNG bytes".into() } }
impl Render for Svg { fn render(&self) -> String { "<svg/>".into() } }

// Static: monomorphized per type, inlineable
fn render_static<T: Render>(item: &T) -> String { item.render() }

// Dynamic: single function body, vtable lookup
fn render_dynamic(item: &dyn Render) -> String { item.render() }

fn main() {
    println!("{}", render_static(&Png));  // direct call to Png::render
    println!("{}", render_dynamic(&Svg)); // vtable call to Svg::render
}
```

## Common compiler errors and how to read them

### `error[E0038]: the trait 'X' cannot be made into an object`

```
error[E0038]: the trait `Clone` cannot be made into an object
 --> src/main.rs:5:17
  |
5 |     let x: &dyn Clone = &value;
  |                 ^^^^^ `Clone` cannot be made into an object
```

**How to fix:** The trait violates object safety. Common causes: returning `Self`, generic methods, or `Self: Sized` on the trait. Add `where Self: Sized` to individual methods, or create an object-safe wrapper trait.

### `error[E0277]: the size for values of type 'dyn Trait' cannot be known`

```
error[E0277]: the size for values of type `dyn Draw` cannot be known
 --> src/main.rs:8:9
  |
8 |     let item: dyn Draw = circle;
  |         ^^^^ doesn't have a size known at compile-time
```

**How to fix:** Place the trait object behind a pointer: `&dyn Draw`, `Box<dyn Draw>`, or `Arc<dyn Draw>`.

### `error[E0308]: mismatched types` (concrete vs `dyn`)

```
error[E0308]: mismatched types
 --> src/main.rs:12:5
  |
11 | fn make() -> Box<dyn Draw> {
12 |     Circle
  |     ^^^^^^ expected `Box<dyn Draw>`, found `Circle`
```

**How to fix:** Wrap the value: `Box::new(Circle)`. The coercion from `Box<Circle>` to `Box<dyn Draw>` is automatic once the `Box` exists.

### `error[E0782]: trait objects must include the 'dyn' keyword`

```
error[E0782]: trait objects must include the `dyn` keyword
 --> src/main.rs:4:16
  |
4 | fn render(item: &Draw) {
  |                  ^^^^
```

**How to fix:** Write `&dyn Draw` instead of `&Draw`. Since Rust 2021 the `dyn` keyword is mandatory for trait objects.

## Use-case cross-references

- [-> UC-04](../usecases/UC14-extensibility.md) — Plugin architectures rely on `dyn Trait` to accept types defined outside the core crate, enabling open-ended extensibility.
- [-> UC-02](../usecases/UC20-ownership-apis.md) — APIs that accept `Box<dyn Trait>` transfer ownership of an erased value, combining ownership semantics with type erasure.
- [-> UC-05](../usecases/UC21-concurrency.md) — `dyn Trait + Send` ensures trait objects can be shipped across threads safely.

## Source anchors

- `book/src/ch18-02-trait-objects.md`
- `rust-by-example/src/trait/dyn.md`
- `reference/src/types/trait-object.md`
- `rust-lang/rfcs/2113-dyn-trait-syntax.md` (the `dyn` keyword RFC)
- `rust-lang/rfcs/3324-dyn-upcasting.md` (trait upcasting stabilization)
