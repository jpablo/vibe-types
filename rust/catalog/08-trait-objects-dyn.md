# Trait Objects and dyn

## What it is

`dyn Trait` enables runtime polymorphism via vtables when object safety rules are met.

## What constraint it enforces

**Only object-safe trait methods are callable through trait objects.**

## Minimal snippet

```rust
trait Draw {
    fn draw(&self);
}

fn paint(x: &dyn Draw) {
    x.draw();
}
```

## Interaction with other features

- Alternative to static dispatch in `[-> catalog/05]` and `[-> catalog/06]`.
- Used for extensibility in `[-> UC-04]`.

## Gotchas and limitations

- Trait objects require object safety; many generic or `Self`-typed methods are not object-safe.
- Dynamic dispatch adds vtable indirection and may reduce optimization opportunities.

### Beginner mental model

Trait objects (`dyn Trait`) are like pointing to a behavior slot instead of a concrete type. The compiler stores the actual method pointers (vtable) so you can pass any compatible type through the same reference.

### Example A

```rust
trait Draw {
    fn draw(&self);
}

struct Circle;

impl Draw for Circle {
    fn draw(&self) {
        println!("circle");
    }
}

fn render(item: &dyn Draw) {
    item.draw();
}
```

### Example B

```rust
// Continuing from Example A.
let shapes: Vec<&dyn Draw> = vec![&Circle];
for shape in shapes {
    shape.draw();
}
```

### Common compiler errors and how to read them

- `error[E0038]: the trait `Draw` cannot be made into an object` means the trait has non-object-safe methods (e.g., returning `Self` or having generic type params); remove those features or keep the usage generic.
- `error[E0718]: `dyn` trait must be object safe` appears when a trait method requires `Self` in the signature or contains `where Self: Sized`; stick to object-safe signatures (`&self`, `&mut self`, `fn foo(&self) -> u32`).

## Use-case cross-references

- `[-> UC-04]`

## Source anchors

- `book/src/ch18-02-trait-objects.md`
- `rust-by-example/src/trait/dyn.md`
