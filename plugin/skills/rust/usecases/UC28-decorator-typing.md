# Decorator Pattern (via Closures and Fn Traits)

## The constraint

Wrap existing behavior with additional logic (logging, timing, retry) using higher-order functions and closures. Rust has no built-in decorator syntax, but the `Fn` trait hierarchy enables the same pattern: a function that takes a callable and returns a callable with augmented behavior.

## Feature toolkit

- `[-> T22](../catalog/T22-callable-typing.md)`
- `[-> T04](../catalog/T04-generics-bounds.md)`
- `[-> T36](../catalog/T36-trait-objects.md)`

## Patterns

- Pattern A: simple wrapper returning a closure.
```rust
fn with_logging<F, R>(name: &str, f: F) -> R
where
    F: FnOnce() -> R,
{
    println!("[start] {name}");
    let result = f();
    println!("[end]   {name}");
    result
}

let value = with_logging("compute", || 2 + 2);
```

- Pattern B: returning a closure that wraps the original function.
```rust
fn logged<F>(f: F) -> impl Fn(i32) -> i32
where
    F: Fn(i32) -> i32,
{
    move |x| {
        println!("input: {x}");
        let result = f(x);
        println!("output: {result}");
        result
    }
}

let add_one = logged(|x| x + 1);
assert_eq!(add_one(5), 6);
```

- Pattern C: middleware pattern with trait objects.
```rust
type Handler = Box<dyn Fn(&str) -> String>;

fn with_auth(next: Handler) -> Handler {
    Box::new(move |request| {
        if request.contains("token=valid") {
            next(request)
        } else {
            "401 Unauthorized".to_string()
        }
    })
}

fn with_logging(next: Handler) -> Handler {
    Box::new(move |request| {
        println!(">> {request}");
        let response = next(request);
        println!("<< {response}");
        response
    })
}

// Compose middleware (innermost applied first):
let handler: Handler = Box::new(|req| format!("OK: {req}"));
let stack = with_logging(with_auth(handler));
```

- Pattern D: generic decorator preserving arbitrary signatures.
```rust
fn timed<F, R>(f: F) -> impl FnOnce() -> (R, std::time::Duration)
where
    F: FnOnce() -> R,
{
    move || {
        let start = std::time::Instant::now();
        let result = f();
        (result, start.elapsed())
    }
}

let (value, elapsed) = timed(|| {
    std::thread::sleep(std::time::Duration::from_millis(10));
    42
})();
```

## Tradeoffs

- Closure-based decorators are composable and zero-cost (static dispatch) but each composition creates a unique unnameable type.
- `Box<dyn Fn>` enables runtime composition and storage but adds heap allocation and dynamic dispatch.
- Rust lacks syntactic sugar for decoration — the wrapping must be explicit at the call site or in a builder.

## When to use which feature

- Use generic closures (`impl Fn`) for performance-critical, statically known wrapper chains.
- Use `Box<dyn Fn>` when middleware must be composed dynamically (plugin systems, configurable pipelines).
- Use the newtype wrapper pattern (a struct implementing a trait) when decorators need to carry state or implement additional traits.

## Source anchors

- `book/src/ch13-01-closures.md`
- `book/src/ch20-05-advanced-functions-and-closures.md`
- `rust-by-example/src/fn/closures.md`
- `rust-by-example/src/fn/closures/output_parameters.md`
