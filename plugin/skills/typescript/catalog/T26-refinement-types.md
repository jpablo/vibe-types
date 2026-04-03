# Refinement Types via Branded Smart Constructors

> **Since:** TypeScript community pattern; `unique symbol` since TypeScript 2.7

## 1. What It Is

TypeScript has no built-in refinement types (types that restrict a base type to values satisfying a predicate, such as `int > 0`). The standard workaround is the **branded smart constructor** pattern: (1) define a branded type by intersecting the base type with an object type carrying a unique brand property — `type Email = string & { readonly __brand: unique symbol }` — (2) provide a single constructor function that validates the value and returns it cast to the branded type, and (3) use only the branded type downstream, so consumers never re-validate. Because the brand property is never actually present on the value at runtime (the cast is done with `as`), there is zero runtime overhead. Runtime validation libraries — **zod**, **io-ts**, **arktype**, **valibot** — automate this pattern at schema boundaries, producing typed validated values from untyped input.

## 2. What Constraint It Lets You Express

**Values carry compile-time proof of having been validated; a function that requires a branded `Email` cannot be called with a plain `string`, forcing the caller to go through the validated constructor.**

- The brand acts as a proof token: holding an `Email` value means the validation was performed at some point in the program.
- Invalid values cannot flow into typed APIs without an explicit `as` cast — the type system enforces that validation must precede use.
- Multiple brands can be stacked: `type TrimmedEmail = Email & { readonly __trimmed: unique symbol }` narrows further.

## 3. Minimal Snippet

```typescript
// --- Define branded type ---
declare const __emailBrand: unique symbol;
type Email = string & { readonly [__emailBrand]: true };

// --- Smart constructor: only way to produce an Email ---
function parseEmail(raw: string): Email {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(raw)) {
    throw new Error(`Invalid email: ${raw}`);
  }
  return raw as Email; // OK — cast is safe because we validated above
}

// --- Branded type in API surface ---
function sendWelcomeEmail(to: Email, subject: string): void {
  console.log(`Sending "${subject}" to ${to}`);
}

const email = parseEmail("alice@example.com"); // OK — Email
sendWelcomeEmail(email, "Welcome!");            // OK

// sendWelcomeEmail("bob@example.com", "Hi"); // error — string is not assignable to Email

// --- Stacked brands ---
declare const __nonEmptyBrand: unique symbol;
type NonEmptyString = string & { readonly [__nonEmptyBrand]: true };

function parseNonEmpty(s: string): NonEmptyString {
  if (s.length === 0) throw new Error("String must not be empty");
  return s as NonEmptyString;
}

// --- Schema library pattern (zod) ---
import { z } from "zod";

const EmailSchema = z.string().email().brand<"Email">();
type ZodEmail = z.infer<typeof EmailSchema>; // OK — string & { [BRAND]: "Email" }

const result = EmailSchema.safeParse("alice@example.com");
if (result.success) {
  sendWelcomeEmail(result.data, "Via zod!"); // OK — ZodEmail satisfies Email? (only with matching brand)
}
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Newtypes & Opaque Types** [-> T03](T03-newtypes-opaque.md) | Branded smart constructors are TypeScript's approximation of opaque types; they achieve nominal-like distinctness without language-level newtype support. The brand intersection approach is the most idiomatic TypeScript version of this pattern. |
| **Phantom Types** [-> T27](T27-erased-phantom.md) | Brands and phantom types are closely related; both attach type-level information that has no runtime representation. A brand proves a predicate was checked; a phantom encodes a categorical property (units, state, capability). |
| **Callable Typing** [-> T22](T22-callable-typing.md) | The smart constructor itself is a callable type; it can be overloaded or generic (e.g., `parse<T extends Schema>(schema: T, value: unknown): Infer<T>`) to support multiple validated types through one entry point. |

## 5. Gotchas and Limitations

1. **Runtime cost is in the constructor, not the brand** — the brand itself is zero-cost, but every `parseEmail` call performs the validation regex; cache or memoize validators for hot paths.
2. **Brands do not compose automatically** — `type TrimmedEmail = Email & Trimmed` requires separate constructors for each brand; there is no automatic way to combine validators.
3. **`as` cast in the constructor must be trustworthy** — if the constructor logic is wrong or bypassed (e.g., `rawValue as Email`), the brand is a lie; the type system cannot verify the constructor's predicate is correct.
4. **Brands are not visible in error messages** — TypeScript error messages show the brand intersection, which can be verbose and confusing for consumers who see `string & { readonly [__emailBrand]: true }` instead of `Email`.
5. **No exhaustive refinement** — unlike dependent types or Liquid Types, TypeScript brands cannot encode arithmetic predicates (`x > 0 && x < 100`); they only record that *some* check was performed, not the specific invariant.
6. **Library interop** — branded types from different libraries (e.g., `zod` brand vs hand-rolled brand) are not compatible even if conceptually the same; teams must standardize on one branding approach per domain type.

## 6. Use-Case Cross-References

- [-> UC-01](../usecases/UC01-invalid-states.md) Prevent invalid values from entering the system by requiring branded proof tokens at API boundaries
- [-> UC-02](../usecases/UC02-domain-modeling.md) Model domain primitives (Email, UserId, Money) as branded types to prevent accidental mixing of structurally identical but semantically different strings
- [-> UC-09](../usecases/UC09-builder-config.md) Use branded validated types to ensure builder fields are set with validated values before the built object is used
