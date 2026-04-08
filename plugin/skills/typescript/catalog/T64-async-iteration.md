# Async Iteration

> **Since:** TypeScript 2.3 (`AsyncIterator`); `for await...of` since TypeScript 2.3 / ES2018

## 1. What It Is

TypeScript has first-class type support for the JavaScript async iteration protocol. An **`AsyncIterable<T>`** is any object with a `[Symbol.asyncIterator]()` method that returns an `AsyncIterator<T>`. An **`AsyncGenerator<T, TReturn, TNext>`** is a function prefixed with `async function*` that `yield`s values of type `T`, optionally returns a value of type `TReturn`, and optionally accepts injected values of type `TNext` via `yield`. The `for await...of` loop consumes any `AsyncIterable<T>` and infers `T` for the loop variable; the compiler rejects `for await...of` on non-async iterables in strict mode. The utility type `Awaited<T>` unwraps a `Promise<T>` to `T` and is used internally to type the resolved values of async generators.

Async generators are the standard TypeScript idiom for typed streaming: paginated API responses, file-chunk readers, event streams, SSE feeds, and database cursor wrappers all map naturally to `AsyncGenerator` or `AsyncIterable`.

## 2. What Constraint It Lets You Express

**Streaming sequences carry their element type through every consumer; misusing the iterator protocol (e.g., calling `.next()` with the wrong injection type) is a compile error.**

- `for await...of stream` infers the loop variable as `T` from `AsyncIterable<T>` — no manual casting.
- `yield` in an `async function*` is typed: yielding a value of the wrong type is a compile error.
- `TNext` on `AsyncGenerator<T, TReturn, TNext>` types the value sent back via `(yield expr)` — useful for bidirectional coroutines.
- Passing an `AsyncIterable<string>` where `AsyncIterable<number>` is expected is a type error, even though both are async iterables.

## 3. Minimal Snippet

```typescript
// Async generator: streams paginated results as an AsyncIterable<Item>
interface Item { id: number; name: string }

async function* fetchPages(url: string): AsyncGenerator<Item, void, unknown> {
  let cursor: string | null = null;
  do {
    const params = cursor ? `?cursor=${cursor}` : "";
    const res = await fetch(`${url}${params}`);
    const { items, next }: { items: Item[]; next: string | null } = await res.json();
    for (const item of items) yield item;   // type: Item
    cursor = next;
  } while (cursor !== null);
}

// Consumer: for-await-of infers item as Item
async function printAll(url: string): Promise<void> {
  for await (const item of fetchPages(url)) {
    console.log(item.id, item.name); // OK — item is Item
  }
}

// Utility: collect an AsyncIterable into an array
async function collect<T>(source: AsyncIterable<T>): Promise<T[]> {
  const result: T[] = [];
  for await (const value of source) result.push(value);
  return result;
}
```

## 4. Interaction with Other Features

- **`Promise<T>` / effect tracking** ([T12](T12-effect-tracking.md)): each element yield from an async generator is implicitly wrapped in a `Promise`; the generator pauses at every `await` or `yield`.
- **Generics & bounds** ([T04](T04-generics-bounds.md)): `collect<T>(source: AsyncIterable<T>)` is the standard pattern — constrain the element type at the call site.
- **`Awaited<T>`** ([T49](T49-associated-types.md)): useful when extracting the element type of an `AsyncGenerator` with `ReturnType` and `Awaited`.

## 5. Gotchas

| Gotcha | What happens | Fix |
|---|---|---|
| Missing `lib` entry | `AsyncIterable`, `Symbol.asyncIterator` unavailable | Add `"ES2018"` or later to `lib` in `tsconfig.json` |
| `for await...of` on sync iterable | Compiler error under `--downlevelIteration` or strict targets | Use `for...of` for sync; `for await...of` only for async iterables |
| Unhandled rejection inside generator | Unhandled promise rejection; generator silently exits | Wrap `await` expressions in `try/catch` inside the generator body |
| Generator not consumed | No items fetched (lazy) | Always consume the generator; or wrap in a utility like `collect` |
