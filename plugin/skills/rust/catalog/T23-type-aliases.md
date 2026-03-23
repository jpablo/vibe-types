# Type Aliases

Since: Rust 1.0; trait-associated type aliases since Rust 1.0

## What it is

`type Alias = ConcreteType` creates a **transparent name** for an existing type. The alias and the original type are fully interchangeable -- the compiler treats them as identical. This reduces verbosity in complex signatures and improves readability, but it provides **no type safety**: values of the alias and the original type mix freely.

Common patterns include shortening `Result` types (`type Result<T> = std::result::Result<T, MyError>`) and naming complex generics (`type Callback = Box<dyn Fn(i32) -> bool + Send>`).

**Associated type aliases** in traits (`type Item;`) let each implementor fix a type parameter, reducing the number of generics callers must specify. This is a different mechanism from free-standing aliases -- associated types create a projection, not just a name.

Contrast with **newtypes** [-> catalog/T03](T03-newtypes-opaque.md) which create distinct types: `struct UserId(u64)` is **not** `u64`, whereas `type UserId = u64` **is** `u64`.

## What constraint it enforces

**Type aliases enforce no constraint -- they are purely ergonomic. The aliased type and the original type are interchangeable everywhere.**

- No compile-time distinction between alias and original type.
- No prevention of mixing: `fn greet(id: UserId)` where `type UserId = u64` accepts any `u64`.
- Associated type aliases in traits do enforce a constraint: each impl must specify exactly one concrete type for the associated type.

## Minimal snippet

```rust
type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

fn parse(s: &str) -> Result<i32> {
    Ok(s.parse()?)
}

fn main() {
    println!("{:?}", parse("42"));    // Ok(42)
    println!("{:?}", parse("bad"));   // Err(...)
}
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Newtypes** [-> catalog/T03](T03-newtypes-opaque.md) | Newtypes create distinct types; aliases do not. If you need the compiler to reject mixing, use a newtype. If you only need shorter names, use an alias. |
| **Traits / associated types** [-> catalog/T05](T05-type-classes.md) | `type Item = u32;` inside `impl Iterator for MyIter` fixes the associated type. This is the trait-level use of type aliases. |
| **Generics** [-> catalog/T04](T04-generics-bounds.md) | Type aliases can be generic: `type Pair<T> = (T, T)`. The alias is expanded at each use site. |
| **Callable typing** [-> catalog/T22](T22-callable-typing.md) | Complex callback types like `Box<dyn Fn(&str) -> Result<()> + Send>` benefit greatly from aliases. |

## Gotchas and limitations

1. **Aliases do not prevent mixing.** `type Meters = f64; type Seconds = f64;` lets you pass meters where seconds are expected. Use newtypes for safety.

2. **Aliases are not new types for trait impls.** You cannot `impl Display for MyAlias` if `MyAlias = Vec<i32>` -- the orphan rule sees through the alias to the underlying type.

3. **Generic aliases require all parameters.** `type Pair<T> = (T, T)` must be used as `Pair<i32>`, never as bare `Pair`. There are no default type parameters on free-standing aliases (though trait associated types support defaults on nightly).

4. **Associated type aliases vs generic parameters.** Beginners often confuse when to use an associated type vs a generic parameter on a trait. Rule of thumb: if each impl should fix exactly one type, use an associated type. If the trait should be generic over multiple types, use a generic parameter.

5. **`type` in `impl` blocks.** `type` inside an `impl` block is only for satisfying associated types of traits. You cannot define free-standing aliases inside `impl` blocks.

## Beginner mental model

Think of a type alias as a **nickname**. "Bob" and "Robert" refer to the same person -- they are interchangeable everywhere. A newtype, by contrast, is like giving someone a separate passport: even if the person is the same underneath, the system treats the two identities as distinct.

## Example A -- Simplifying complex callback signatures

```rust
type Handler = Box<dyn Fn(&str) -> Result<(), String> + Send>;

fn register(name: &str, handler: Handler) {
    match handler("test") {
        Ok(()) => println!("{name}: OK"),
        Err(e) => println!("{name}: {e}"),
    }
}

fn main() {
    let h: Handler = Box::new(|input| {
        if input.is_empty() { Err("empty".into()) } else { Ok(()) }
    });
    register("check", h);
}
```

## Example B -- Associated type alias in a trait

```rust
trait Storage {
    type Error;
    fn save(&self, data: &[u8]) -> Result<(), Self::Error>;
}

struct FileStore;

impl Storage for FileStore {
    type Error = std::io::Error;

    fn save(&self, data: &[u8]) -> Result<(), Self::Error> {
        println!("saving {} bytes", data.len());
        Ok(())
    }
}

fn main() {
    let store = FileStore;
    store.save(b"hello").unwrap();
}
```

## Use-case cross-references

- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Associated type aliases simplify generic APIs by fixing output types per implementation.

## Source anchors

- `book/src/ch19-04-advanced-types.md` -- "Creating Type Synonyms with Type Aliases"
- `rust-reference/src/items/type-aliases.md`
- `rust-by-example/src/types/alias.md`
