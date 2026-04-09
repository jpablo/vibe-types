# Async Concurrency Safety

## The Constraint

Callers cannot forget to `await` an async result or silently ignore async errors. An `async` function's return type is explicit in the type signature; the resolved value type is tracked through `Promise<T>` generics; unhandled error paths are a type error, not a runtime surprise.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Effect tracking** | `Promise<T>` encodes an async effect; `Task<A>` and `TaskEither<E, A>` from fp-ts make the error channel typed and explicit | [-> T12](../catalog/T12-effect-tracking.md) |
| **Callable types** | `async function f(): Promise<T>` is a typed callable contract — the return type is part of the function's interface | [-> T22](../catalog/T22-callable-typing.md) |
| **`infer` / `Awaited<T>`** | Extract the resolved type of a `Promise` without repeating the annotation; compose with `ReturnType<>` | [-> T49](../catalog/T49-associated-types.md) |
| **Null safety** | `Promise<User \| null>` forces callers to handle the absent case after awaiting — optionality is tracked through the async boundary | [-> T13](../catalog/T13-null-safety.md) |
| **fp-ts Task / TaskEither** | Composable typed async with an explicit, typed error channel; integrates with `pipe` and `chain` | [-> T54](../catalog/T54-functor-applicative-monad.md) |
| **Concurrency combinators** | `Promise.all`, `Promise.allSettled`, `Promise.race`, `Promise.any` — each has a distinct typed signature that reflects its failure semantics | [-> T12](../catalog/T12-effect-tracking.md) |
| **Async iterables** | `AsyncGenerator<T, R, N>` and `AsyncIterable<T>` type streaming sequences; `for await...of` consumes them with full type inference | [-> T64](../catalog/T64-async-iteration.md) |

## Patterns

### Pattern A — `Promise<T>` explicit return type

Annotating the return type of an `async` function makes the resolved type explicit. Callers who use the result without `await` get the `Promise<T>` object — the compiler catches the mistake when they try to use a `Promise`-shaped value as if it were `T`.

```typescript
type User = { id: string; name: string; email: string };

// Explicit return type — callers know the resolved shape before reading the body:
async function fetchUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<User>;
}

async function main() {
  const user = await fetchUser("u1");
  console.log(user.name); // OK — User after await

  // Forgetting await: compiler catches misuse of the Promise object:
  const promise = fetchUser("u2");
  console.log(promise.name); // error: Property 'name' does not exist on type 'Promise<User>'

  // Promise<T | null> forces null handling after await:
  async function findUser(id: string): Promise<User | null> {
    const res = await fetch(`/api/users/${id}`);
    if (res.status === 404) return null;
    return res.json();
  }

  const found = await findUser("u3");
  console.log(found.name);          // error: Object is possibly 'null'
  console.log(found?.name ?? "—");  // OK — optional chaining + nullish coalescing
}
```

### Pattern B — `Awaited<ReturnType<typeof fn>>` for derived types

`Awaited<T>` recursively unwraps nested `Promise<Promise<T>>` to `T`. Combined with `ReturnType<>`, it derives the resolved value type of any async function without duplicating the annotation — changes to the function's return type propagate automatically.

```typescript
async function fetchUserProfile(id: string): Promise<{
  id:          string;
  displayName: string;
  avatarUrl:   string | null;
  joinedAt:    Date;
}> {
  const res = await fetch(`/api/profiles/${id}`);
  return res.json();
}

// Derive the resolved type — no manual duplication:
type UserProfile = Awaited<ReturnType<typeof fetchUserProfile>>;
// { id: string; displayName: string; avatarUrl: string | null; joinedAt: Date }

// Use in wrapper, cache, or test helpers:
function cacheProfile(id: string, profile: UserProfile): void {
  console.log(`Cached ${profile.displayName} (${id})`);
}

// Awaited unwraps multiple layers:
type Nested = Awaited<Promise<Promise<Promise<number>>>>;
// number — fully unwrapped

// Works with any async function — including third-party ones:
declare function externalFetch(): Promise<{ data: string; ts: number }>;
type ExternalResult = Awaited<ReturnType<typeof externalFetch>>;
// { data: string; ts: number }

async function processExternal() {
  const result: ExternalResult = await externalFetch(); // type checked
  console.log(result.data.toUpperCase()); // OK
}
```

### Pattern C — fp-ts `TaskEither<E, A>` for typed error channels

`TaskEither<E, A>` is a lazy async computation that returns `Either<E, A>`. Multiple steps compose with `pipe` and `TE.chain` — errors short-circuit the pipeline and accumulate into a typed union without nested `try/catch` blocks.

```typescript
import { pipe }  from "fp-ts/function";
import * as TE   from "fp-ts/TaskEither";
import * as E    from "fp-ts/Either";

type NetworkError = { tag: "NetworkError"; status: number };
type ParseError   = { tag: "ParseError";   message: string };
type NotFound     = { tag: "NotFound";     id: string };
type AppError     = NetworkError | ParseError | NotFound;

type User    = { id: string; name: string; teamId: string };
type Team    = { id: string; name: string };
type Profile = { user: User; team: Team };

function fetchUser(id: string): TE.TaskEither<NetworkError | NotFound, User> {
  return TE.tryCatch(
    async () => {
      const res = await fetch(`/api/users/${id}`);
      if (res.status === 404) throw { tag: "NotFound" as const, id };
      if (!res.ok) throw { tag: "NetworkError" as const, status: res.status };
      return res.json() as User;
    },
    (e) => e as NetworkError | NotFound,
  );
}

function fetchTeam(id: string): TE.TaskEither<NetworkError, Team> {
  return TE.tryCatch(
    async () => {
      const res = await fetch(`/api/teams/${id}`);
      if (!res.ok) throw { tag: "NetworkError" as const, status: res.status };
      return res.json() as Team;
    },
    (e) => e as NetworkError,
  );
}

// Compose: fetch user → fetch team → build profile
// Error channel: NetworkError | NotFound — union grows automatically per step
const buildProfile = (userId: string): TE.TaskEither<AppError, Profile> =>
  pipe(
    fetchUser(userId),
    TE.chain((user) =>
      pipe(
        fetchTeam(user.teamId),
        TE.map((team) => ({ user, team })),
      ),
    ),
  );

// Run and handle both branches:
async function main() {
  const result = await buildProfile("u1")();

  if (E.isRight(result)) {
    const { user, team } = result.right; // Profile — fully typed
    console.log(`${user.name} is on team ${team.name}`);
  } else {
    const error = result.left; // AppError — exhaustively typed
    switch (error.tag) {
      case "NetworkError": console.error(`HTTP ${error.status}`); break;
      case "ParseError":   console.error(`Parse: ${error.message}`); break;
      case "NotFound":     console.error(`User not found: ${error.id}`); break;
    }
  }
}
```

### Pattern D — Cancellation via typed `AbortSignal` parameter

Passing `AbortSignal` as a typed parameter makes cancellation an explicit part of the function's contract. Callers who need cancellable operations are guided by the type; tools like timeouts and request deduplication compose cleanly.

```typescript
type ApiResponse<T> = { data: T; cached: boolean };

// AbortSignal in the signature: cancellation is part of the contract
async function fetchWithTimeout<T>(
  url:     string,
  signal:  AbortSignal,
  options?: RequestInit,
): Promise<ApiResponse<T>> {
  const res = await fetch(url, { ...options, signal });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  const data: T = await res.json();
  return { data, cached: res.headers.get("x-cache") === "HIT" };
}

// Compose AbortSignal with timeout:
async function fetchUserWithTimeout(id: string): Promise<ApiResponse<User>> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new Error("Request timed out")), 5000);

  try {
    return await fetchWithTimeout<User>(`/api/users/${id}`, controller.signal);
  } finally {
    clearTimeout(timer);
  }
}

// Passing a non-AbortSignal value is a compile error:
async function bad() {
  const result = await fetchWithTimeout<User>("/api/users/1", "cancel"); // error
  // error: Argument of type 'string' is not assignable to parameter of type 'AbortSignal'
}

// Parallel with shared cancellation:
async function fetchAll(ids: string[], signal: AbortSignal): Promise<User[]> {
  const tasks = ids.map((id) =>
    fetchWithTimeout<User>(`/api/users/${id}`, signal),
  );
  return Promise.all(tasks).then((results) => results.map((r) => r.data));
}
```

### Pattern E — Parse, don't validate — async parsers return typed results

An async function that parses external data should return `Promise<Result<T, E>>` instead of throwing. The caller handles the error at the type level — there is no invisible `try/catch` and no `any`-typed `catch (e)`.

```typescript
import { z } from "zod";

const UserSchema = z.object({
  id:    z.string().uuid(),
  name:  z.string().min(1),
  email: z.string().email(),
});

type User        = z.infer<typeof UserSchema>;
type ParseError  = { tag: "ParseError";  issues: z.ZodIssue[] };
type NetworkError = { tag: "NetworkError"; status: number };
type FetchError  = ParseError | NetworkError;

type Result<T, E> = { ok: true; value: T } | { ok: false; error: E };

// Returns a typed Result — no throwing, no any-typed catch:
async function fetchAndParseUser(id: string): Promise<Result<User, FetchError>> {
  let res: Response;
  try {
    res = await fetch(`/api/users/${id}`);
  } catch {
    return { ok: false, error: { tag: "NetworkError", status: 0 } };
  }

  if (!res.ok) {
    return { ok: false, error: { tag: "NetworkError", status: res.status } };
  }

  const raw: unknown = await res.json();
  const parsed = UserSchema.safeParse(raw);

  if (!parsed.success) {
    return { ok: false, error: { tag: "ParseError", issues: parsed.error.issues } };
  }

  return { ok: true, value: parsed.data };
}

// Caller is forced to handle both paths at the type level:
async function main() {
  const result = await fetchAndParseUser("u1");

  if (result.ok) {
    const user = result.value; // User — fully typed
    console.log(`Hello, ${user.name}`);
  } else {
    const err = result.error; // FetchError — exhaustive
    if (err.tag === "ParseError") {
      console.error("Invalid response shape:", err.issues.map(i => i.message));
    } else {
      console.error(`Network failure: HTTP ${err.status}`);
    }
  }

  // Trying to use value without checking is a compile error:
  result.value; // error: Property 'value' does not exist on type '{ ok: false; error: FetchError }'
}
```

### Pattern F — Typed concurrency combinators

TypeScript infers a distinct return type for each `Promise` combinator, reflecting its different failure semantics. The differences are load-bearing: switching from `Promise.all` to `Promise.allSettled` changes both the runtime behaviour and the shape callers must handle.

```typescript
type User  = { id: string; name: string };
type Order = { id: string; total: number };
type Tag   = string;

declare function fetchUser(id: string):   Promise<User>;
declare function fetchOrders(id: string): Promise<Order[]>;
declare function fetchTags(id: string):   Promise<Tag[]>;

// --- Promise.all ---
// Resolves when ALL succeed; rejects on the first failure.
// TypeScript infers a tuple — each position keeps its own type:
async function loadDashboard(userId: string) {
  const [user, orders, tags] = await Promise.all([
    fetchUser(userId),
    fetchOrders(userId),
    fetchTags(userId),
  ]);
  // user: User, orders: Order[], tags: Tag[]  — no overlap, no union
  return { user, orders, tags };
}

// --- Promise.allSettled ---
// Never rejects; resolves with a PromiseSettledResult<T> for every input.
// Callers must inspect .status to access the value — partial failures are typed.
async function loadBestEffort(userId: string) {
  const results = await Promise.allSettled([
    fetchUser(userId),
    fetchOrders(userId),
  ]);
  // results: [PromiseSettledResult<User>, PromiseSettledResult<Order[]>]

  const [userResult, ordersResult] = results;

  const user =
    userResult.status === "fulfilled"
      ? userResult.value      // User
      : null;                 // userResult.reason: unknown

  const orders =
    ordersResult.status === "fulfilled"
      ? ordersResult.value    // Order[]
      : [];
}

// --- Promise.race ---
// Settles with the first promise to resolve OR reject.
// Return type is the union of all input types:
async function withTimeout<T>(
  promise: Promise<T>,
  ms: number,
): Promise<T> {
  const timeout = new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error(`Timed out after ${ms}ms`)), ms),
  );
  return Promise.race([promise, timeout]);
  // Promise<T> — never contributes to the value type, only to rejection
}

// --- Promise.any ---
// Resolves with the first fulfillment; rejects with AggregateError only if ALL reject.
// Return type is the union of all input value types:
async function firstAvailable(userId: string): Promise<User | Order[]> {
  return Promise.any([fetchUser(userId), fetchOrders(userId)]);
  // Promise<User | Order[]> — whichever resolves first
}

// --- Sequential vs parallel: a common type-safe pitfall ---
// These two snippets are type-identical but have very different performance:

// SEQUENTIAL — each await blocks before starting the next:
async function sequential(userId: string) {
  const user   = await fetchUser(userId);   // starts, waits
  const orders = await fetchOrders(userId); // starts after user resolves
  return { user, orders };
}

// PARALLEL — both start immediately; total time ≈ max(t_user, t_orders):
async function parallel(userId: string) {
  const [user, orders] = await Promise.all([
    fetchUser(userId),
    fetchOrders(userId),
  ]);
  return { user, orders };
}
// TypeScript cannot warn about the sequential case — it is a semantic choice,
// not a type error. The discipline is yours; the types are the same either way.
```

### Pattern G — Typed async generators and `AsyncIterable<T>`

`async function*` returns `AsyncGenerator<T, R, N>`. The first type parameter is the yielded element type — `for await...of` iterates with full inference. Async iterables are the right model for paginated APIs, streaming reads, or any sequence that arrives over time.

```typescript
type Page<T> = { items: T[]; nextCursor: string | null };
type Post    = { id: string; title: string; body: string };

// Async generator: yields Post, returns void, receives nothing via next()
async function* paginatePosts(
  endpoint: string,
  signal:   AbortSignal,
): AsyncGenerator<Post, void, undefined> {
  let cursor: string | null = null;

  do {
    const url = cursor ? `${endpoint}?cursor=${cursor}` : endpoint;
    const res = await fetch(url, { signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const page: Page<Post> = await res.json();
    yield* page.items;          // yields each Post individually
    cursor = page.nextCursor;
  } while (cursor !== null);
}

// Consumer — item is inferred as Post:
async function printAllPosts(signal: AbortSignal) {
  for await (const post of paginatePosts("/api/posts", signal)) {
    console.log(`[${post.id}] ${post.title}`);
  }
}

// Typed transformation utilities work with any AsyncIterable<T>:
async function* take<T>(
  source: AsyncIterable<T>,
  n:      number,
): AsyncGenerator<T, void, undefined> {
  let count = 0;
  for await (const item of source) {
    if (count++ >= n) break;
    yield item;
  }
}

async function* map<T, U>(
  source:    AsyncIterable<T>,
  transform: (item: T) => U | Promise<U>,
): AsyncGenerator<U, void, undefined> {
  for await (const item of source) {
    yield await transform(item);
  }
}

// Compose: take the first 5 posts, map to their titles:
async function firstFiveTitles(signal: AbortSignal): Promise<string[]> {
  const titles: string[] = [];
  const posts = take(paginatePosts("/api/posts", signal), 5);
  for await (const title of map(posts, (p) => p.title)) {
    titles.push(title); // title: string — inferred through the chain
  }
  return titles;
}

// Functions that accept any async sequence use AsyncIterable<T>:
async function collect<T>(source: AsyncIterable<T>): Promise<T[]> {
  const items: T[] = [];
  for await (const item of source) items.push(item);
  return items;
}
// Works with paginatePosts, ReadableStream, or any other AsyncIterable<T>.
```

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Async return contract | `async function fetchUser(id)` — resolved type is `any`; callers learn the shape by convention or docs | `async function fetchUser(id: string): Promise<User>` — resolved type is checked at every call site |
| Forgot to await | `promise.name` silently reads `undefined` on the Promise object | `promise.name` — compile error: property does not exist on `Promise<User>` |
| Error handling | `try/catch (e)` — `e` is `any`; error shape is undocumented and unchecked | `Promise<Result<T, E>>` or `TaskEither<E, A>` — error type is explicit and exhaustively checkable |
| Derived async types | Manually write out the resolved type wherever needed — drifts when the function changes | `Awaited<ReturnType<typeof fn>>` — single source of truth; updates automatically |
| Cancellation | Pass a flag or callback by convention; no type enforcement | `signal: AbortSignal` parameter — callers who omit it get a compile error |
| Concurrency combinators | `Promise.all`, `Promise.allSettled` etc. return untyped arrays; callers must cast | Each combinator has a precise generic signature; tuple positions, settled statuses, and union types are all inferred |
| Streaming sequences | Async generators yield `any`; consumers have no contract on the element type | `AsyncGenerator<T, R, N>` / `AsyncIterable<T>` — element type, return type, and `next()` argument are all checked |

## When to Use Which Feature

**`Promise<T>` with explicit return types** (Pattern A) is the right default. It is built into the language, costs nothing at runtime, and gives callers and linters full visibility into the resolved shape. Always annotate return types on `async` functions — do not let them widen to `Promise<any>`.

**`Awaited<ReturnType<typeof fn>>`** (Pattern B) eliminates type duplication in wrappers, caches, test helpers, and HOF utilities. Use it any time you derive a type from an existing async function rather than repeating the annotation.

**fp-ts `TaskEither<E, A>`** (Pattern C) pays off when you chain three or more async operations each of which can fail with a specific typed error. The `pipe` + `TE.chain` pattern eliminates nested `try/catch` blocks and keeps the error union growing automatically. Adopt it only if the team is comfortable with functional style and the codebase already uses fp-ts.

**`AbortSignal` parameters** (Pattern D) make cancellation an explicit, typed contract. Add them to any long-running or user-cancellable operation — HTTP calls, streaming reads, polling loops. Compose controllers with `AbortSignal.any()` (TypeScript 5.3+) for multi-source cancellation.

**Parse, don't validate async parsers** (Pattern E) apply at any async boundary that ingests external data — API responses, webhook payloads, file reads. Combining Zod (or io-ts) with a typed `Result` return ensures that the error path is always handled at the call site, not silently swallowed.

**Typed concurrency combinators** (Pattern F) are the right choice whenever you fan out to multiple async operations. Prefer `Promise.all` when all operations must succeed; switch to `Promise.allSettled` when partial failure is acceptable and callers need to inspect each result individually. Use `Promise.race` for timeouts and `Promise.any` for first-wins scenarios. Note that TypeScript cannot detect sequential `await` chains that should be parallelised — that discipline rests with the author.

**Async generators and `AsyncIterable<T>`** (Pattern G) model any sequence that arrives over time: paginated APIs, file streams, WebSocket messages, server-sent events. Write transformation utilities (`take`, `map`, `filter`) against `AsyncIterable<T>` so they compose with any source. Pass `AbortSignal` into generators for cooperative cancellation — the generator checks the signal on each iteration boundary.

## When to Use

| Scenario | Technique |
|---|---|
| Single async operation with known output shape | `Promise<T>` with explicit return type |
| Deriving resolved type from an existing async function | `Awaited<ReturnType<typeof fn>>` |
| Chaining 3+ async ops with distinct typed errors | `TaskEither<E, A>` with `pipe` |
| Long-running or user-cancellable operations | `AbortSignal` parameter |
| Parsing external data (APIs, webhooks, files) | `Promise<Result<T, E>>` return (parse, don't validate) |
| Fanning out independent async ops | `Promise.all` (all-or-nothing) or `Promise.allSettled` (best-effort) |
| Timeout behavior | `Promise.race` with a rejection promise |
| First-success behavior with fallbacks | `Promise.any` with multiple sources |
| Paginated/streaming sequences | `AsyncGenerator<T, R, N>` and `AsyncIterable<T>` |

### Concrete thresholds

- **3+ async steps with distinct error types** → `TaskEither` (nested `try/catch` becomes verbose and untyped).
- **2+ independent async ops** → `Promise.all` (sequential `await` adds linear latency).
- **Pagination or streaming** → async generators (no need to buffer full response in memory).
- **Human-facing timeouts** → `AbortSignal` + `Promise.race` (graceful cancellation vs silent error).

## When NOT to Use

| Technique | Avoid when |
|---|---|
| `TaskEither<E, A>` | Single async step; team unfamiliar with fp-ts; no need for error chaining |
| `Promise.allSettled` | All operations must succeed (prefer `Promise.all` for clarity and brevity) |
| `Promise.any` | All sources share the same failure mode (no redundancy benefit) |
| Async generators | Small, known-size datasets (array return is simpler and more composable) |
| `AbortSignal` parameter | Sync helper functions or trivial ops (< 10ms, no user impact) |
| `Result<T, E>` return | Internal functions where throwing is caught and logged at a known boundary |

### Concrete counterexamples

```typescript
// NOT TaskEither: single step is fine with native Promise
async function getUserId(id: string): Promise<string> {
  const r = await fetch(`/api/users/${id}`);
  return r.json();
}

// NOT allSettled: all-or-nothing is clearer
async function loadProfile(userId: string) {
  const [user, orders] = await Promise.all([
    fetchUser(userId),
    fetchOrders(userId),
  ]);
  return { user, orders };
}

// NOT async generator: array is simpler for known sizes
async function fetchTop3Posts(): Promise<Post[]> {
  const r = await fetch("/api/posts?limit=3");
  return r.json();
}
```

## Antipatterns When Using This Technique

### A1 — Sequential `await` instead of parallel `Promise.all`

```typescript
// Antipattern: linear latency, type-safe but slow
async function getUserData(userId: string) {
  const user   = await fetchUser(userId);
  const orders = await fetchOrders(userId);
  const tags   = await fetchTags(userId);
  return { user, orders, tags };
}

// Fix: parallel execution
async function getUserData(userId: string) {
  const [user, orders, tags] = await Promise.all([
    fetchUser(userId),
    fetchOrders(userId),
    fetchTags(userId),
  ]);
  return { user, orders, tags };
}
// Latency: max(t_user, t_orders, t_tags) vs sum of all
```

### A2 — `Promise.all` when partial failure is acceptable

```typescript
// Antipattern: one failure cancels all results
async function loadDashboard(userId: string) {
  const [user, widgetA, widgetB] = await Promise.all([
    fetchUser(userId),
    fetchWidgetA(),
    fetchWidgetB(),
  ]);
  // If widgetA fails, user and widgetB are lost
}

// Fix: allSettled for best-effort loading
async function loadDashboard(userId: string) {
  const [userR, widgetAR, widgetBR] = await Promise.allSettled([
    fetchUser(userId),
    fetchWidgetA(),
    fetchWidgetB(),
  ]);

  return {
    user:    userR.status === "fulfilled"    ? userR.value    : null,
    widgetA: widgetAR.status === "fulfilled" ? widgetAR.value : null,
    widgetB: widgetBR.status === "fulfilled" ? widgetBR.value : null,
  };
}
```

### A3 — Throwing inside `TaskEither` without proper error mapping

```typescript
// Antipattern: error type is `unknown`, breaks exhaustiveness
function fetchUser(id: string): TE.TaskEither<NetworkError, User> {
  return TE.tryCatch(
    async () => {
      const res = await fetch(`/api/users/${id}`);
      if (!res.ok) throw new Error("Failed"); // Error, not NetworkError
      return res.json();
    },
    (e) => e as NetworkError, // unsafe cast
  );
}

// Fix: throw typed error or map in fallback
function fetchUser(id: string): TE.TaskEither<NetworkError, User> {
  return TE.tryCatch(
    async () => {
      const res = await fetch(`/api/users/${id}`);
      if (!res.ok) throw { tag: "NetworkError", status: res.status };
      return res.json();
    },
    () => ({ tag: "NetworkError", status: 0 }) as const,
  );
}
```

### A4 — Memory leak with uncanceled `AbortSignal`

```typescript
// Antipattern: signal created but never aborted
async function search(query: string): Promise<SearchResult[]> {
  const controller = new AbortController();
  const res = await fetch(`/api/search?q=${query}`, { signal: controller.signal });
  // No way to cancel; controller forgotten -> leak if operation interrupted
  return res.json();
}

// Fix: wire cancellation to user action or timeout
async function search(query: string): Promise<SearchResult[]> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const res = await fetch(`/api/search?q=${query}`, { signal: controller.signal });
    return res.json();
  } finally {
    clearTimeout(timeout);
  }
}
```

### A5 — Nested async generators without `yield*`

```typescript
// Antipattern: yields arrays instead of individual items
async function* badGenerator(): AsyncGenerator<Page<Post>, void> {
  const page1 = await fetchPage(1);
  const page2 = await fetchPage(2);
  yield page1.items; // yields an array
  yield page2.items; // yields an array
}

// Fix: use yield* to flatten
async function* goodGenerator(): AsyncGenerator<Post, void> {
  const page1 = await fetchPage(1);
  const page2 = await fetchPage(2);
  yield* page1.items; // yields each Post
  yield* page2.items; // yields each Post
}
```

## Antipatterns With Other Techniques (Where This Technique Helps)

### B1 — Callback pyramids (pre-async/await)

```typescript
// Callback hell: error-prone, no type tracking
getUser(id, (err, user) => {
  if (err) return handleError(err);
  getOrders(user.id, (err, orders) => {
    if (err) return handleError(err);
    getTags(user.id, (err, tags) => {
      if (err) return handleError(err);
      render({ user, orders, tags });
    });
  });
});

// Async/await with Promise.all: flat, typed, parallel
async function loadData(id: string) {
  const user = await fetchUser(id);
  const [orders, tags] = await Promise.all([
    fetchOrders(user.id),
    fetchTags(user.id),
  ]);
  render({ user, orders, tags });
}
```

### B2 — Silent `catch` with `any` error type

```typescript
// Silent catch: error type is `any`, loss of information
async function fetchUser(id: string): Promise<User> {
  try {
    const res = await fetch(`/api/users/${id}`);
    return res.json();
  } catch (e) {
    console.error(e); // e is any, no structure
    throw new Error("Failed"); // loses original error details
  }
}

// Typed Result return: error handled at type level
async function fetchUser(id: string): Promise<Result<User, FetchError>> {
  const res = await fetch(`/api/users/${id}`);
  if (!res.ok) return { ok: false, error: { tag: "NetworkError", status: res.status } };
  const data = await res.json();
  return { ok: true, value: data };
}

// Caller forced to handle both branches
async function main() {
  const r = await fetchUser("u1");
  if (r.ok) console.log(r.value.name);
  else console.error(r.error.tag, r.error.status);
}
```

### B3 — Manual polling without cancellation

```typescript
// Polling with hardcoded sleep: can't cancel, memory leak
async function pollForCompletion(jobId: string): Promise<JobResult> {
  let attempts = 0;
  while (attempts < 50) {
    await new Promise(r => setTimeout(r, 1000));
    const res = await fetch(`/api/jobs/${jobId}`);
    const job = await res.json();
    if (job.status === "complete") return job.result;
    attempts++;
  }
  throw new Error("Job timed out");
}

// Polling with AbortSignal: cancellable, clean shutdown
async function pollForCompletion(
  jobId:  string,
  signal: AbortSignal,
): Promise<JobResult> {
  const interval = 1000;
  while (true) {
    signal.throwIfAborted(); // check cancellation
    await new Promise(r => setTimeout(r, interval));
    const res = await fetch(`/api/jobs/${jobId}`, { signal });
    const job = await res.json();
    if (job.status === "complete") return job.result;
    if (job.status === "failed") throw new Error("Job failed");
  }
}

// Caller cancels on timeout
async function runJob(id: string) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30000);
  try {
    return await pollForCompletion(id, controller.signal);
  } finally {
    clearTimeout(timer);
  }
}
```

### B4 — Event emission without backpressure

```typescript
// Event emitter: unbounded buffer, no flow control
class EventEmitterProcessor {
  on(event: string, cb: (data: any) => void) { /* ... */ }
  process(data: Item[]) {
    data.forEach(item => {
      this.on('item', (item) => this.handle(item)); // fires synchronously
    });
  }
}

// Async generator: natural backpressure via iteration
async function* processItems(items: Item[]): AsyncGenerator<Item, void> {
  for (const item of items) {
    yield item; // consumer controls pace
  }
}

async function consume() {
  for await (const item of processItems(largeBatch)) {
    await processSlowly(item); // consumer pace determines throughput
  }
}
```
