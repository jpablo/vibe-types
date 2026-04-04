# Effect Tracking

> **Since:** TypeScript 1.0 (Promise); fp-ts for full effect types

## 1. What It Is

TypeScript has no native effect system. The language tracks one effect natively: **asynchrony**, via the `Promise<T>` return type and `async`/`await` syntax. Any function that performs I/O asynchronously must declare `Promise<T>` as its return type; the compiler enforces that callers `await` or chain the result. For richer effect tracking — side effects, error effects, environment dependencies, non-determinism — the community uses libraries such as **fp-ts** (which provides `IO<A>`, `Task<A>`, `TaskEither<E, A>`, `ReaderTaskEither<R, E, A>`) and **Effect** (the `Effect<A, E, R>` type). These encode effectful computations as values in the return type, making the effects visible to callers and composable via monadic chaining. The `Result<T, E>` / `Either<E, A>` pattern (also from fp-ts or hand-rolled) is the minimal form of error effect tracking.

## 2. What Constraint It Lets You Express

**Effectful computations are encoded in return types so callers cannot ignore the effect; the compiler enforces that `Promise` values are awaited and that `IO`/`Task`/`Either` values are explicitly run or composed.**

- `async function fetchUser(): Promise<User>` cannot be called as if it returns `User`; forgetting `await` yields `Promise<User>`, which is incompatible with `User`.
- `type Task<A> = () => Promise<A>` defers execution; the type communicates that the computation is lazy and asynchronous.
- `TaskEither<E, A>` signals both asynchrony and the possibility of a typed error, forcing callers to handle both.

## 3. Minimal Snippet

```typescript
// Native effect tracking: async/await with Promise<T>
async function fetchUser(id: string): Promise<{ name: string }> {
  const response = await fetch(`/users/${id}`);
  return response.json();
}

// Caller must await — ignoring the Promise gives Promise<{name:string}>, not {name:string}
const user = await fetchUser("42"); // OK
// const user2: { name: string } = fetchUser("42"); // error — Promise<...> not assignable to {name:string}

// Minimal hand-rolled Result type for error effects
type Result<T, E> =
  | { ok: true;  value: T }
  | { ok: false; error: E };

async function parseUser(raw: string): Promise<Result<{ name: string }, string>> {
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed.name !== "string") return { ok: false, error: "missing name" };
    return { ok: true, value: parsed };
  } catch {
    return { ok: false, error: "invalid JSON" };
  }
}

// fp-ts style: IO<A> — synchronous side-effectful computation as a value
type IO<A> = () => A;

const readLine: IO<string> = () => "input from console"; // deferred execution
const result: string = readLine(); // explicitly run

// fp-ts TaskEither pattern (abbreviated without library import)
type Task<A> = () => Promise<A>;
type Either<E, A> = { _tag: "Left"; left: E } | { _tag: "Right"; right: A };
type TaskEither<E, A> = Task<Either<E, A>>;

function fetchOrError(url: string): TaskEither<string, Response> {
  return async () => {
    try {
      const r = await fetch(url);
      return { _tag: "Right", right: r };
    } catch (e) {
      return { _tag: "Left", left: String(e) };
    }
  };
}
```

## Recommended Libraries

| Library | Role | Link |
|---|---|---|
| fp-ts | Full functional effect stack: `IO`, `Task`, `Either`, `TaskEither`, `ReaderTaskEither` | https://gcanti.github.io/fp-ts/ |
| Effect | Modern `Effect<A, E, R>` type with structured concurrency, dependency injection, and streaming | https://effect.website |
| neverthrow | Lightweight `Result<T, E>` type with chaining methods | https://github.com/supermacro/neverthrow |

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Callable Typing** [-> T22](T22-callable-typing.md) | `Task<A> = () => Promise<A>` is a zero-argument call signature; the effect is encoded in the return type of a callable. Generic call signatures express effectful higher-order functions. |
| **Variance & Subtyping** [-> T08](T08-variance-subtyping.md) | `Promise<T>` is covariant in `T`; `Awaited<T>` (TypeScript 4.5) recursively unwraps nested promises, used with `ReturnType` to infer the resolved type of an async function. |
| **Associated Types** [-> T49](T49-associated-types.md) | `Awaited<T>`, `ReturnType<T>`, and `Parameters<T>` are built-in conditional types that extract components of function types, including their effect wrappers. |
| **Functor / Applicative / Monad** [-> T54](T54-functor-applicative-monad.md) | fp-ts encodes `IO`, `Task`, and `Either` as functor/monad instances; `map`, `chain`, and `ap` are the composition operators that replace `await` chaining at the type level. |

## 5. Gotchas and Limitations

1. **`Promise` is not tracked at the call site** — TypeScript does not warn if a `Promise` is returned by a function but never `await`ed or `.then()`ed; the `@typescript-eslint/no-floating-promises` lint rule fills this gap.
2. **`async` always returns `Promise`** — an `async` function that never `await`s and always returns synchronously still has return type `Promise<T>`; there is no way to express "sync or async" in the native type system without overloading.
3. **`Awaited<T>` flattens nested promises** — `Awaited<Promise<Promise<number>>>` is `number`, which matches runtime behavior but can surprise callers who expect `Promise<number>`.
4. **fp-ts has a steep learning curve** — the full monadic effect stack requires understanding functor/monad combinators; teams unfamiliar with FP often find `neverthrow` or a plain `Result` union more approachable.
5. **Effect library introduces a runtime dependency** — unlike fp-ts's nearly zero-cost abstractions, the Effect library has a runtime with a fiber scheduler; factor this into bundle-size considerations for browser code.
6. **No compiler enforcement of `IO` execution** — `IO<A>` is just `() => A`; the compiler cannot distinguish "this `IO` was run" from "this `IO` was not run". Discipline (or a more opaque type) is required.

## Coming from JavaScript

JavaScript's `Promise` already tracks asynchrony at runtime, but nothing prevents you from calling an async function and discarding the result. TypeScript's `Promise<T>` return type makes the async effect visible in the type, and the `Awaited` utility type and `async`/`await` syntax make it ergonomic to compose. Richer effect tracking (errors, environment) requires library support that JavaScript has no equivalent for.

## 6. Use-Case Cross-References

- [-> UC-08](../usecases/UC08-error-handling.md) Typed error effects via `Result<T, E>`, `Either<E, A>`, or `TaskEither<E, A>`
- [-> UC-21](../usecases/UC21-async-concurrency.md) Async concurrency with `Promise<T>`, `Task<A>`, and structured effect types
