# Ownership and Move Semantics

## What it is

Every value in Rust has exactly one *owner* — the variable binding that is responsible for the value's memory. When that owner goes out of scope, Rust automatically calls `drop` to free the associated resources. There is no garbage collector; instead, ownership rules provide deterministic, compile-time memory management.

When you assign a value to another variable or pass it to a function, Rust *moves* ownership by default. The original binding becomes invalid and the compiler rejects any further use of it. This is fundamentally different from languages with garbage collection (Java, Python, Go), where multiple references can point to the same heap object simultaneously, and from C/C++, where copies happen implicitly and dangling pointers are a runtime hazard.

Move semantics apply to types that manage heap resources (`String`, `Vec<T>`, `Box<T>`, file handles, etc.). Types that are small and cheap to bitwise-copy — integers, floats, `bool`, `char`, and any type that implements the `Copy` trait — are *copied* instead of moved, so the original binding remains valid after assignment.

## What constraint it enforces

**A value cannot be used after ownership has been moved, and cleanup runs exactly once when the current owner goes out of scope.**

More specifically:

- **No use-after-move.** The compiler tracks ownership statically and rejects code that reads or writes a binding whose value has been moved away.
- **No double-free.** Because exactly one owner exists at any time, `drop` runs exactly once — there is no risk of freeing the same memory twice.
- **Deterministic destruction.** Resources are released at predictable points (scope exits), not at GC-chosen moments. This matters for file handles, locks, network connections, and any RAII-managed resource.
- **No dangling pointers.** The combination of ownership tracking and borrowing rules [→ T11](T11-borrowing-mutability.md) guarantees that every pointer/reference is valid for its entire lifetime.

## Minimal snippet

```rust
let s = String::from("hello");
let t = s;               // ownership moves from `s` to `t`
// println!("{}", s);     // error[E0382]: use of moved value `s`
println!("{}", t);        // OK — `t` is the owner now
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Borrowing** [→ T11](T11-borrowing-mutability.md) | Borrowing lets you *use* a value without taking ownership. `&T` and `&mut T` references are temporary loans that the compiler tracks alongside the owner. |
| **Lifetimes** [→ T48](T48-lifetimes.md) | Lifetimes annotate how long a borrow is valid. The owner must outlive every borrow of its value; lifetime annotations make this explicit in function signatures. |
| **Structs and Enums** [→ T01](T01-algebraic-data-types.md) | Each field of a struct or enum variant has its own ownership. Moving a non-`Copy` field out of a struct creates a *partial move* that invalidates the struct as a whole. |
| **Smart Pointers** [→ T24](T24-smart-pointers.md) | `Box<T>` gives heap ownership to a single owner. `Rc<T>` and `Arc<T>` introduce *shared* ownership via reference counting, relaxing the single-owner rule at a controlled cost. |
| **Send and Sync** [→ T50](T50-send-sync.md) | `Send` means ownership can be transferred to another thread. Whether a type is `Send` depends on its internal ownership structure. |

## Gotchas and limitations

1. **`Copy` types hide the ownership model.** Integers, `bool`, `char`, and other `Copy` types are silently duplicated on assignment. Beginners who only work with integers may not encounter move errors until they use `String` or `Vec`, which can be disorienting.

2. **Partial moves.** Moving a single non-`Copy` field out of a struct invalidates the struct as a whole, even though the remaining fields are still individually accessible. You cannot pass the struct to a function or use it as a unit anymore.

   ```rust
   struct Pair { a: String, b: String }
   let p = Pair { a: "x".into(), b: "y".into() };
   let grabbed = p.a;         // partial move of field `a`
   println!("{}", p.b);       // OK — non-moved fields are still individually accessible
   // println!("{:?}", p);    // error — struct as a whole is partially moved
   ```

3. **Closures capture by move.** When a closure uses the `move` keyword, it takes ownership of every captured variable. The original bindings become invalid outside the closure. This is especially important when spawning threads.

4. **`clone()` is explicit.** Unlike C++ copy constructors that fire implicitly, Rust requires you to call `.clone()` to duplicate a value. This makes the cost visible but means you must remember to clone when you need two independent copies.

5. **Cannot move out of a reference.** If you have `&T` or `&mut T`, you cannot move the inner value out — you only have a borrow. This leads to `error[E0507]`, which is common when working with iterators or match arms on borrowed data.

6. **Cannot move out of an index.** Moving an element out of a `Vec` or array by index would leave a hole in the collection. Use `.remove()`, `.swap_remove()`, `std::mem::take()`, or `std::mem::replace()` instead.

7. **Return values transfer ownership out.** Functions that return owned values move ownership to the caller. This is how builders and factory functions work — the caller receives a freshly owned value, and the function's local bindings are gone.

## Beginner mental model

Think of ownership as **holding a physical object**. You can hand it to someone else (move), but once you do, your hands are empty — you can't use it anymore. You can let someone *look at it* or *borrow it temporarily* (references, covered in [→ T11](T11-borrowing-mutability.md)), but you still own it and get it back. When the last person holding it leaves the room (scope ends), the object is cleaned up automatically.

The key insight: **Rust doesn't prevent you from sharing data — it prevents you from sharing data unsafely.** Ownership is the foundation that makes borrowing, lifetimes, and concurrency safety possible.

## Example A — Move on assignment

```rust
fn main() {
    let original = String::from("owned by original");
    let new_owner = original;   // value moves here

    // `original` is now invalid — the compiler knows it has no value
    // println!("{original}");  // error[E0382]: borrow of moved value: `original`

    println!("{new_owner}");    // OK: new_owner is the current owner
}   // `new_owner` is dropped here, freeing the String's heap memory
```

## Example B — Move into a function

```rust
fn take_ownership(s: String) {
    println!("I own: {s}");
}   // `s` is dropped here — the String is freed

fn main() {
    let greeting = String::from("hello");
    take_ownership(greeting);    // ownership moves into the function

    // `greeting` is now invalid
    // println!("{greeting}");   // error[E0382]: borrow of moved value: `greeting`
}
```

To keep using the value after the call, either pass a reference instead (`&greeting`) or `.clone()` the value before passing it.

## Example C — Copy vs Move

```rust
fn main() {
    // Integers implement Copy — assignment duplicates the bits
    let x = 42;
    let y = x;      // x is copied, not moved
    println!("x={x}, y={y}");   // both are valid ✓

    // Strings do NOT implement Copy — assignment moves
    let a = String::from("move me");
    let b = a;      // a is moved
    // println!("{a}");  // error[E0382]
    println!("{b}");     // OK ✓
}
```

A type implements `Copy` only if all of its fields are also `Copy` and it does not implement `Drop`. You can opt in by deriving `#[derive(Clone, Copy)]` on types that meet these criteria.

## Example D — Returning ownership

```rust
fn create_greeting(name: &str) -> String {
    // The String is created inside the function...
    let s = format!("Hello, {name}!");
    s   // ...and ownership is moved OUT to the caller via return
}

fn main() {
    let msg = create_greeting("Rust");  // caller now owns the String
    println!("{msg}");
}   // `msg` is dropped here
```

Returning a value is how Rust transfers ownership *out* of a function without requiring heap allocation tricks or output parameters.

## Example E — Partial moves from structs

```rust
struct User {
    name: String,
    email: String,
}

fn main() {
    let user = User {
        name: "Alice".into(),
        email: "alice@example.com".into(),
    };

    // Move just one field out
    let name = user.name;          // partial move
    println!("{}", user.email);    // OK — non-moved fields are still accessible individually
    // println!("{}", user.name);  // error[E0382] — this field was moved
    // drop(user);                 // error — struct as a whole cannot be used

    // If you need both: destructure to move all fields at once
    let user2 = User {
        name: "Bob".into(),
        email: "bob@example.com".into(),
    };
    let User { name, email } = user2;
    println!("name={name}, email={email}");
}
```

## Example F — `move` closures

```rust
use std::thread;

fn main() {
    let data = String::from("thread-owned");

    // `move` transfers ownership of `data` into the closure
    let handle = thread::spawn(move || {
        println!("thread says: {data}");
    });

    // `data` is no longer accessible here — it was moved into the closure
    // println!("{data}"); // error[E0382]

    handle.join().unwrap();
}
```

Without `move`, the closure would try to borrow `data`, but `thread::spawn` requires `'static` — the thread might outlive the current scope. Moving ownership into the closure satisfies this requirement.

## Common compiler errors and how to read them

### `error[E0382]: borrow of moved value`

The most common ownership error. You tried to use a variable after its value was moved somewhere else.

```
error[E0382]: borrow of moved value: `s`
 --> src/main.rs:4:20
  |
2 |     let s = String::from("hello");
  |         - move occurs because `s` has type `String`, which does not implement `Copy`
3 |     let t = s;
  |             - value moved here
4 |     println!("{}", s);
  |                    ^ value borrowed here after move
```

**How to fix:** Clone the value before the move (`let t = s.clone();`), pass a reference instead (`let t = &s;`), or restructure the code so you don't need the value after the move.

### `error[E0507]: cannot move out of borrowed content`

You tried to take ownership of a value through a reference. Since a reference is a loan, not an ownership transfer, you cannot move the value out.

```
error[E0507]: cannot move out of `*item` which is behind a shared reference
 --> src/main.rs:3:9
  |
3 |     let owned = *item;
  |         ^^^^^ move occurs because `*item` has type `String`,
  |               which does not implement `Copy`
```

**How to fix:** Clone the value (`let owned = item.clone();`), work with the reference directly, or if you have `&mut T`, use `std::mem::take()` or `std::mem::replace()` to swap the value out.

### `error[E0505]: cannot move out of 'x' because it is borrowed`

You tried to move a value while an outstanding borrow still exists.

```
error[E0505]: cannot move out of `data` because it is borrowed
 --> src/main.rs:4:14
  |
3 |     let r = &data;
  |             ----- borrow of `data` occurs here
4 |     let moved = data;
  |                 ^^^^ move out of `data` occurs here
5 |     println!("{r}");
  |               - borrow later used here
```

**How to fix:** Make sure the borrow is no longer used before the move, or clone the data so the borrow and the move operate on independent copies.

### `error[E0509]: cannot move out of type 'S', which implements the 'Drop' trait`

Moving a field out of a struct that implements `Drop` would leave the struct in a partially-valid state when `drop()` runs. Rust prevents this to avoid undefined behavior in the destructor.

**How to fix:** Clone the field, use `std::mem::take()` if the field type implements `Default`, or restructure to avoid partial moves from `Drop` types.

## Use-case cross-references

- [→ UC-02](../usecases/UC20-ownership-apis.md) — Designing APIs that encode ownership transfer and borrowing contracts in their signatures.
- [→ UC-05](../usecases/UC21-concurrency.md) — Thread-safety relies on ownership transfer (`Send`) to prevent data races.

## Source anchors

- `book/src/ch04-01-what-is-ownership.md`
- `book/src/ch04-02-references-and-borrowing.md` (for contrast with borrowing)
- `rust-by-example/src/scope/move.md`
- `rust-by-example/src/scope/move/partial_move.md`
