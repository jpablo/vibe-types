# Newtype Pattern and Opaque Wrappers

Since: Rust 1.0

## What it is

The newtype pattern wraps an existing type in a single-field tuple struct -- `struct UserId(u64)` -- creating a **distinct type** at zero runtime cost. The compiler erases the wrapper entirely: in the generated machine code a `UserId` is just a `u64`. Yet at the type level `UserId` and `u64` are incompatible, so you cannot accidentally pass a raw `u64` where a `UserId` is expected.

By keeping the inner field **private** (the default), the module that defines the newtype controls construction, validation, and access. Callers must use an explicit constructor (e.g., `UserId::new(42)`) and an accessor (e.g., `id.get()`), giving the author a place to enforce invariants -- non-zero values, length limits, format checks -- once and for all.

Contrast this with **type aliases** (`type UserId = u64`), which create an alternative *name* for the same type. A type alias does **not** prevent mixing: `fn greet(id: UserId)` still accepts any `u64`. Newtypes prevent mixing; aliases do not. See [-> catalog/T23](T23-type-aliases.md).

## What constraint it enforces

**Values of the wrapped type cannot be used where the newtype is expected, and vice versa, unless the author provides an explicit conversion.**

- The compiler rejects assignment, argument passing, and comparison between the newtype and its inner type.
- Private inner fields prevent external code from constructing or destructuring the wrapper, funneling all creation through validated constructors.
- Newtypes bypass the orphan rule: you can implement a foreign trait on a foreign type by wrapping it first [-> catalog/T25](T25-coherence-orphan.md).

## Minimal snippet

```rust
struct UserId(u64);          // inner field is private outside this module

impl UserId {
    pub fn new(id: u64) -> Self { Self(id) }
    pub fn get(&self) -> u64  { self.0 }
}

fn lookup(id: UserId) -> String {
    format!("user#{}", id.get())
}

// lookup(42);              // error[E0308]: expected `UserId`, found integer
lookup(UserId::new(42));    // OK
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type aliases** [-> catalog/T23](T23-type-aliases.md) | Aliases are transparent synonyms; newtypes are opaque wrappers. Choose newtypes when you need the compiler to prevent mixing. |
| **Traits** [-> catalog/T05](T05-type-classes.md) | You can implement any trait on a newtype -- including foreign traits on foreign inner types -- bypassing the orphan rule. |
| **Derive macros** [-> catalog/T06](T06-derivation.md) | `#[derive(Debug, Clone, PartialEq)]` works on newtypes. The derived impls delegate to the inner type's impls. |
| **PhantomData** [-> catalog/T27](T27-erased-phantom.md) | Newtypes can carry a `PhantomData<Tag>` for typestate or tag-based differentiation without runtime overhead. |
| **Encapsulation** [-> catalog/T21](T21-encapsulation.md) | Private inner fields are the mechanism that makes newtypes truly opaque. Without privacy you just have a transparent wrapper. |
| **From / Into conversions** [-> catalog/T18](T18-conversions-coercions.md) | Implementing `From<u64> for UserId` provides ergonomic explicit conversion while keeping the types distinct. |

## Gotchas and limitations

1. **No automatic trait delegation.** `struct Email(String)` does not implement `Display`, `AsRef<str>`, or any other `String` trait. You must implement each one manually or use `Deref` -- but `Deref` to the inner type erodes the type safety you were seeking.

2. **Deref abuse.** Implementing `Deref<Target = InnerType>` lets callers use all inner-type methods on the newtype, which silently defeats the purpose of the wrapper. Prefer explicit accessor methods.

3. **Pattern matching exposes the inner field within the module.** Inside the defining module, `let UserId(raw) = id;` works because the field is visible. This is correct behavior but can surprise if you expect the wrapper to be opaque everywhere.

4. **Serde requires extra work.** By default `#[derive(Serialize, Deserialize)]` on a tuple struct serializes as a one-element array. Use `#[serde(transparent)]` to serialize/deserialize as the inner type directly.

5. **No generic newtype shorthand.** Each newtype needs its own struct declaration. For many wrappers consider a macro or a crate like `derive_more` to reduce boilerplate.

## Beginner mental model

Think of a newtype as a **labeled envelope**. The letter inside (the inner type) is the same, but the label on the outside (`UserId` vs `OrderId`) determines which mailbox it fits into. The compiler checks labels at every handoff, so you can never put a letter in the wrong mailbox. Making the envelope sealed (private inner field) means only the post office (the defining module) can open or seal it.

## Example A -- Validated newtype with private field

```rust
#[derive(Debug, Clone, PartialEq)]
pub struct Email(String);

impl Email {
    pub fn parse(raw: &str) -> Result<Self, &'static str> {
        if raw.contains('@') {
            Ok(Self(raw.to_owned()))
        } else {
            Err("missing '@' in email address")
        }
    }

    pub fn as_str(&self) -> &str { &self.0 }
}

fn send(to: &Email) {
    println!("sending to {}", to.as_str());
}

fn main() {
    let addr = Email::parse("alice@example.com").unwrap();
    send(&addr);
    // send(&String::from("not-an-email")); // error[E0308]
}
```

## Example B -- Orphan-rule workaround

```rust
use std::fmt;

struct PrettyVec(Vec<i32>);

impl fmt::Display for PrettyVec {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let inner = self.0.iter()
            .map(|n| n.to_string())
            .collect::<Vec<_>>()
            .join(", ");
        write!(f, "[{inner}]")
    }
}

fn main() {
    let v = PrettyVec(vec![1, 2, 3]);
    println!("{v}");   // [1, 2, 3]
}
```

You cannot `impl Display for Vec<i32>` directly because both are foreign. Wrapping in a newtype makes the outer type local.

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Newtypes make invalid raw values unrepresentable by requiring validated construction.
- [-> UC-20](../usecases/UC20-ownership-apis.md) -- Newtypes encode domain distinctions in API signatures, preventing callers from supplying the wrong kind of value.
- [-> UC-22](../usecases/UC22-conversions.md) -- `From`/`Into` impls on newtypes provide explicit, type-safe conversions.

## Source anchors

- `book/src/ch19-04-advanced-types.md` -- "Using the Newtype Pattern"
- `rust-by-example/src/generics/new_types.md`
- `rust-reference/src/items/structs.md`
- `api-guidelines/src/type-safety.md` -- C-NEWTYPE
