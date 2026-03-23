# Trait Solver and Parameter Environments

## What it is

The trait solver is the part of the Rust compiler responsible for proving whether trait obligations are satisfied. Every time your code requires a type to implement a trait — through a bound like `T: Clone`, a method call like `x.clone()`, an operator like `+`, or a `dyn Trait` coercion — the compiler generates a *trait obligation*. The solver must then find a proof that the obligation holds, or reject the program with a compile error. This process is entirely static: it happens at compile time, not at runtime.

The solver does not operate in a vacuum. At every point in the source code, there is a *parameter environment* (`ParamEnv`) — the set of assumptions the solver is allowed to use. The `ParamEnv` is built primarily from the `where` clauses and trait bounds written on the enclosing function, impl block, or trait definition. For example, inside `fn foo<T: Clone + Debug>(x: T)`, the solver knows it may assume `T: Clone` and `T: Debug`. It also includes *elaborated* bounds: if `T: Clone`, the solver automatically adds `T: Sized` (because `Clone: Sized` is a supertrait), without you writing it. Supertraits, implied bounds from well-formedness rules, and auto-trait assumptions all flow into the `ParamEnv`.

When the solver receives an obligation, it searches for a proof by examining impl candidates (concrete `impl Trait for Type` blocks, blanket impls, and built-in impls for auto traits), the assumptions in the `ParamEnv`, and projections of associated types. It uses *unification* to match type parameters against candidates and *backtracking* to try alternatives when one candidate fails. If no candidate satisfies the obligation, the solver reports an error. If multiple candidates could apply, the solver checks for overlap and coherence violations. The current stable solver has been refined over many years; a new chalk-inspired "next-gen" solver is under development to handle edge cases more uniformly. Understanding this machinery is what lets you read confusing trait errors and know exactly which bound to add or which constraint to restructure.

## What constraint it enforces

**A trait obligation is accepted only when the solver can construct a proof from the available impl candidates and the assumptions in the active `ParamEnv`.**

More specifically:

- **Obligations must be provable.** Every trait bound, method call, operator use, and coercion generates an obligation. The solver must find exactly one applicable impl or `ParamEnv` assumption for each.
- **The `ParamEnv` is local.** The solver can only use the bounds visible at the current item — function, impl, or trait. A bound written on one function is not available inside another function, even if both are in the same module.
- **Elaboration adds implied bounds.** Supertraits, `Sized` assumptions, and well-formedness requirements are automatically inserted into the `ParamEnv`, so the solver may use bounds you did not write explicitly.
- **Coherence must hold globally.** There must be at most one applicable impl for any concrete type-trait pair across the entire program. The solver enforces this through overlap checks and the orphan rule.
- **No negative reasoning by default.** The solver assumes a trait is *not* implemented unless it can prove otherwise. You cannot write "T does not implement Clone" as a bound (though negative impls exist internally for auto traits).

## Minimal snippet

```rust
trait Alias: Clone {}

fn promote<T: Alias>(value: T) -> T {
    // The ParamEnv contains {T: Alias, T: Clone, T: Sized}.
    // The solver proves the Clone obligation via elaboration of Alias.
    value.clone()
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Generics and Trait Bounds** [-> T04](T04-generics-bounds.md) | Every generic bound generates obligations that the trait solver must prove. The `ParamEnv` for a generic function is exactly the set of bounds declared on it. |
| **Trait Objects (`dyn Trait`)** [-> T05](T05-type-classes.md) | Building a `dyn Trait` requires the solver to prove the type implements the trait. Calling methods through `dyn Trait` uses vtable dispatch, but the solver still checks bounds at the coercion site. |
| **Associated Types** [-> T49](T49-associated-types.md) | Associated type projections (`<T as Iterator>::Item`) create additional obligations. The solver must normalize projections and may introduce bounds you did not write directly. |
| **Closures and `Fn` Traits** [-> T36](T36-trait-objects.md) | Closures implement `Fn`, `FnMut`, or `FnOnce`. The solver infers which trait a closure satisfies and proves obligations when closures are passed to generic functions. |
| **Send and Sync** [-> T50](T50-send-sync.md) | `Send` and `Sync` are auto traits. The solver checks them by inspecting struct fields recursively — no explicit impl is needed unless you use `unsafe impl`. |
| **Lifetime Bounds** [-> T48](T48-lifetimes.md) | The solver handles trait obligations and lifetime obligations together. A bound like `T: Iterator + 'a` creates both a trait obligation and a lifetime obligation in the same `ParamEnv`. |

## Gotchas and limitations

1. **Elaboration surfaces bounds you never wrote.** If you bound `T: Iterator`, the solver's `ParamEnv` also contains `T: Sized` (from the supertrait on `Iterator`). Error messages may mention these implicit bounds, which can be confusing when you cannot find them in your source code.

2. **Auto trait leakage.** The compiler infers `Send` and `Sync` from a struct's fields. A single `*const u8` field or an `Rc<T>` makes the entire struct `!Send`. This often surfaces as a surprising error far from the offending field, especially when returning `impl Future` from async functions.

   ```rust
   struct MyHandle {
       ptr: *const u8, // raw pointers are !Send
   }
   // MyHandle is automatically !Send — no error here,
   // but passing it to thread::spawn fails at the call site.
   ```

3. **Error messages may suggest incomplete fixes.** Trait resolution is order-independent, but the compiler's diagnostics pick one path to report. The suggested "add bound `T: Foo`" may not be the only or best fix — sometimes restructuring the code or adding a different bound is cleaner.

4. **Cyclic obligations cause overflow.** If trait bounds create a cycle — e.g., `T: Foo` requires `T: Bar` which requires `T: Foo` — the solver hits a recursion limit and reports "overflow evaluating the requirement." The fix is to break the cycle by restructuring bounds or adding explicit type annotations.

   ```rust
   // Contrived cycle: A: From<B> and B: From<A> can cause
   // overflow when the solver tries to prove one via the other.
   ```

5. **Associated type projection introduces hidden obligations.** Writing `T::Output: Debug` in a where clause generates an obligation to first normalize `T::Output`, which requires proving `T` implements the trait that defines `Output`. These transitive obligations can be surprising.

6. **`where` clauses on impls vs functions differ.** A bound on `impl<T: Clone> Foo for T` restricts which types get the impl. A bound on `fn bar<T: Clone>()` restricts which types callers may supply. The solver treats these differently — an impl bound narrows candidate selection, while a function bound enriches the `ParamEnv` inside the function body.

7. **The solver considers future impls for coherence.** The orphan rule and overlap checks are conservative: the solver rejects impls that *could* conflict with a future upstream impl, even if no conflict exists today. This is why `impl<T: Display> MyTrait for T` can conflict with a specific `impl MyTrait for SomeType` — the solver must assume upstream could add `impl Display for SomeType`.

8. **Negative reasoning is implicit.** The solver assumes a trait is not implemented unless proven otherwise. You cannot express `T: !Clone` as a user-facing bound. Specialization (unstable) partially relaxes this, but the stable solver has no opt-in negative bounds.

## Beginner mental model

Think of the trait solver as a **logic engine with a notebook**. The notebook is the `ParamEnv` — it contains every fact (bound) the compiler is allowed to assume at a given point. When your code does something that requires a trait (calling a method, using an operator, passing a value to a bounded function), the solver writes down an obligation and tries to prove it using the facts in the notebook plus the impls defined across the crate graph.

If the notebook says `T: Iterator` and `Iterator` requires `Sized`, the solver writes `T: Sized` into the notebook automatically — that is elaboration. If you call `.clone()` on `T` but the notebook does not contain `T: Clone` and no impl of `Clone` exists for the concrete type, the solver gives up and reports an error. Your job is to make sure the notebook has enough facts (bounds) for the solver to complete every proof your code requires. When you get a trait error, you are essentially seeing the solver say: "I could not prove this obligation with the facts I have."

## Example A — Supertrait elaboration

```rust
use std::fmt;

trait Summarize: fmt::Display {
    fn summary(&self) -> String;
}

fn print_summary<T: Summarize>(item: &T) {
    // The ParamEnv contains {T: Summarize, T: fmt::Display, T: Sized}.
    // We can call Display methods without an explicit Display bound.
    println!("Summary of {}: {}", item, item.summary());
}
```

The solver elaborates `T: Summarize` into `T: fmt::Display` because `Display` is a supertrait of `Summarize`. You never wrote `T: Display`, but the solver proves the `Display` obligation from elaboration.

## Example B — ParamEnv in action

```rust
fn largest<T: PartialOrd + Clone>(list: &[T]) -> T {
    // ParamEnv: {T: PartialOrd, T: Clone, T: Sized}
    let mut max = list[0].clone();  // Clone obligation proven from ParamEnv
    for item in &list[1..] {
        if *item > max {            // PartialOrd obligation proven from ParamEnv
            max = item.clone();
        }
    }
    max
}
```

Remove `Clone` from the bound and the solver cannot prove the `.clone()` obligation — you get `the trait bound T: Clone is not satisfied`. The `ParamEnv` is exactly and only what you declare.

## Example C — Obligation chain across traits

```rust
use std::fmt;

trait Encode: fmt::Display {
    fn encode(&self) -> Vec<u8> {
        self.to_string().into_bytes()
    }
}

fn log_and_encode<T: Encode>(val: &T) -> Vec<u8> {
    // Obligation chain: T: Encode -> T: Display -> T: Sized
    // All proven by elaboration from the single bound T: Encode.
    println!("Logging: {val}");
    val.encode()
}
```

A single bound can satisfy multiple obligations through the supertrait chain. The solver walks the chain automatically during elaboration.

## Example D — Overflow from cyclic bounds

```rust
trait A {
    type Out: B;
}

trait B {
    type Out: A;
}

// Attempting to use these traits together can produce:
// error[E0275]: overflow evaluating the requirement `<T as A>::Out: B`
//
// The solver tries: T: A -> T::Out: B -> <T::Out as B>::Out: A -> ...
// and hits the recursion limit.
```

Break the cycle by removing one of the cross-referencing supertrait bounds or by introducing a concrete type that terminates the chain.

## Example E — Auto trait leakage with raw pointers

```rust
use std::thread;

struct Wrapper {
    data: String,
    cache: *const u8, // raw pointer: !Send, !Sync
}

fn try_send(w: Wrapper) {
    // error[E0277]: `*const u8` cannot be sent between threads safely
    //   = help: within `Wrapper`, the trait `Send` is not implemented for `*const u8`
    thread::spawn(move || {
        println!("{}", w.data);
    });
}
```

The solver checks `Wrapper: Send` by inspecting every field. The `*const u8` is `!Send`, so `Wrapper` is automatically `!Send`. Fix by replacing the raw pointer with a `Send` type, wrapping it in a newtype with `unsafe impl Send`, or restructuring to avoid sending the wrapper across threads.

## Example F — Helping the solver with explicit bounds

```rust
use std::fmt;

fn debug_pair<A, B>(a: &A, b: &B)
where
    A: fmt::Debug,         // explicit bound satisfies the solver
    B: fmt::Debug + Clone, // two bounds, both added to ParamEnv
{
    let b_copy = b.clone();
    println!("{:?} and {:?}", a, b_copy);
}

// Without the bounds, the solver reports:
//   error[E0277]: `A` doesn't implement `Debug`
// The fix is always: add the bound the solver says is missing,
// or restructure so the obligation is not generated.
```

When the solver's error message says "the trait X is not implemented for Y," the most direct fix is to add `Y: X` to the nearest enclosing `where` clause. But sometimes the better fix is to avoid generating the obligation altogether — for example, by not calling the method that requires it.

## Common compiler errors and how to read them

### `error[E0277]: the trait bound 'T: Trait' is not satisfied`

The most common trait solver error. The solver generated an obligation but found no matching impl and no assumption in the `ParamEnv`.

```
error[E0277]: the trait bound `T: Clone` is not satisfied
 --> src/main.rs:4:15
  |
4 |     let y = x.clone();
  |               ^^^^^ the trait `Clone` is not implemented for `T`
  |
help: consider restricting type parameter `T`
  |
2 | fn foo<T: Clone>(x: T) {
  |         +++++++
```

**How to fix:** Add the missing bound to the function or impl header. If you cannot add the bound (e.g., in a trait definition), restructure to avoid the obligation.

### `error[E0275]: overflow evaluating the requirement`

The solver entered a cycle while trying to prove an obligation and hit the recursion limit.

```
error[E0275]: overflow evaluating the requirement `<T as MyTrait>::Assoc: SomeOtherTrait`
 --> src/main.rs:10:1
  |
  = help: consider adding a `#![recursion_limit="256"]` attribute to your crate
```

**How to fix:** Raising the recursion limit is a band-aid. The real fix is to break the cycle — simplify associated type chains, remove circular supertrait requirements, or add concrete type annotations so the solver can terminate.

### `error[E0119]: conflicting implementations of trait`

The solver found two impls that could apply to the same type. Coherence requires at most one impl per type-trait pair.

```
error[E0119]: conflicting implementations of trait `MyTrait` for type `Vec<_>`
 --> src/main.rs:8:1
  |
5 | impl<T> MyTrait for T { ... }
  | ------------------------ first implementation here
8 | impl MyTrait for Vec<i32> { ... }
  | ^^^^^^^^^^^^^^^^^^^^^^^^^ conflicting implementation
```

**How to fix:** Remove one of the impls, narrow the blanket impl with additional bounds so it no longer covers the concrete type, or use a newtype wrapper to differentiate the types.

### `error[E0277]: 'X' cannot be sent between threads safely`

An auto trait obligation (`Send` or `Sync`) failed because one or more fields are not `Send`/`Sync`.

```
error[E0277]: `Rc<String>` cannot be sent between threads safely
 --> src/main.rs:12:18
  |
12 |     thread::spawn(move || {
   |                   ^^^^^^^ `Rc<String>` cannot be sent between threads safely
   |
   = help: within `MyStruct`, the trait `Send` is not implemented for `Rc<String>`
```

**How to fix:** Replace `Rc` with `Arc`, remove the non-`Send` field, or restructure so the value is not sent across threads. If you are certain it is safe, use `unsafe impl Send` on a newtype wrapper — but only as a last resort.

## Use-case cross-references

- [-> UC-07](../usecases/UC23-diagnostics.md) — Strategies for reading and resolving complex trait solver error messages in real-world code.
- [-> UC-05](../usecases/UC21-concurrency.md) — Understanding how the solver proves `Send` and `Sync` obligations is key to diagnosing thread-safety errors.
- [-> UC-02](../usecases/UC20-ownership-apis.md) — API designs that rely on trait bounds are shaped by what the solver can prove from function-level `ParamEnv` assumptions.

## Source anchors

- `rust/src/doc/reference/src/trait-bounds.md`
- `rust/src/doc/reference/src/type-system.md`
- `rust/src/doc/rustc-dev-guide/src/typing-parameter-envs.md`
- `rust/src/doc/rustc-dev-guide/src/solve/trait-solving.md`
- `rust/src/doc/rustc-dev-guide/src/traits/resolution.md`
- `rust/src/doc/book/src/ch10-02-traits.md`
