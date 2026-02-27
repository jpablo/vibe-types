# Borrowing and Mutability Rules

## What it is

Rust's ownership system [→ catalog/01] guarantees that every value has a single owner, but programs constantly need to *read* or *modify* data without taking ownership of it. **Borrowing** solves this: you create a *reference* to a value, which lets you use it while the original owner retains responsibility for cleanup.

There are two kinds of references. A **shared reference** `&T` gives read-only access to a value, and any number of them can coexist at the same time. An **exclusive (mutable) reference** `&mut T` gives read-write access, but the compiler enforces that it is the *only* reference to that value for the duration of the borrow. The fundamental invariant is: **many readers OR one writer, never both at once.** This is checked entirely at compile time, with zero runtime cost.

This is a sharp departure from other languages. C and C++ let you create as many pointers as you like, mutable or not, and the programmer must manually ensure they do not conflict — data races and aliased-mutation bugs are common results. Java and C# give you object references that are always shared and always mutable; thread-safety is achieved through runtime synchronization (locks, `synchronized` blocks), not compile-time proof. Rust's borrow checker eliminates entire categories of bugs — iterator invalidation, data races, dangling pointers — before the program ever runs.

Modern Rust uses **Non-Lexical Lifetimes (NLL)**: a borrow is considered active from the point it is created to the point of its *last use*, not to the end of its lexical scope. This means you can create a shared reference, use it, and then create a mutable reference later in the same block, as long as the shared reference is never used after that point.

A related concept is **reborrowing**: when you have `&mut T`, you can create a shorter-lived `&T` or `&mut T` from it without moving the original reference. The compiler implicitly reborrows in many contexts (e.g., passing `&mut T` to a function that takes `&mut T`), which is why mutable references feel less restrictive in practice than the "only one" rule might suggest.

## What constraint it enforces

**At any given point in the program, a value may be accessed through many `&T` references or through exactly one `&mut T` reference, but never both simultaneously; and no reference may outlive the data it points to.**

More specifically:

- **No aliased mutation.** If a mutable reference exists, no other reference — shared or mutable — to the same data may be live at the same time. This prevents data races at compile time.
- **No mutation through shared references.** A `&T` does not permit modifying the underlying value (barring interior mutability via `Cell`, `RefCell`, `Mutex`, etc.).
- **References must be valid.** A reference cannot outlive the value it borrows. The compiler uses lifetime analysis [→ catalog/03] to enforce this.
- **Owner is frozen during borrows.** While a shared borrow is live, the owner cannot mutate or move the value. While a mutable borrow is live, the owner cannot read, mutate, or move the value through any other path.

## Minimal snippet

```rust
let mut x = 5;
let r = &x;           // shared borrow — read OK
println!("{r}");       // last use of `r`; borrow ends here (NLL)
let m = &mut x;        // mutable borrow — allowed because `r` is no longer used
*m += 1;
println!("{x}");       // prints 6
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Ownership** [→ catalog/01] | Borrowing is the complement of ownership: instead of transferring a value, you loan access to it. The owner must outlive every borrow. |
| **Lifetimes** [→ catalog/03] | Lifetime annotations describe *how long* a borrow is valid. The borrow checker uses them to ensure no reference outlives its referent. |
| **Structs and Enums** [→ catalog/04] | You can borrow individual fields of a struct independently. The compiler tracks disjoint field borrows within a single function body. |
| **Traits and Generics** [→ catalog/05] | Trait methods declare whether they need `&self`, `&mut self`, or `self`. Generic bounds like `T: AsRef<U>` abstract over borrowing. |
| **Interior Mutability** [→ catalog/09] | `Cell<T>`, `RefCell<T>`, `Mutex<T>`, and `RwLock<T>` allow mutation behind `&T` by deferring the borrow check to runtime or using atomic operations. |
| **Smart Pointers** [→ catalog/10] | `Box<T>` implements `Deref`/`DerefMut`, so `&Box<T>` auto-dereferences to `&T`. `Rc<T>` only provides `&T` (shared ownership = shared access). |

## Gotchas and limitations

1. **NLL subtleties: borrows extend to last use, not end of block.** Before NLL, borrows lasted until the closing `}`, which forced artificial scoping blocks. With NLL, the borrow ends at its last use — but "last use" can be non-obvious when control flow is involved (e.g., a reference used inside an `if` branch still extends through that branch).

2. **Mutable references are exclusive *even to the owner*.** While `&mut x` is live, you cannot read `x` directly — the mutable reference has *exclusive* access. This surprises beginners who expect the original variable to remain readable.

   ```rust
   let mut v = vec![1, 2, 3];
   let r = &mut v;
   // println!("{}", v.len()); // error: cannot borrow `v` as immutable
   r.push(4);                  // must go through the mutable reference
   ```

3. **Cannot borrow through `&T` to call `&mut self` methods.** If you only hold a shared reference to a value, you cannot call any methods that require `&mut self`, even if you "know" it would be safe. This often appears with `HashMap::get` vs `HashMap::insert` in the same scope.

4. **Reborrowing vs moving a mutable reference.** Passing `&mut T` to a function that accepts `&mut T` *reborrows* (the original reference is temporarily suspended but usable afterwards). However, moving a mutable reference into a closure or storing it in a struct transfers ownership of the reference itself — the original binding becomes invalid.

5. **Iterating and mutating simultaneously.** Calling `.iter()` borrows the collection immutably, so you cannot modify the collection inside the loop. Even `.iter_mut()` forbids structural changes (push, remove). This is Rust enforcing iterator invalidation safety at compile time.

   ```rust
   let mut items = vec![1, 2, 3];
   for item in &items {
       // items.push(*item); // error[E0502]: cannot borrow `items` as mutable
   }
   ```

6. **Disjoint field borrows work inside a function, but not across function calls.** The compiler can see that `&mut s.a` and `&mut s.b` do not overlap when both borrows are in the same function. But if you call a method `s.borrow_a()` that returns `&mut s.a`, the compiler sees the signature `&mut self`, which borrows all of `s`, blocking access to `s.b`.

7. **Temporary values and reference scope.** Creating a reference to a temporary (`&String::from("hi")`) extends the temporary's lifetime to match the reference in simple `let` bindings, but this does not work in all contexts (e.g., inside a `match` arm or as a function argument).

8. **Implicit reborrowing hides complexity.** The compiler inserts reborrows automatically in many places, which makes code ergonomic but can confuse beginners who wonder why `&mut T` sometimes "moves" and sometimes does not.

## Beginner mental model

Think of borrowing as a **library lending system**. The owner of a book (the variable) can lend it out for reading: many people can hold a photocopy (shared reference `&T`) and read it simultaneously. But if someone needs to *edit* the book (mutable reference `&mut T`), the library recalls all copies first — only the editor may hold the book, and nobody else can read or edit it until the editor returns it. Once the editor is done (the mutable reference is no longer used), the book goes back on the shelf and new readers can check it out again.

The key insight is that **the borrow checker does not prevent you from writing flexible code — it prevents you from writing code where two parts of the program disagree about who can modify data.** Once you internalize the rhythm of "create reference, use it, let it end, then do something else," most borrow-checker errors disappear. NLL makes this natural: you do not need explicit blocks to end borrows, because the compiler tracks actual usage points.

## Example A — Basic shared references

Multiple shared references can coexist, and they all provide read-only access to the same underlying value. The owner retains ownership throughout.

```rust
fn print_len(s: &String) {
    println!("length = {}", s.len());
}

fn main() {
    let greeting = String::from("hello, world");
    let r1 = &greeting;
    let r2 = &greeting;           // multiple shared borrows are fine
    println!("{r1} and {r2}");
    print_len(&greeting);          // another shared borrow via function call
    println!("{greeting}");        // owner is still valid
}
```

## Example B — Mutable references and exclusivity

An `&mut T` reference gives exclusive read-write access. While it exists, no other reference — and not even the owner — may access the value.

```rust
fn push_greeting(v: &mut Vec<String>, name: &str) {
    v.push(format!("Hello, {name}!"));
}

fn main() {
    let mut names = vec!["Alice".to_string()];
    let r = &mut names;
    r.push("Bob".to_string());
    push_greeting(r, "Carol");     // reborrow of `r` — OK
    // println!("{}", names.len()); // error: `names` is mutably borrowed
    println!("{r:?}");             // last use of `r`
    println!("{}", names.len());   // OK — mutable borrow has ended
}
```

## Example C — NLL in action: reusing after last use

Before NLL, the shared borrow of `data` would have lasted until the end of the block, making the mutable borrow illegal. With NLL, the borrow ends at its last use (`println!`), so the subsequent mutable borrow succeeds.

```rust
fn main() {
    let mut data = vec![1, 2, 3];

    let first = &data[0];
    println!("first element: {first}");  // last use of `first`

    // NLL recognizes `first` is dead here — mutable borrow is allowed
    data.push(4);
    println!("{data:?}");                // [1, 2, 3, 4]
}
```

## Example D — Reborrowing

When you pass a mutable reference to a function, the compiler *reborrows* it: the callee gets a fresh `&mut T` derived from yours, and your reference is temporarily suspended. After the call returns, your original reference is usable again.

```rust
fn increment(val: &mut i32) {
    *val += 1;
}

fn main() {
    let mut count = 0;
    let r = &mut count;

    increment(r);   // implicit reborrow: `r` is suspended, not moved
    increment(r);   // `r` is active again — we can reuse it
    *r += 10;

    println!("{count}"); // prints 12
}
```

If `increment` took ownership of the reference (e.g., via a generic or closure), the second call would fail because the reference was moved, not reborrowed.

## Example E — Iterating and mutating (the pitfall and the fix)

A common beginner mistake is trying to modify a collection while iterating over it. Rust prevents this at compile time.

```rust
fn main() {
    let mut scores = vec![10, 20, 30];

    // WRONG: iterator borrows `scores` immutably, push borrows mutably
    // for s in &scores {
    //     if *s > 15 {
    //         scores.push(*s * 2); // error[E0502]
    //     }
    // }

    // FIX 1: collect changes first, apply after
    let extras: Vec<i32> = scores.iter()
        .filter(|&&s| s > 15)
        .map(|&s| s * 2)
        .collect();
    scores.extend(extras);

    // FIX 2: use indices so there is no live borrow on the Vec
    let len = scores.len();
    for i in 0..len {
        scores[i] += 1;  // indexing borrows and releases immediately
    }

    println!("{scores:?}");
}
```

## Example F — Disjoint field borrows

Within a single function, the compiler can track that borrows of different struct fields do not overlap. This lets you hold `&mut` references to two fields simultaneously.

```rust
struct Player {
    health: i32,
    name: String,
}

fn main() {
    let mut p = Player { health: 100, name: "Ferris".into() };

    let h = &mut p.health;
    let n = &mut p.name;       // OK: disjoint fields
    *h -= 10;
    n.push_str(" the Crab");
    println!("{}: {} HP", p.name, p.health);
}

// However, if you call a method with `&mut self`, the compiler borrows
// the *entire* struct, blocking access to other fields:
impl Player {
    fn take_damage(&mut self, amount: i32) {
        self.health -= amount;
    }
}

fn demo() {
    let mut p = Player { health: 100, name: "Ferris".into() };
    // let n = &mut p.name;
    // p.take_damage(5);       // error: cannot borrow `p` as mutable more than once
    // println!("{n}");
    // FIX: avoid holding a field borrow across a method call on the same struct
    p.take_damage(5);
    let n = &mut p.name;
    n.push_str("!");
    println!("{}: {} HP", p.name, p.health);
}
```

## Common compiler errors and how to read them

### `error[E0502]: cannot borrow 'x' as mutable because it is also borrowed as immutable`

This is the most frequent borrowing error. A shared reference is still live when you try to create a mutable reference to the same data.

```
error[E0502]: cannot borrow `data` as mutable because it is also borrowed as immutable
 --> src/main.rs:5:5
  |
3 |     let r = &data;
  |             ----- immutable borrow occurs here
4 |     data.push(4);
  |     ^^^^^^^^^^^^ mutable borrow occurs here
5 |     println!("{r}");
  |               - immutable borrow later used here
```

**How to fix:** Move the use of the shared reference (`r`) before the mutable operation, so NLL ends the immutable borrow earlier. Alternatively, clone the data you need from the shared reference so it becomes independent.

### `error[E0499]: cannot borrow 'x' as mutable more than once at a time`

Two mutable references to the same data are alive at the same time.

```
error[E0499]: cannot borrow `v` as mutable more than once at a time
 --> src/main.rs:4:14
  |
3 |     let r1 = &mut v;
  |              ------ first mutable borrow occurs here
4 |     let r2 = &mut v;
  |              ^^^^^^ second mutable borrow occurs here
5 |     r1.push(1);
  |     -- first borrow later used here
```

**How to fix:** Ensure the first mutable borrow is no longer used before creating the second. If you need to mutate two parts of a structure, use disjoint field borrows or split the data into separate variables.

### `error[E0506]: cannot assign to 'x' because it is borrowed`

You tried to write to a variable directly while a reference to it still exists.

```
error[E0506]: cannot assign to `count` because it is borrowed
 --> src/main.rs:4:5
  |
3 |     let r = &count;
  |             ------ `count` is borrowed here
4 |     count = 10;
  |     ^^^^^^^^^^ `count` is assigned to here but it was already borrowed
5 |     println!("{r}");
  |               - borrow later used here
```

**How to fix:** Finish using the reference before reassigning the variable, or restructure the code so the assignment and the borrow do not overlap.

### `error[E0596]: cannot borrow 'x' as mutable, as it is not declared as mutable`

You tried to create `&mut x` but `x` was declared with `let` instead of `let mut`.

```
error[E0596]: cannot borrow `data` as mutable, as it is not declared as mutable
 --> src/main.rs:3:5
  |
2 |     let data = vec![1, 2, 3];
  |         ---- help: consider changing this to be mutable: `mut data`
3 |     data.push(4);
  |     ^^^^^^^^^^^^ cannot borrow as mutable
```

**How to fix:** Add `mut` to the variable declaration: `let mut data = vec![1, 2, 3];`. If the value comes from a function parameter, change the parameter to `mut` or take `&mut T`.

## Use-case cross-references

- [→ UC-02](../usecases/02-ownership-safe-apis.md) — Designing APIs that express borrowing contracts (`&self` vs `&mut self`) in their signatures, guiding callers toward safe usage patterns.
- [→ UC-05](../usecases/05-compile-time-concurrency-constraints.md) — The aliasing rule (`&T` xor `&mut T`) is the foundation for Rust's data-race freedom: `&T` is `Sync` (safe to share across threads), while `&mut T` requires exclusive access.
- [→ UC-03](../usecases/03-state-machine-types.md) — State machines often borrow the underlying resource in each state, using lifetimes to tie the borrow to the state's duration.

## Source anchors

- `book/src/ch04-02-references-and-borrowing.md`
- `book/src/ch15-05-interior-mutability.md` (for `RefCell` and interior mutability contrast)
- `rust-by-example/src/scope/borrow.md`
- `rust-by-example/src/scope/borrow/mut.md`
- `reference/src/expressions/operator-expr.md` (dereference and borrow operators)
- `edition-guide/src/rust-2021/disjoint-capture-in-closures.md`
