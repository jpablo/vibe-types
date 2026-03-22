# Structs, Enums, and Newtypes

## What it is

Rust provides three fundamental mechanisms for defining custom data types: **structs**, **enums**, and the **newtype pattern**. Together they let you model your domain precisely so that invalid states become unrepresentable at compile time. Unlike languages where data modeling is loosely typed or relies on runtime checks, Rust's type system makes the structure of your data an enforceable contract.

**Structs** are *product types* — they combine several named fields into a single unit. Rust offers three flavors: named-field structs (`struct User { name: String, age: u32 }`), tuple structs (`struct Pair(i32, i32)`), and unit structs (`struct Marker;`). Named-field structs are the workhorse for most domain modeling; tuple structs shine when position is more meaningful than a name; unit structs act as zero-size markers for trait implementations and type-level programming.

**Enums** are *sum types* — a value is exactly one of several variants at any given time, and each variant may carry its own data. This is fundamentally different from enums in C or Java, which are little more than named integer constants. Rust enums are closer to *algebraic data types* in Haskell or OCaml: a variant can hold no data (`Quit`), a tuple of values (`Move(i32, i32)`), or a full set of named fields (`Login { user: String, token: String }`). The compiler enforces *exhaustive matching*, meaning every `match` expression must account for every variant — if you add a new variant, every consumer is forced to handle it or the code will not compile.

The **newtype pattern** wraps an existing type in a single-field tuple struct to create a distinct type at zero runtime cost. `struct Email(String)` and `struct Username(String)` are both `String` underneath, but the compiler treats them as incompatible types, preventing you from accidentally passing a username where an email is expected. Newtypes are the idiomatic Rust way to add domain semantics, implement foreign traits on foreign types (the orphan rule workaround), and restrict the API surface of an inner type.

## What constraint it enforces

**Only explicitly modeled states are constructible, and pattern matching forces callers to handle every declared variant.**

More specifically:

- **No unnamed states.** Every possible state of a value must be a declared struct or enum variant. There is no null, no uninitialized memory, and no implicit default — you must explicitly construct one of the defined shapes.
- **Exhaustive matching.** A `match` on an enum must cover every variant. The compiler refuses to compile incomplete matches, so adding a variant is guaranteed to surface every site that needs updating.
- **Field-level encapsulation.** Struct fields are private by default. A public struct with private fields cannot be constructed outside its module, forcing callers through constructor functions that can enforce invariants.
- **Distinct types via newtypes.** Two newtypes wrapping the same inner type are incompatible. This prevents accidental misuse at the type level, not just at runtime.

## Minimal snippet

```rust
enum Payment {
    Cash,
    Card { last4: u16 },
}

struct Email(String);          // newtype — distinct from raw String

fn process(p: Payment) {
    match p {
        Payment::Cash => println!("paid cash"),
        Payment::Card { last4 } => println!("card ending {last4}"),
    }
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Ownership & Moves** [-> catalog/01] | Each field of a struct or enum variant is independently owned. Moving a non-`Copy` field out of a struct creates a partial move that invalidates the struct as a whole. |
| **Borrowing** [-> catalog/02] | You can borrow individual fields of a struct or destructure a reference to an enum variant. The borrow checker tracks each field independently. |
| **Traits** [-> catalog/06] | `#[derive(...)]` auto-implements common traits (`Debug`, `Clone`, `PartialEq`, etc.) for structs and enums. Newtypes frequently need manual trait impls or `Deref` to expose inner-type behavior. |
| **Generics** [-> catalog/07] | Structs and enums can be generic over types and lifetimes (`Option<T>`, `Result<T, E>`). This is the foundation of Rust's polymorphism story. |
| **Pattern Matching** | `match`, `if let`, and `let..else` destructure structs and enums, binding fields to local variables. Guards (`if` clauses in match arms) add conditional logic. |
| **Visibility / Modules** | Fields default to private; enum variants inherit their enum's visibility. Module boundaries control who can construct or destructure a type. |

## Gotchas and limitations

1. **Struct update syntax moves non-`Copy` fields.** The `..source` syntax copies `Copy` fields and *moves* everything else, invalidating the source for those fields.

   ```rust
   struct Config { name: String, retries: u32 }
   let a = Config { name: "alpha".into(), retries: 3 };
   let b = Config { retries: 5, ..a };  // `a.name` is moved into `b`
   // println!("{}", a.name);           // error[E0382]: use of moved value
   println!("{}", a.retries);           // OK — u32 is Copy
   ```

2. **Enum variants are not types.** You cannot use `Payment::Cash` as a standalone type in a function signature. Each variant is a *constructor* of the enum, not an independent type. If you need a variant to be its own type, extract it into a separate struct and reference it from the variant.

3. **Adding a variant is a breaking change.** For library crates, adding a new enum variant forces every downstream `match` to be updated. Use `#[non_exhaustive]` on the enum to require a wildcard arm in external crates, reserving the right to add variants without a semver-major bump.

4. **Newtypes need manual trait delegation.** A `struct Email(String)` does not automatically implement `Display`, `AsRef<str>`, or any other trait from `String`. You must implement each trait yourself or use `Deref` to forward to the inner type — but `Deref` can erode the type-safety you were seeking.

5. **Field visibility defaults differ.** Struct fields default to **private**; enum variant fields are **public** whenever the enum itself is public. This asymmetry surprises newcomers who expect enums to behave like structs.

6. **`ref` vs move in patterns.** Destructuring a value in a `match` arm *moves* non-`Copy` fields by default. Use `ref` (or match on a reference `&val`) to borrow instead.

   ```rust
   let opt = Some(String::from("data"));
   match &opt {                         // matching on a reference
       Some(s) => println!("{s}"),      // `s` is `&String`, no move
       None => {}
   }
   println!("{:?}", opt);               // `opt` is still valid
   ```

7. **`#[non_exhaustive]` on structs prevents external construction.** A `#[non_exhaustive]` struct cannot be constructed with literal syntax outside its defining crate, even if all fields are public. External consumers must use a provided constructor or builder.

8. **`mem::size_of` for enums includes tag + largest variant.** An enum is as large as its biggest variant plus a discriminant tag. A single variant with a large payload inflates the size of every instance, even lightweight variants.

## Beginner mental model

Think of a **struct** as a labeled form: every field has a name and a type, and you must fill in every blank to create an instance. A **tuple struct** is the same idea but the blanks are identified by position instead of name, and a **unit struct** is a form with no blanks at all — it simply exists as a unique marker.

An **enum** is a choice with consequences. Imagine a physical switch with labeled positions — `Cash`, `Card`, `Crypto` — where each position may have its own set of associated paperwork. The switch can only be in one position at a time, and the compiler's exhaustive `match` is like a checklist: you must write handling code for every position before the program will compile. The **newtype** pattern is like putting a labeled sticker on an envelope — the envelope still holds the same letter (`String`), but the label (`Email` vs `Username`) prevents you from misfiling it.

## Example A — Basic struct with named fields

```rust
struct User {
    name: String,
    email: String,
    active: bool,
}

fn main() {
    let user = User {
        name: String::from("Alice"),
        email: String::from("alice@example.com"),
        active: true,
    };
    println!("{} <{}>", user.name, user.email);
}
```

## Example B — Enum with data-carrying variants and exhaustive match

```rust
enum Shape {
    Circle(f64),                         // radius
    Rectangle { width: f64, height: f64 },
    Point,                               // unit variant — no data
}

fn area(s: &Shape) -> f64 {
    match s {
        Shape::Circle(r)                          => std::f64::consts::PI * r * r,
        Shape::Rectangle { width, height }        => width * height,
        Shape::Point                              => 0.0,
    }
}

fn main() {
    let shapes = vec![
        Shape::Circle(3.0),
        Shape::Rectangle { width: 4.0, height: 5.0 },
        Shape::Point,
    ];
    for s in &shapes {
        println!("area = {:.2}", area(s));
    }
}
```

## Example C — Newtype pattern for domain safety

```rust
struct Email(String);
struct Username(String);

fn send_welcome(email: &Email) {
    println!("Sending welcome to {}", email.0);
}

fn main() {
    let addr = Email(String::from("bob@example.com"));
    let user = Username(String::from("bob"));

    send_welcome(&addr);      // OK
    // send_welcome(&user);   // error[E0308]: expected `&Email`, found `&Username`
}
```

The compiler catches the mix-up at build time — no runtime check needed.

## Example D — Tuple structs and unit structs

```rust
// Tuple struct — fields accessed by index
struct Coordinate(f64, f64);

// Unit struct — zero-size type, useful as a marker
struct Production;

trait Logger {
    fn log(&self, msg: &str);
}

impl Logger for Production {
    fn log(&self, msg: &str) { println!("[PROD] {msg}"); }
}

fn main() {
    let origin = Coordinate(0.0, 0.0);
    println!("x={}, y={}", origin.0, origin.1);

    let logger = Production;
    logger.log("system started");
}
```

## Example E — `#[non_exhaustive]` and why libraries use it

```rust
// In a library crate:
#[non_exhaustive]
pub enum DatabaseError {
    ConnectionLost,
    Timeout,
    QueryFailed(String),
}

// In a downstream crate:
fn handle(err: DatabaseError) {
    match err {
        DatabaseError::ConnectionLost => reconnect(),
        DatabaseError::Timeout        => retry(),
        DatabaseError::QueryFailed(q) => log_bad_query(&q),
        _                             => fallback(), // required by #[non_exhaustive]
    }
}
```

Without the wildcard arm, the downstream `match` would fail to compile. This lets the library add new variants (e.g., `AuthFailed`) in a minor release without breaking dependents.

## Example F — Pattern matching with destructuring and guards

```rust
enum Command {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
}

fn execute(cmd: Command) {
    match cmd {
        Command::Quit => println!("quitting"),
        Command::Move { x, y } if x == 0 && y == 0 => {
            println!("move to origin — no-op");
        }
        Command::Move { x, y } => {
            println!("moving to ({x}, {y})");
        }
        Command::Write(ref text) if text.is_empty() => {
            println!("ignoring empty write");
        }
        Command::Write(text) => {
            println!("writing: {text}");
        }
    }
}

fn main() {
    execute(Command::Move { x: 0, y: 0 });
    execute(Command::Write(String::from("hello")));
    execute(Command::Write(String::new()));
    execute(Command::Quit);
}
```

Guards (`if` clauses) refine which arm matches. Note the use of `ref text` in the fourth arm to borrow instead of move, so the binding does not consume the `String`.

## Common compiler errors and how to read them

### `error[E0063]: missing field in initializer`

You left out one or more required fields when constructing a struct.

```
error[E0063]: missing field `email` in initializer of `User`
 --> src/main.rs:8:16
  |
8 |     let u = User { name: "Alice".into(), active: true };
  |                ^^^^ missing `email`
```

**How to fix:** Supply the missing field, or if the struct implements `Default`, use `..Default::default()` to fill remaining fields.

### `error[E0027]: pattern does not mention field`

A struct pattern omits a field that the compiler expects you to handle.

```
error[E0027]: pattern does not mention field `active`
 --> src/main.rs:4:9
  |
4 |     let User { name, email } = user;
  |         ^^^^^^^^^^^^^^^^^^^^^^^^ missing field `active`
```

**How to fix:** Add the missing binding or use `..` to explicitly ignore remaining fields: `let User { name, email, .. } = user;`

### `error[E0004]: non-exhaustive patterns`

A `match` does not cover every variant of an enum.

```
error[E0004]: non-exhaustive patterns: `Shape::Point` not covered
 --> src/main.rs:10:11
   |
10 |     match s {
   |           ^ pattern `Shape::Point` not covered
```

**How to fix:** Add an arm for each uncovered variant, or add a wildcard (`_ =>`) if appropriate. If matching a `#[non_exhaustive]` enum, a wildcard arm is mandatory.

### `error[E0308]: mismatched types (enum variant confusion)`

Passing the wrong newtype or an incorrect variant where a specific type is expected.

```
error[E0308]: mismatched types
 --> src/main.rs:12:19
   |
12 |     send_welcome(&user);
   |                  ^^^^^ expected `&Email`, found `&Username`
```

**How to fix:** Ensure you are passing the correct type. Newtypes exist precisely to catch this class of bug — trace back to where the value was constructed and verify you used the right wrapper.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Structs and enums are the primary tool for making invalid states unrepresentable: if the type cannot hold it, the program cannot produce it.
- [-> UC-02](../usecases/UC20-ownership-apis.md) — Newtypes encode domain distinctions in function signatures, preventing callers from supplying the wrong kind of value.
- [-> UC-05](../usecases/UC21-concurrency.md) — Enums model finite state machines; exhaustive matching ensures every state transition is handled.

## Source anchors

- `book/src/ch05-01-defining-structs.md`
- `book/src/ch05-02-example-structs.md`
- `book/src/ch06-01-defining-an-enum.md`
- `book/src/ch06-02-match.md`
- `book/src/ch18-03-pattern-syntax.md`
- `rust-by-example/src/custom_types/structs.md`
- `rust-by-example/src/custom_types/enum.md`
- `rust-reference/src/items/structs.md`
- `rust-reference/src/items/enumerations.md`
