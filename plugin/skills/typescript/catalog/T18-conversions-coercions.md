# Type Assertions & Coercions

> **Since:** TypeScript 1.0 (`as` assertions); `satisfies` since TypeScript 4.9

## 1. What It Is

TypeScript provides several explicit mechanisms for bridging between types. **Type assertions** (`value as T`) instruct the compiler to treat a value as a given type, bypassing structural compatibility checks — no runtime conversion occurs. The **double assertion** idiom (`value as unknown as T`) sidesteps even the overlap requirement for unrelated types, making it the escape hatch of last resort. **User-defined type predicates** (`function isEmail(x: unknown): x is Email`) narrow the type in the calling scope when the function returns `true`. **Assertion functions** (`function assert(cond: boolean): asserts cond`) narrow the type of subsequent code when they do not throw. The **`satisfies` operator** (TypeScript 4.9) validates that an expression conforms to a type without widening it to that type, preserving the literal or inferred type for downstream use.

## 2. What Constraint It Lets You Express

**All conversions are explicit and opt-in; TypeScript has no implicit coercions between types — every boundary crossing is visible in source code.**

- `as T` is a compile-time-only assertion; it cannot convert a `string` to a `number` at runtime — if the runtime value does not match `T`, behavior is undefined.
- `satisfies T` checks shape conformance at the point of use without widening; the variable keeps its most precise type rather than being boxed into `T`.
- Type predicates and assertion functions are the correct way to narrow at runtime boundaries (JSON parsing, API responses) because they tie runtime checks to type narrowing.

## 3. Minimal Snippet

```typescript
// --- as T: bypass structural check (no runtime effect) ---
const raw: unknown = fetchJson();
const user = raw as { name: string; age: number }; // OK — trust the caller
// (user as string) // error — no overlap between object and string
const forced = raw as unknown as string;            // OK — double assertion always compiles

// --- satisfies: validate shape without widening ---
const palette = {
  red: [255, 0, 0],
  green: "#00ff00",
} satisfies Record<string, string | number[]>;
// palette.red is still number[], not string | number[]  // OK — literal type preserved
// palette.missing                                        // error — key does not exist

// --- User-defined type predicate ---
interface Cat { meow(): void }
interface Dog { bark(): void }

function isCat(animal: Cat | Dog): animal is Cat {
  return "meow" in animal;
}

function greet(animal: Cat | Dog) {
  if (isCat(animal)) {
    animal.meow(); // OK — narrowed to Cat
  } else {
    animal.bark(); // OK — narrowed to Dog
  }
}

// --- Assertion function ---
function assertDefined<T>(val: T | null | undefined, msg: string): asserts val is T {
  if (val == null) throw new Error(msg);
}

const maybeUser: string | null = getUser();
assertDefined(maybeUser, "User must be present");
maybeUser.toUpperCase(); // OK — narrowed to string after assertion
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | Type predicates and assertion functions are the user-extensible extension points of the narrowing system; built-in narrowing handles `typeof`/`instanceof`, while predicates cover domain-specific runtime checks. |
| **Gradual Typing** [-> T47](T47-gradual-typing.md) | `as unknown as T` is the primary escape hatch when integrating untyped or weakly-typed code; it is the explicit bridge from the `unknown` boundary into the typed world. |
| **Null Safety** [-> T13](T13-null-safety.md) | The non-null assertion operator `x!` is a shorthand assertion that `x` is not `null` or `undefined`; assertion functions (`asserts val is T`) are the principled alternative that proves the non-null condition. |
| **Structural Typing** [-> T07](T07-structural-typing.md) | `as T` requires structural overlap between the source and target types; structurally unrelated types require the double-assertion escape hatch, signaling a dangerous boundary. |

## 5. Gotchas and Limitations

1. **`as` has no runtime effect** — asserting `x as T` does not convert or validate `x`; if `x` is not actually a `T` at runtime, downstream code will silently operate on the wrong type.
2. **`satisfies` does not narrow variables** — `satisfies` checks the expression at the point of use but does not change the declared type of the variable; it is most useful for inline objects and `const` declarations.
3. **Double assertion is an escape hatch, not a tool** — `x as unknown as T` compiles unconditionally; use it only at genuine type boundaries (e.g., FFI, deserialized JSON) and add a comment explaining why the assertion is safe.
4. **Predicate purity is not enforced** — TypeScript trusts that a `x is T` function accurately reflects the runtime check; a predicate that lies (always returns `true`) will produce unsound types silently.
5. **`asserts` functions must be declared separately** — arrow functions cannot have `asserts` return types in all TypeScript versions; prefer `function` declarations for assertion functions.
6. **`satisfies` and type widening** — `satisfies` does not help when a value is passed to a function expecting the wide type; the parameter's type is still widened at the call site.

## 6. Use-Case Cross-References

- [-> UC-05](../usecases/UC05-structural-contracts.md) Use `satisfies` to validate structural contracts without losing literal precision at definition sites
- [-> UC-16](../usecases/UC16-nullability.md) Use assertion functions and non-null assertions to handle nullable values safely at checked boundaries
