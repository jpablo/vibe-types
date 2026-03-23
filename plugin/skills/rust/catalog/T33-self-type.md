# The Self Type

Since: Rust 1.0

## What it is

`Self` is a special keyword in Rust that refers to **the implementing type** within `impl` blocks and trait definitions. Inside `impl Widget`, `Self` means `Widget`. Inside `impl MyTrait for Foo`, `Self` means `Foo`. This allows trait definitions to be written generically without knowing the concrete type, and `impl` blocks to refer to their own type concisely.

Common uses include: **constructors** (`fn new() -> Self`), **builder patterns** (methods returning `Self` for chaining), **`From`/`Into` conversions** (`impl From<String> for Self`), and **trait definitions** that produce values of the implementing type (`fn clone(&self) -> Self`).

`Self` is only available inside `impl` blocks, trait definitions, and trait `impl` blocks. It cannot be used in free functions or at module scope.

## What constraint it enforces

**`Self` binds method signatures to the concrete implementing type, ensuring return types and parameter types are consistent with the type being defined.**

- `fn new() -> Self` in a trait means each implementor must return its own type, not some other type.
- `Self` in trait definitions affects object safety: traits with methods returning `Self` cannot be used as `dyn Trait` without workarounds.
- Using `Self` instead of the concrete type name makes refactoring safer -- renaming the type automatically updates all `Self` references.

## Minimal snippet

```rust
struct Point { x: f64, y: f64 }

impl Point {
    fn new(x: f64, y: f64) -> Self {
        Self { x, y }            // Self = Point
    }

    fn translate(self, dx: f64, dy: f64) -> Self {
        Self { x: self.x + dx, y: self.y + dy }
    }
}

fn main() {
    let p = Point::new(1.0, 2.0).translate(3.0, 4.0);
    println!("({}, {})", p.x, p.y);  // (4.0, 6.0)
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Traits** [-> catalog/T05](T05-type-classes.md) | `Self` in a trait definition refers to the future implementor. `fn clone(&self) -> Self` means "return my own type." |
| **Trait objects** [-> catalog/T36](T36-trait-objects.md) | Methods returning `Self` break object safety because the compiler cannot know the concrete return type behind `dyn Trait`. |
| **Conversions** [-> catalog/T18](T18-conversions-coercions.md) | `From` and `Into` use `Self` extensively: `impl From<String> for MyType { fn from(s: String) -> Self { ... } }`. |
| **Newtypes** [-> catalog/T03](T03-newtypes-opaque.md) | Newtype constructors idiomatically use `Self`: `fn new(val: u64) -> Self { Self(val) }`. |
| **Callable typing** [-> catalog/T22](T22-callable-typing.md) | Builder methods returning `Self` enable fluent APIs where each call returns the same type for chaining. |

## Gotchas and limitations

1. **`Self` in traits breaks object safety.** A method `fn make() -> Self` in a trait prevents `dyn Trait` because the size of `Self` is unknown. Workarounds include returning `Box<Self>` or removing the method from the object-safe subset via `where Self: Sized`.

2. **`Self` is always the *concrete* type, not a trait.** Inside `impl MyTrait for Foo`, `Self` is `Foo`, not `dyn MyTrait`. This matters when constructing values.

3. **Cannot use `Self` outside `impl` blocks.** `fn standalone() -> Self` in a free function is a compile error. `Self` is only meaningful where there is an implementing type.

4. **`Self` in associated type bounds.** `Self::Item` refers to the associated type of the current impl. This is valid and common but can create complex type relationships that confuse beginners.

5. **Shadowing with type aliases.** `type Self_ = Self;` is not valid. You cannot alias `Self` -- it is a keyword, not a type identifier.

## Beginner mental model

Think of `Self` as a **mirror** inside an `impl` block. When a struct looks in the mirror, it sees its own type. This lets you write methods that say "return one of me" or "accept another one of me" without spelling out the type name. In a trait, `Self` is a mirror that each implementor brings -- it reflects *their* type, not a fixed one.

## Example A -- Builder pattern with Self return

```rust
#[derive(Debug)]
struct Request {
    url: String,
    method: String,
    timeout: u64,
}

impl Request {
    fn new(url: &str) -> Self {
        Self { url: url.into(), method: "GET".into(), timeout: 30 }
    }

    fn method(mut self, m: &str) -> Self {
        self.method = m.into();
        self
    }

    fn timeout(mut self, secs: u64) -> Self {
        self.timeout = secs;
        self
    }
}

fn main() {
    let req = Request::new("https://api.example.com")
        .method("POST")
        .timeout(10);
    println!("{req:?}");
}
```

## Example B -- Self in trait definition and From conversion

```rust
trait Parseable {
    fn parse_from(s: &str) -> Option<Self> where Self: Sized;
}

struct Port(u16);

impl Parseable for Port {
    fn parse_from(s: &str) -> Option<Self> {
        s.parse::<u16>().ok().filter(|&p| p > 0).map(Self)
    }
}

impl From<u16> for Port {
    fn from(val: u16) -> Self {
        Self(val)
    }
}

fn main() {
    let p = Port::parse_from("8080").unwrap();
    println!("port = {}", p.0);

    let q: Port = 443.into();
    println!("port = {}", q.0);
}
```

## Use-case cross-references

- [-> UC-22](../usecases/UC22-conversions.md) -- `From`/`Into` patterns rely on `Self` to bind conversions to the target type.
- [-> UC-14](../usecases/UC14-extensibility.md) -- Traits using `Self` allow each implementor to produce its own type, enabling polymorphic construction.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- `where Self: Sized` bounds control which trait methods are available in generic vs dynamic-dispatch contexts.

## Source anchors

- `book/src/ch05-03-method-syntax.md`
- `rust-reference/src/paths.md` -- Self type
- `rust-reference/src/items/implementations.md`
