# PhantomData and Zero-Size Type Markers

Since: Rust 1.0

## What it is

`PhantomData<T>` is a **zero-size type** (ZST) from `std::marker` that tells the compiler "this type logically contains or is associated with a `T`, even though no actual `T` value is stored." It occupies zero bytes at runtime but participates fully in the type system at compile time.

Primary uses include: **variance control** (making a type covariant, contravariant, or invariant over a lifetime or type parameter), **lifetime annotation** (declaring that a struct borrows data with a certain lifetime even when no reference field exists), **typestate patterns** (tagging a type with a phantom type parameter to represent states like `Locked`/`Unlocked`), and **tag types** (distinguishing otherwise identical structs like `Id<User>` vs `Id<Order>`).

Without `PhantomData`, the compiler issues `error[E0392]: parameter T is never used` for unused type parameters. `PhantomData` resolves this while communicating the *logical* relationship to both the compiler and human readers.

## What constraint it enforces

**`PhantomData<T>` causes the compiler to treat the enclosing type as if it contains a `T`, applying the same variance, drop-check, and auto-trait rules that would apply to a real `T` field.**

- A struct with `PhantomData<&'a T>` is treated as borrowing a `&'a T`, so it cannot outlive `'a`.
- A struct with `PhantomData<T>` is considered to own a `T` for drop-check purposes.
- Auto-traits (`Send`, `Sync`) are blocked if `T` does not implement them.

## Minimal snippet

```rust
use std::marker::PhantomData;

struct Id<T> {
    value: u64,
    _marker: PhantomData<T>,
}

struct User;
struct Order;

fn process_user(id: Id<User>) {
    println!("user #{}", id.value);
}

fn main() {
    let uid = Id::<User> { value: 42, _marker: PhantomData };
    process_user(uid);

    let oid = Id::<Order> { value: 42, _marker: PhantomData };
    // process_user(oid);  // error[E0308]: expected `Id<User>`, found `Id<Order>`
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Newtypes** [-> catalog/T03](T03-newtypes-opaque.md) | A newtype with `PhantomData` creates a zero-cost tagged wrapper: `struct Meters(f64, PhantomData<MeterTag>)`. |
| **Variance & subtyping** [-> catalog/T08](T08-variance-subtyping.md) | `PhantomData<fn() -> T>` makes a type covariant in `T`; `PhantomData<fn(T)>` makes it contravariant. This is the primary tool for controlling variance. |
| **Lifetimes** [-> catalog/T48](T48-lifetimes.md) | `PhantomData<&'a ()>` ties a struct to lifetime `'a` without storing an actual reference. |
| **Compile-time ops** [-> catalog/T16](T16-compile-time-ops.md) | Const generics can sometimes replace phantom type parameters for numeric tags, but `PhantomData` remains essential for type-level and lifetime tagging. |
| **Send / Sync** [-> catalog/T50](T50-send-sync.md) | `PhantomData<*const T>` makes a type `!Send` and `!Sync`, useful for types that logically contain raw pointers. |

## Gotchas and limitations

1. **Drop-check implications.** `PhantomData<T>` tells the compiler the type may drop a `T`. If `T` has a destructor, this can trigger stricter lifetime requirements. Use `PhantomData<*const T>` for a weaker "does not own" relationship.

2. **Variance is subtle.** `PhantomData<T>` makes the type covariant in `T` (like owning a `T`). `PhantomData<fn(T)>` makes it contravariant. Getting this wrong can cause confusing lifetime errors. See [-> catalog/T08](T08-variance-subtyping.md).

3. **Construction noise.** Every struct literal must include `_marker: PhantomData`. The `PhantomData` field cannot be elided. Use a constructor function to hide this from callers.

4. **ZST arrays.** `[PhantomData<T>; N]` has size 0 regardless of `N`. This is correct but can surprise when reasoning about memory layout.

5. **No runtime introspection.** `PhantomData` is a purely compile-time construct. At runtime there is no trace of the phantom type parameter -- you cannot query it or branch on it.

## Beginner mental model

Think of `PhantomData<T>` as a **label on an empty shelf**. The shelf holds nothing at runtime (zero bytes), but the label tells the compiler "this shelf is reserved for type `T`." The compiler then applies all the rules it would apply if `T` were actually sitting on the shelf -- ownership, borrowing, send/sync -- even though the shelf is physically empty.

## Example A -- Typestate pattern with PhantomData

```rust
use std::marker::PhantomData;

struct Locked;
struct Unlocked;

struct Door<State> {
    _state: PhantomData<State>,
}

impl Door<Locked> {
    fn unlock(self) -> Door<Unlocked> {
        println!("unlocking");
        Door { _state: PhantomData }
    }
}

impl Door<Unlocked> {
    fn open(&self) {
        println!("opening");
    }

    fn lock(self) -> Door<Locked> {
        println!("locking");
        Door { _state: PhantomData }
    }
}

fn main() {
    let door = Door::<Locked> { _state: PhantomData };
    // door.open();         // error: no method `open` for Door<Locked>
    let door = door.unlock();
    door.open();            // OK
}
```

## Example B -- Lifetime marker without a reference field

```rust
use std::marker::PhantomData;

struct Cursor<'a> {
    pos: usize,
    _lifetime: PhantomData<&'a [u8]>,
}

impl<'a> Cursor<'a> {
    fn new(_data: &'a [u8]) -> Self {
        Cursor { pos: 0, _lifetime: PhantomData }
    }
}

fn main() {
    let data = vec![1, 2, 3];
    let cursor = Cursor::new(&data);
    println!("cursor at {}", cursor.pos);
    // `cursor` cannot outlive `data` because PhantomData ties them
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Typestate with `PhantomData` makes protocol violations (e.g., opening a locked door) unrepresentable.
- [-> UC-18](../usecases/UC18-type-arithmetic.md) -- Phantom type parameters enable type-level tags and arithmetic without runtime cost.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- `PhantomData` allows generic structs to express constraints on type parameters they do not physically store.

## Source anchors

- `book/src/ch19-04-advanced-types.md`
- `rust-reference/src/special-types-and-traits.md` -- PhantomData
- `nomicon/src/phantom-data.md`
- `std::marker::PhantomData` documentation
