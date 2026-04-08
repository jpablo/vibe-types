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

## 4. Beginner Mental Model

Think of a branded type as a **value with a stamp**. Once the validator stamps a `string` as `Email`, that stamp is part of its type forever. Functions that require an `Email` only accept stamped values — they refuse to handle an unstamped `string` directly. The stamp costs nothing at runtime (there is no actual field); it exists only in the type system to guarantee that validation happened somewhere before this point.

Coming from Rust: this is analogous to a newtype `struct Email(String)` with a private field and a fallible `try_from` constructor, except TypeScript's check is purely static — the brand is erased at runtime, whereas Rust's newtype is a real wrapper.

The key difference from Lean/Scala's refinement libraries: TypeScript's brand only records *that* a check occurred, not *what* the check proved. The type system trusts the constructor author. Lean proves the predicate formally; TypeScript relies on the constructor being correct.

## 5. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Newtypes & Opaque Types** [-> T03](T03-newtypes-opaque.md) | Branded smart constructors are TypeScript's approximation of opaque types; they achieve nominal-like distinctness without language-level newtype support. The brand intersection approach is the most idiomatic TypeScript version of this pattern. |
| **Phantom Types** [-> T27](T27-erased-phantom.md) | Brands and phantom types are closely related; both attach type-level information that has no runtime representation. A brand proves a predicate was checked; a phantom encodes a categorical property (units, state, capability). |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | User-defined type guards (`value is Email`) are the idiomatic way to narrow to a branded type without throwing; the guard body performs the check and the return type asserts the brand. |
| **Conversions & Coercions** [-> T18](T18-conversions-coercions.md) | Extracting the underlying value from a branded type is a free upcast (no cast needed); the base type is always assignable from the branded type because the brand is an intersection. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | The smart constructor itself is a callable type; it can be overloaded or generic (e.g., `parse<T extends Schema>(schema: T, value: unknown): Infer<T>`) to support multiple validated types through one entry point. |

## 6. Gotchas and Limitations

1. **Runtime cost is in the constructor, not the brand** — the brand itself is zero-cost, but every `parseEmail` call performs the validation regex; cache or memoize validators for hot paths.
2. **Brands do not compose automatically** — `type TrimmedEmail = Email & Trimmed` requires separate constructors for each brand; there is no automatic way to combine validators.
3. **`as` cast in the constructor must be trustworthy** — if the constructor logic is wrong or bypassed (e.g., `rawValue as Email`), the brand is a lie; the type system cannot verify the constructor's predicate is correct.
4. **Brands are not visible in error messages** — TypeScript error messages show the brand intersection, which can be verbose and confusing for consumers who see `string & { readonly [__emailBrand]: true }` instead of `Email`.
5. **No exhaustive refinement** — unlike dependent types or Liquid Types, TypeScript brands cannot encode arithmetic predicates (`x > 0 && x < 100`); they only record that *some* check was performed, not the specific invariant.
6. **Library interop** — branded types from different libraries (e.g., `zod` brand vs hand-rolled brand) are not compatible even if conceptually the same; teams must standardize on one branding approach per domain type.

## 7. Example A — Domain Model with Refined Fields

The same Port / Email / Username domain model shown in the Rust and Scala siblings, expressed with smart constructors:

```typescript
// --- Branded primitive types ---
declare const __portBrand: unique symbol;
declare const __emailBrand: unique symbol;
declare const __usernameBrand: unique symbol;

type Port     = number & { readonly [__portBrand]: true };
type Email    = string & { readonly [__emailBrand]: true };
type Username = string & { readonly [__usernameBrand]: true };

// --- Fallible constructors (Result-style, no throws) ---
function parsePort(n: number): Port | Error {
  return Number.isInteger(n) && n >= 1 && n <= 65535
    ? (n as Port)
    : new Error(`Port must be 1–65535, got ${n}`);
}

function parseEmail(s: string): Email | Error {
  return /^[\w.+-]+@[\w-]+\.[\w.]+$/.test(s)
    ? (s as Email)
    : new Error(`Invalid email: ${s}`);
}

function parseUsername(s: string): Username | Error {
  return s.length >= 1 && s.length <= 32 && /^[a-zA-Z0-9_]+$/.test(s)
    ? (s as Username)
    : new Error(`Username must be 1–32 alphanumeric chars, got "${s}"`);
}

// --- Domain object that only accepts validated types ---
interface ServerConfig {
  host: string;
  port: Port;
  adminEmail: Email;
}

// Callers are forced to validate before constructing ServerConfig
const port = parsePort(8080);
if (port instanceof Error) throw port;
const email = parseEmail("admin@example.com");
if (email instanceof Error) throw email;

const config: ServerConfig = { host: "localhost", port, adminEmail: email };

// parsePort(0) returns Error — no valid Port is produced, so
// ServerConfig({ host, port: parsePort(0), adminEmail }) — compile error:
//   Argument of type 'Port | Error' is not assignable to parameter of type 'Port'
```

### Throwing vs. result-returning constructors

Both styles are idiomatic depending on context:

```typescript
// Throwing: simple, suits trusted-input paths (e.g., seeding test data)
function mustParseEmail(s: string): Email {
  if (!/^[\w.+-]+@[\w-]+\.[\w.]+$/.test(s)) throw new Error(`Invalid email: ${s}`);
  return s as Email;
}

// Result-returning: suits untrusted input (user input, API payloads)
function tryParseEmail(s: string): { ok: true; value: Email } | { ok: false; error: string } {
  if (!/^[\w.+-]+@[\w-]+\.[\w.]+$/.test(s)) return { ok: false, error: `Invalid email: ${s}` };
  return { ok: true, value: s as Email };
}

// Type guard variant: integrates with if/else narrowing
function isEmail(s: string): s is Email {
  return /^[\w.+-]+@[\w-]+\.[\w.]+$/.test(s);
}

function sendEmail(to: Email) { /* ... */ }

const raw = "user@example.com";
if (isEmail(raw)) {
  sendEmail(raw); // OK — narrowed to Email inside the block
}
```

## 8. Example B — Parse, Don't Validate with a Schema Library

The "parse, don't validate" principle: push raw input through a validated constructor once at the boundary; downstream code works only with refined types and never re-validates.

```typescript
import { z } from "zod";

// --- Schema definitions ---
const PortSchema     = z.number().int().min(1).max(65535).brand<"Port">();
const EmailSchema    = z.string().email().brand<"Email">();
const UsernameSchema = z.string().min(1).max(32).regex(/^[a-zA-Z0-9_]+$/).brand<"Username">();

type Port     = z.infer<typeof PortSchema>;
type Email    = z.infer<typeof EmailSchema>;
type Username = z.infer<typeof UsernameSchema>;

// --- Single validated parse at the boundary ---
const ServerConfigSchema = z.object({
  host: z.string(),
  port: PortSchema,
  adminEmail: EmailSchema,
});

type ServerConfig = z.infer<typeof ServerConfigSchema>;

// parse() throws ZodError on invalid input; safeParse() returns a discriminated union
const result = ServerConfigSchema.safeParse({
  host: "localhost",
  port: 8080,
  adminEmail: "admin@example.com",
});

if (result.success) {
  // result.data is ServerConfig — all fields are branded
  startServer(result.data); // Port, Email guaranteed valid from here on
}

// --- Functions that accept only validated values ---
function startServer(cfg: ServerConfig): void {
  // cfg.port is Port (branded number), not plain number
  // cfg.adminEmail is Email (branded string), not plain string
  console.log(`Starting on port ${cfg.port}`);
}

// startServer({ host: "x", port: 0, adminEmail: "bad" }); // compile error: 0 is not Port
```

## 9. Recommended Libraries

| Library | Style | Key strength |
|---------|-------|-------------|
| [zod](https://github.com/colinhacks/zod) | Schema object → `.brand<"Name">()` | Most popular; first-class TypeScript inference; `.safeParse()` returns discriminated union |
| [arktype](https://github.com/arktypeio/arktype) | String-based type syntax `"number > 0"` | Parses at definition time; very fast runtime; zero-dependency |
| [valibot](https://github.com/fabian-hiller/valibot) | Composable pipe functions | Smallest bundle size; tree-shakeable per-validator |
| [io-ts](https://github.com/gcanti/io-ts) | Codec duality (encode + decode) | fp-ts integration; principled `Either`-based errors |
| Hand-rolled | `declare const __brand: unique symbol` | Zero dependencies; total control; more boilerplate |

All schema libraries produce branded types on `.parse()` / `.safeParse()`, so the downstream type guarantees are equivalent regardless of which library provides the constructor.

## 10. Common TypeScript Errors and How to Read Them

### `Type 'string' is not assignable to type 'Email'`

```
Argument of type 'string' is not assignable to parameter of type
  'string & { readonly [__emailBrand]: true }'.
  Type 'string' is not assignable to type '{ readonly [__emailBrand]: true }'.
```

**Meaning:** A raw `string` was passed where a branded `Email` is required. The fix is to route the value through `parseEmail()` (or equivalent) rather than casting it directly.

### `Type 'Port | Error' is not assignable to type 'Port'`

```
Type 'Port | Error' is not assignable to type 'Port'.
  Type 'Error' is not assignable to type 'Port'.
```

**Meaning:** A result-returning constructor returned `T | Error` and the caller didn't narrow away the `Error` branch. Add an `instanceof Error` guard before using the value.

### `Property '[__emailBrand]' is missing in type 'ZodEmail'`

```
Type 'string & { [x: symbol]: "Email" }' is not assignable to type
  'string & { readonly [__emailBrand]: true }'.
```

**Meaning:** Two different branding approaches are in use — the zod brand symbol differs from the hand-rolled brand symbol. Standardize: either use zod's `.brand<"Email">()` everywhere, or define the symbol in one place and reference it from the zod schema via a type cast.

### No error when you expect one (silent invalid cast)

```typescript
const bad: Email = "notanemail" as Email; // compiles — no error
```

**Meaning:** The `as` cast bypasses all checking. This is intentional: `as` is an escape hatch. The only protection is that the constructor is the only place in normal code that should use this cast. If you're seeing this outside a constructor, that's the bug.

## 11. Use-Case Cross-References

- [-> UC-01](../usecases/UC01-invalid-states.md) Prevent invalid values from entering the system by requiring branded proof tokens at API boundaries
- [-> UC-02](../usecases/UC02-domain-modeling.md) Model domain primitives (Email, UserId, Money) as branded types to prevent accidental mixing of structurally identical but semantically different strings
- [-> UC-09](../usecases/UC09-builder-config.md) Use branded validated types to ensure builder fields are set with validated values before the built object is used

## Source Anchors

- [TypeScript Handbook — Symbols](https://www.typescriptlang.org/docs/handbook/symbols.html) — `unique symbol` used as brand key
- [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/) — foundational article for the smart constructor pattern
- [zod `.brand()` docs](https://zod.dev/?id=brand) — branded types in zod
- [arktype docs](https://arktype.io/) — string-syntax refinements with zero-dependency runtime checking
- [valibot docs](https://valibot.dev/) — composable pipe-based validation with brand support
