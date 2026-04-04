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
  const result = await fetchWithTimeout<User>("/api/users/1", "cancel" as any); // error
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

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Async return contract | `async function fetchUser(id)` — resolved type is `any`; callers learn the shape by convention or docs | `async function fetchUser(id: string): Promise<User>` — resolved type is checked at every call site |
| Forgot to await | `promise.name` silently reads `undefined` on the Promise object | `promise.name` — compile error: property does not exist on `Promise<User>` |
| Error handling | `try/catch (e)` — `e` is `any`; error shape is undocumented and unchecked | `Promise<Result<T, E>>` or `TaskEither<E, A>` — error type is explicit and exhaustively checkable |
| Derived async types | Manually write out the resolved type wherever needed — drifts when the function changes | `Awaited<ReturnType<typeof fn>>` — single source of truth; updates automatically |
| Cancellation | Pass a flag or callback by convention; no type enforcement | `signal: AbortSignal` parameter — callers who omit it get a compile error |

## When to Use Which Feature

**`Promise<T>` with explicit return types** (Pattern A) is the right default. It is built into the language, costs nothing at runtime, and gives callers and linters full visibility into the resolved shape. Always annotate return types on `async` functions — do not let them widen to `Promise<any>`.

**`Awaited<ReturnType<typeof fn>>`** (Pattern B) eliminates type duplication in wrappers, caches, test helpers, and HOF utilities. Use it any time you derive a type from an existing async function rather than repeating the annotation.

**fp-ts `TaskEither<E, A>`** (Pattern C) pays off when you chain three or more async operations each of which can fail with a specific typed error. The `pipe` + `TE.chain` pattern eliminates nested `try/catch` blocks and keeps the error union growing automatically. Adopt it only if the team is comfortable with functional style and the codebase already uses fp-ts.

**`AbortSignal` parameters** (Pattern D) make cancellation an explicit, typed contract. Add them to any long-running or user-cancellable operation — HTTP calls, streaming reads, polling loops. Compose controllers with `AbortSignal.any()` (TypeScript 5.3+) for multi-source cancellation.

**Parse, don't validate async parsers** (Pattern E) apply at any async boundary that ingests external data — API responses, webhook payloads, file reads. Combining Zod (or io-ts) with a typed `Result` return ensures that the error path is always handled at the call site, not silently swallowed.
