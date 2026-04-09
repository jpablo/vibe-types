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

## 6. When to Use It

- Streaming paginated API responses without loading all pages into memory
- Processing file chunks, large logs, or binary streams
- Event-based data flows (WebSockets, SSE, Node.js streams)
- Pipeline transformations where backpressure matters
- Wrapping async cursors (Redis, databases) as typed iterables

```typescript
// File streaming: memory-efficient processing of large files
async function* readChunks(path: string): AsyncGenerator<Buffer, void, unknown> {
  const fs = await import('fs/promises');
  const f = await fs.open(path, 'r');
  const buf = Buffer.alloc(8192);
  let bytesRead = 0;
  while (true) {
    const result = await f.read(buf, 0, buf.length, null);
    bytesRead = result.bytesRead;
    if (bytesRead === 0) break;
    yield buf.subarray(0, bytesRead);
  }
  await f.close();
}
```

## 7. When Not to Use It

- Small, known-size collections (just use arrays)
- When you need random access to elements
- When early termination is impossible and full iteration is required anyway
- When the consumer needs all data upfront (e.g., sorting the entire result)

```typescript
// Don't: tiny static list
async function* badStatic(): AsyncGenerator<number> {
  const arr = [1, 2, 3];
  for (const x of arr) yield x; // overkill; just return arr
}

// Do: return array directly
function staticList(): number[] {
  return [1, 2, 3];
}
```

## 8. Antipatterns When Using It

### Blocking until full collection

```typescript
// Bad: defeats streaming, loads everything into memory
async function processBad(source: AsyncIterable<string>): Promise<void> {
  const all = await collect(source); // all at once
  for (const item of all) {
    await process(item); // too late; memory already used
  }
}

// Good: process as you receive
async function processGood(source: AsyncIterable<string>): Promise<void> {
  for await (const item of source) {
    await process(item); // one at a time
  }
}
```

### Reusing a generator

```typescript
// Bad: generators are single-use
async function* oneTime(): AsyncGenerator<number> {
  yield 1;
  yield 2;
}

const gen = oneTime();
for await (const x of gen) console.log(x); // 1, 2
for await (const x of gen) console.log(x); // nothing already consumed

// Good: re-run the generator function
for await (const x of oneTime()) console.log(x); // 1, 2
for await (const x of oneTime()) console.log(x); // 1, 2
```

### Ignoring cleanup

```typescript
// Bad: resource leak
async function* leaky(): AsyncGenerator<string, void, unknown> {
  const conn = await connect();
  try {
    while (true) {
      const msg = await conn.read();
      if (!msg) break;
      yield msg;
    }
  } finally {
    // never called if consumer breaks early
  }
}

// Good: proper cleanup
async function* safe(): AsyncGenerator<string, void, unknown> {
  const conn = await connect();
  try {
    while (true) {
      const msg = await conn.read();
      if (!msg) break;
      yield msg;
    }
  } finally {
    await conn.close(); // always called on break or return
  }
}
```

## 9. Antipatterns with Other Techniques

### Nested async loops (callback-like pattern)

```typescript
// Bad: nested callbacks, no streaming
async function processPagesBad(): Promise<void> {
  let cursor: string | null = null;
  do {
    const { items, next } = await fetchPage(cursor);
    cursor = next;
    for (const item of items) {
      await process(item); // blocks until page done
    }
  } while (cursor);
}

// Good: async generator abstracts pagination
async function* pageStream(): AsyncGenerator<Item> {
  let cursor: string | null = null;
  do {
    const { items, next } = await fetchPage(cursor);
    cursor = next;
    for (const item of items) yield item;
  } while (cursor);
}

async function processPagesGood(): Promise<void> {
  for await (const item of pageStream()) {
    await process(item); // true streaming
  }
}
```

### Recursive async without yielding

```typescript
// Bad: stack grows, no backpressure
async function traverseBad(node: Node): Promise<void> {
  await process(node);
  for (const child of node.children) {
    await traverseBad(child); // deep stack on large trees
  }
}

// Good: async generator enables controlled traversal
async function* traverseStream(root: Node): AsyncGenerator<Node> {
  const stack = [root];
  while (stack.length) {
    const node = stack.pop()!;
    yield node;
    for (const child of node.children) stack.push(child);
  }
}

async function traverseGood(root: Node): Promise<void> {
  for await (const node of traverseStream(root)) {
    await process(node); // backpressure possible with .return()
  }
}
```

### Promise.all over large async iterables

```typescript
// Bad: O(n) memory, no streaming
async function transformBad(source: AsyncIterable<number>): Promise<number[]> {
  const arr = await collect(source);
  return arr.map(n => transformSync(n)); // load all, then map
}

// Good: stream transformations
async function* transformStream(source: AsyncIterable<number>): AsyncGenerator<number> {
  for await (const n of source) {
    yield transformSync(n); // one at a time
  }
}
```
