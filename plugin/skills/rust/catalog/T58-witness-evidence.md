# Witness and Evidence Types (via PhantomData and Marker Traits)

> **Since:** Rust 1.0 (PhantomData, marker traits); patterns evolved with sealed traits and typestate idioms

## What it is

Rust does not have a built-in evidence or witness type system like Scala's `=:=` or Lean's propositions-as-types. Instead, **evidence is encoded through zero-size marker types and sealed traits**. A type like `PhantomData<Authenticated>` acts as a proof token -- its presence in a struct proves that some validation step has occurred. Sealed traits (traits with no public implementors) serve as capability evidence: only code within the defining module can create values that implement the trait.

The pattern works because Rust's type system prevents constructing the marker type from outside the module boundary. If `Authenticated` is a zero-size struct with a private constructor, only the `authenticate()` function can produce it. Any API that requires `Token<Authenticated>` as a parameter effectively requires proof that authentication has succeeded.

## What constraint it enforces

**Marker types and sealed traits restrict API access to callers that hold evidence values. The evidence cannot be forged because the constructors are private, and the types carry no runtime cost because they are zero-sized.**

- `PhantomData<State>` tags a struct with a compile-time state that gates method availability.
- Sealed traits ensure only trusted code can implement the evidence interface.
- Zero-size evidence is erased at runtime -- no memory or performance overhead.

## Minimal snippet

```rust
mod auth {
    use std::marker::PhantomData;

    pub struct Verified;    // ZST — cannot be constructed outside this module
    pub struct Unverified;

    pub struct Email<S> {
        addr: String,
        _state: PhantomData<S>,
    }

    impl Email<Unverified> {
        pub fn new(addr: String) -> Self {
            Email { addr, _state: PhantomData }
        }

        pub fn verify(self) -> Result<Email<Verified>, String> {
            if self.addr.contains('@') {
                Ok(Email { addr: self.addr, _state: PhantomData })
            } else {
                Err("invalid email".into())
            }
        }
    }

    pub fn send(email: &Email<Verified>, body: &str) {
        println!("Sending to {}: {}", email.addr, body);
    }
}

fn main() {
    let raw = auth::Email::new("alice@example.com".into());
    // auth::send(&raw, "hi");  // error: expected Email<Verified>, found Email<Unverified>

    let verified = raw.verify().unwrap();
    auth::send(&verified, "hi");  // OK — evidence of verification
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **PhantomData** [-> catalog/T27](T27-erased-phantom.md) | PhantomData is the primary mechanism for carrying evidence at zero cost. The marker type parameter IS the evidence. |
| **Newtypes** [-> catalog/T03](T03-newtypes-opaque.md) | A newtype wrapping a value with a private constructor is itself a form of evidence -- possessing a `ValidatedInput(String)` proves validation occurred. |
| **Ownership and moves** [-> catalog/T10](T10-ownership-moves.md) | Evidence tokens are consumed by move, ensuring single-use proofs. A `fn consume(proof: AuthToken)` takes ownership, preventing reuse. |
| **Sealed traits** [-> catalog/T21](T21-encapsulation.md) | `pub trait Sealed: private::Sealed {}` prevents external implementations. Only the crate can create evidence of the sealed trait. |
| **Trait objects** [-> catalog/T36](T36-trait-objects.md) | Evidence traits can be used as trait objects for dynamic dispatch, though this sacrifices the compile-time guarantees for flexibility. |

## Gotchas and limitations

1. **No compiler-assisted evidence synthesis.** Unlike Scala's `summon` or Lean's tactics, Rust requires you to manually thread evidence values through function calls. There is no implicit resolution for evidence types.

2. **Evidence is unforgeable only by convention.** If the marker type's constructor is accidentally made public, any code can forge evidence. Always keep evidence constructors private and audit `pub` visibility carefully.

3. **Sealed trait boilerplate.** The sealed trait pattern requires a private super-trait in a private module. This is idiomatic but verbose. There is no language-level `sealed` keyword in Rust.

4. **PhantomData construction noise.** Every struct literal must include `_marker: PhantomData`. Use constructor functions to hide this from API consumers.

5. **No negation evidence.** You cannot express "this type does NOT implement Trait" in Rust's type system. Negative trait bounds are unstable and not generally available.

## Beginner mental model

Think of evidence types as **tamper-proof wristbands** applied at a checkpoint. The `verify()` function is the checkpoint -- it checks your email and, if valid, snaps on a `Verified` wristband (the phantom type tag). The `send()` function is a bouncer who only admits people wearing the `Verified` wristband. You cannot buy the wristband at a store (the constructor is private) -- you must go through the checkpoint. The wristband weighs nothing (zero-size type) and is checked at compile time, not runtime.

## Example A -- Capability tokens for database access

```rust
mod db {
    use std::marker::PhantomData;

    pub struct ReadOnly;
    pub struct ReadWrite;

    pub struct Connection<Mode> {
        _mode: PhantomData<Mode>,
    }

    pub fn connect_ro() -> Connection<ReadOnly> {
        Connection { _mode: PhantomData }
    }

    pub fn connect_rw(password: &str) -> Connection<ReadWrite> {
        assert!(!password.is_empty(), "password required");
        Connection { _mode: PhantomData }
    }

    pub fn query<M>(_conn: &Connection<M>, sql: &str) -> Vec<String> {
        println!("SELECT: {sql}");
        vec![]
    }

    pub fn execute(_conn: &Connection<ReadWrite>, sql: &str) {
        println!("EXECUTE: {sql}");
    }
}

fn main() {
    let ro = db::connect_ro();
    db::query(&ro, "SELECT * FROM users");
    // db::execute(&ro, "DROP TABLE users");  // error: expected Connection<ReadWrite>

    let rw = db::connect_rw("secret");
    db::execute(&rw, "INSERT INTO users VALUES (1)");  // OK
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Evidence tokens make unauthorized operations (sending unverified email, writing to a read-only connection) unrepresentable at the type level.
- [-> UC-13](../usecases/UC13-state-machines.md) -- Typestate with PhantomData evidence models state machines where transitions require proof of the current state.
- [-> UC-20](../usecases/UC20-ownership-apis.md) -- Evidence tokens leverage ownership to ensure single-use proofs and capability transfer.

## Source anchors

- `std::marker::PhantomData` documentation
- `nomicon/src/phantom-data.md`
- "Typestate pattern in Rust" (Rust API Guidelines)
- `rust-reference/src/items/traits.md` -- sealed trait pattern
