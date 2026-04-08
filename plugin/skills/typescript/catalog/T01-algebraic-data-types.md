# Discriminated Unions & ADTs

> **Since:** TypeScript 2.0 (discriminated unions officially documented)

## 1. What It Is

TypeScript's algebraic data type pattern is built on **discriminated unions** (also called tagged unions): a union of object types where each member carries a common literal-typed property — the *discriminant tag* — that distinguishes it from the others. The compiler uses control-flow analysis to narrow the union to the exact member type inside each branch of a `switch` or `if` chain. Recursive variants (linked lists, trees) are expressed by combining discriminated unions with self-referential type aliases.

TypeScript handles **product types** (records, structs) through plain interfaces and type aliases with named fields — covered in [→ T31](T31-record-types.md). The focus here is on **sum types**: values that can be exactly one of several named shapes at any given time.

TypeScript also has an `enum` keyword (available since TypeScript 1.0), but discriminated unions are generally preferred for richer modeling: they carry payload per variant, compose naturally with generics, and produce plain JavaScript objects rather than a runtime construct. The `enum` keyword is better suited for simple closed sets of named constants (analogous to Python's `Enum` or Java's enum). TypeScript has no native GADT equivalent; type-level constraints on constructors require workarounds with conditional types or phantom parameters.

## 2. What Constraint It Lets You Express

**Values are restricted to a closed set of named shapes; the compiler rejects any code that fails to handle every variant.**

- Each variant is a plain object type with a literal `kind` (or `type`) field, so exhaustiveness is checked structurally, not by class hierarchy.
- Adding a new variant to the union causes a compile error at every `switch` that uses the `never` exhaustiveness pattern, forcing you to update all handler sites.
- Recursive variants (e.g., `type Tree = Leaf | Node<Tree>`) work without any special syntax.

## 3. Minimal Snippet

```typescript
// Discriminated union for payment status
type PaymentStatus =
  | { kind: "pending"; amount: number }
  | { kind: "completed"; amount: number; transactionId: string }
  | { kind: "failed"; amount: number; reason: string };

// Exhaustive handler — compiler enforces all branches are covered
function describe(status: PaymentStatus): string {
  switch (status.kind) {
    case "pending":
      return `Awaiting payment of ${status.amount}`;
    case "completed":
      return `Paid ${status.amount} (tx: ${status.transactionId})`;
    case "failed":
      return `Failed: ${status.reason}`;
    default: {
      // If a new variant is added, `status` will not be `never` here — compile error
      const _exhaustive: never = status; // error if any case is missing
      return _exhaustive;
    }
  }
}

// Recursive variant: binary tree
type Tree<A> =
  | { kind: "leaf" }
  | { kind: "node"; value: A; left: Tree<A>; right: Tree<A> };

function depth<A>(t: Tree<A>): number {
  if (t.kind === "leaf") return 0; // OK — narrowed to Leaf
  return 1 + Math.max(depth(t.left), depth(t.right)); // OK — narrowed to Node
}
```

## 4. Beginner Mental Model

Think of a discriminated union as a **labeled envelope system**. Each envelope has a printed label (`kind: "pending"`) that tells you exactly what's inside without opening it. The compiler acts like a sorter: it reads the label on the envelope and lets you access only the contents that belong to that label. If you set up a sorting machine (a `switch`) but forget to handle one type of envelope, the compiler refuses to run the machine until you add a slot for every possible label.

Coming from Rust: TypeScript's discriminated union ≈ Rust's `enum` with data-carrying variants. The key difference is that TypeScript's check is structural — you are matching on a literal-typed field — while Rust uses actual algebraic enum constructors. Coming from Scala 3: TypeScript's discriminated union ≈ Scala's `enum` with ADT cases, minus the GADT capability.

## 5. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Union Types** [→ T02](T02-union-intersection.md) | Discriminated unions are a special case of union types where each member is an object type with a shared literal field; raw unions without discriminants still narrow but require `typeof`/`instanceof` guards. |
| **Newtypes / Opaque** [→ T03](T03-newtypes-opaque.md) | Brand patterns can be applied to individual variant fields for additional nominal safety — e.g., `{ kind: "completed"; transactionId: TransactionId }` where `TransactionId` is a branded type. |
| **Generics** [→ T04](T04-generics-bounds.md) | ADTs can be parameterized (`Result<T, E>`, `Tree<A>`), reusing the variant structure across different payload types. Generic ADTs are the TypeScript equivalent of Rust's `Option<T>` or `Result<T, E>`. |
| **Structural Typing** [→ T07](T07-structural-typing.md) | Each variant is matched structurally: an object with extra fields satisfies the variant shape unless it is a fresh object literal (excess property checking). This means accidental over-construction can slip past if you pass a pre-existing variable rather than a literal. |
| **Null Safety** [→ T13](T13-null-safety.md) | An ADT variant can carry `T \| null` fields; narrowing inside a variant branch then further narrows nullable fields with `!== null` checks. |
| **Type Narrowing** [→ T14](T14-type-narrowing.md) | Discriminated union narrowing is the primary use case for TS's control-flow analysis; the `default: never` exhaustiveness check is the canonical pattern. |
| **Never / Bottom** [→ T34](T34-never-bottom.md) | `never` is the type of the expression in the default branch after all variants are handled; assigning to a `never`-typed variable is the compile-time exhaustiveness proof. |
| **Literal Types** [→ T52](T52-literal-types.md) | The discriminant field must be a literal type (string or number literal); literal widening must be suppressed with `as const` or explicit annotations. |
| **Phantom / Erased Types** [→ T27](T27-erased-phantom.md) | Phantom type parameters can be added to an ADT to track state (e.g., `Order<"draft">` vs `Order<"submitted">`) without changing runtime shape. |
| **Record Types** [→ T31](T31-record-types.md) | Each variant is itself a record type with a mandatory discriminant field; `interface` or `type` are both valid for individual variants. |

## 6. Gotchas and Limitations

1. **No GADT support** — TypeScript cannot express constructor-level type constraints (e.g., a `List<number>` constructor that guarantees the head is positive). Workarounds with conditional types exist but are complex and fragile.

2. **Discriminant must be a literal** — using `string` or `number` (non-literal) as the tag field prevents narrowing entirely; always annotate with a specific literal type.

3. **Literal widening** — object literals infer widened types by default. `const x = { kind: "pending" }` infers `{ kind: string }` unless you write `{ kind: "pending" as const }` or annotate the variable as the union type:

   ```typescript
   // Wrong — kind infers as `string`, not the literal "pending"
   const bad = { kind: "pending", amount: 100 };
   // bad.kind is string — cannot narrow PaymentStatus with it

   // Fix A — annotate at the call site
   const good1: PaymentStatus = { kind: "pending", amount: 100 };

   // Fix B — use `as const` on the discriminant
   const good2 = { kind: "pending" as const, amount: 100 };

   // Fix C — use `satisfies` (TS 4.9+) to check shape without widening
   const good3 = { kind: "pending", amount: 100 } satisfies PaymentStatus;
   ```

4. **Open vs closed** — TypeScript unions are closed in the sense that you list all members, but there is no `sealed` keyword; nothing prevents external code from constructing an object that matches multiple variants if the discriminant values are not unique.

5. **`instanceof` vs discriminant** — class-based unions use `instanceof` for narrowing, but discriminant-based unions require no class at all; mixing the two in one union makes narrowing awkward.

6. **Recursive types require `type`, not `interface`** — self-referential unions must be expressed with `type` aliases; `interface` supports recursive properties but cannot be used in a union that the same interface is a member of without a wrapping type alias.

7. **Structural excess property checking does not protect pre-existing values** — fresh object literals are excess-property-checked, but assigning an existing variable that has extra fields is not:

   ```typescript
   type Event =
     | { kind: "click"; x: number; y: number }
     | { kind: "keydown"; key: string };

   const data = { kind: "click" as const, x: 10, y: 20, extra: "surprise" };
   const e: Event = data; // OK — no excess property check on variable assignment
   ```

   This is by design (structural typing), but means library boundaries should validate input shapes at runtime if they cannot trust the source.

8. **Adding a variant is a breaking change for consumers.** Unlike Rust's `#[non_exhaustive]` attribute, TypeScript has no mechanism to warn library authors' consumers that more variants may appear in future. Any external code with an exhaustive `switch` on your union type will get a compile error if you add a variant. Options: document that the union is stable, use a `default:` wildcard in externally-facing handlers, or expose a helper type like `KnownPaymentStatus` alongside a wider `PaymentStatus` that includes a catch-all variant (`| { kind: string }`) for forward-compatibility.

9. **TypeScript `enum` vs discriminated union** — the `enum` keyword creates a runtime object and its members are not plain string literals, which can cause friction with serialization and type narrowing. Prefer discriminated unions for complex payload-carrying variants; use `enum` or `const` enum only for simple closed sets of named constants with no associated data.

   ```typescript
   // enum — runtime cost, members are not plain strings
   enum Status { Pending = "pending", Done = "done" }
   // typeof Status.Pending is Status, not "pending"

   // Discriminated union — no runtime overhead, literals narrow naturally
   type Status2 = "pending" | "done";
   ```

## Example A — `assertNever` exhaustiveness helper

The inline `const _: never = x` pattern works but produces a misleading error message. A named helper gives clearer diagnostics and can throw at runtime as a safety net:

```typescript
function assertNever(x: never, message?: string): never {
  throw new Error(message ?? `Unexpected value: ${JSON.stringify(x)}`);
}

type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rect"; width: number; height: number }
  | { kind: "triangle"; base: number; height: number };

function area(s: Shape): number {
  switch (s.kind) {
    case "circle":
      return Math.PI * s.radius ** 2;
    case "rect":
      return s.width * s.height;
    case "triangle":
      return 0.5 * s.base * s.height;
    default:
      return assertNever(s); // compile error if Shape gains a new variant
  }
}
```

If a new variant `{ kind: "ellipse"; rx: number; ry: number }` is added to `Shape`, the `assertNever(s)` call turns into a compile error:

```
Argument of type '{ kind: "ellipse"; rx: number; ry: number }' is not
assignable to parameter of type 'never'.
```

## Example B — Generic `Result<T, E>` type

A reusable two-variant ADT, analogous to Rust's `Result<T, E>` or Scala's `Either`:

```typescript
type Result<T, E> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function divide(a: number, b: number): Result<number, string> {
  if (b === 0) return { ok: false, error: "division by zero" };
  return { ok: true, value: a / b };
}

function unwrapOr<T, E>(result: Result<T, E>, fallback: T): T {
  return result.ok ? result.value : fallback;
}

// Composing results
function parseAndDivide(
  numerator: string,
  denominator: string,
): Result<number, string> {
  const n = Number(numerator);
  const d = Number(denominator);
  if (Number.isNaN(n) || Number.isNaN(d)) {
    return { ok: false, error: "not a number" };
  }
  return divide(n, d);
}

const r = parseAndDivide("10", "2");
if (r.ok) {
  console.log(r.value); // number — narrowed
} else {
  console.error(r.error); // string — narrowed
}
```

`ok: true` / `ok: false` is the discriminant. Note the discriminant does not have to be a `kind` string — any literal-typed field with distinct values works.

## Example C — Guards inside switch arms

TypeScript supports multiple levels of narrowing within a single variant branch using `if` conditions — the equivalent of Rust/Scala match guards:

```typescript
type Command =
  | { kind: "move"; x: number; y: number }
  | { kind: "write"; text: string }
  | { kind: "quit" };

function execute(cmd: Command): void {
  switch (cmd.kind) {
    case "move":
      // further narrowing with a guard
      if (cmd.x === 0 && cmd.y === 0) {
        console.log("move to origin — no-op");
      } else {
        console.log(`moving to (${cmd.x}, ${cmd.y})`);
      }
      break;
    case "write":
      if (cmd.text.length === 0) {
        console.log("ignoring empty write");
      } else {
        console.log(`writing: ${cmd.text}`);
      }
      break;
    case "quit":
      console.log("quitting");
      break;
    default:
      assertNever(cmd);
  }
}
```

TypeScript does not have a `match` expression with inline guards (unlike Rust's `if` guard syntax in `match` arms), so the pattern is a `switch` with nested `if` checks.

## Example D — Multiple discriminant fields

TypeScript can narrow on multiple literal-typed fields simultaneously — the equivalent of matching on a pair of tags. Useful when variants share a primary tag but differ further by a secondary property:

```typescript
type ApiResponse =
  | { status: "success"; format: "json"; data: unknown }
  | { status: "success"; format: "csv";  rows: string[] }
  | { status: "error";   code: number;  message: string };

function handle(res: ApiResponse): void {
  if (res.status === "error") {
    // narrowed to the error variant — `res.code` and `res.message` available
    console.error(`Error ${res.code}: ${res.message}`);
    return;
  }
  // narrowed to success variants — `res.format` available
  if (res.format === "json") {
    console.log("json payload:", res.data); // narrowed further — `res.data`
  } else {
    console.log("csv rows:", res.rows);     // narrowed further — `res.rows`
  }
}
```

The compiler tracks the intersection of both narrowings, so you never need a cast.

## Example E — Recursive ADT: expression evaluator

Recursive discriminated unions with mutual exhaustiveness, analogous to Lean's inductive types or Scala's recursive ADT `enum`:

```typescript
type Expr =
  | { kind: "lit"; value: number }
  | { kind: "add"; left: Expr; right: Expr }
  | { kind: "neg"; expr: Expr }
  | { kind: "mul"; left: Expr; right: Expr };

function evaluate(e: Expr): number {
  switch (e.kind) {
    case "lit":  return e.value;
    case "add":  return evaluate(e.left) + evaluate(e.right);
    case "neg":  return -evaluate(e.expr);
    case "mul":  return evaluate(e.left) * evaluate(e.right);
    default:     return assertNever(e);
  }
}

function prettyPrint(e: Expr): string {
  switch (e.kind) {
    case "lit":  return String(e.value);
    case "add":  return `(${prettyPrint(e.left)} + ${prettyPrint(e.right)})`;
    case "neg":  return `-${prettyPrint(e.expr)}`;
    case "mul":  return `(${prettyPrint(e.left)} * ${prettyPrint(e.right)})`;
    default:     return assertNever(e);
  }
}

// (2 + 3) * -4  →  -20
const expr: Expr = {
  kind: "mul",
  left: { kind: "add", left: { kind: "lit", value: 2 }, right: { kind: "lit", value: 3 } },
  right: { kind: "neg", expr: { kind: "lit", value: 4 } },
};
console.log(evaluate(expr));    // -20
console.log(prettyPrint(expr)); // ((2 + 3) * -4)
```

## Example F — TypeScript `enum` flavors

TypeScript's built-in `enum` keyword has several flavors, each with distinct trade-offs:

```typescript
// String enum — each member is a distinct string literal at runtime
enum Direction {
  North = "NORTH",
  South = "SOUTH",
  East  = "EAST",
  West  = "WEST",
}

// The type of Direction.North is Direction, not "NORTH"
// Narrowing works in switch/case:
function opposite(d: Direction): Direction {
  switch (d) {
    case Direction.North: return Direction.South;
    case Direction.South: return Direction.North;
    case Direction.East:  return Direction.West;
    case Direction.West:  return Direction.East;
    default:              return assertNever(d); // exhaustiveness check still works
  }
}

// Numeric enum — members default to 0, 1, 2, ... (or explicit numbers)
// TypeScript allows passing *any* number where a numeric enum is expected — a known footgun:
enum Status { Pending = 0, Active = 1, Archived = 2 }
function setStatus(s: Status): void { /* ... */ }
setStatus(99);                     // no compile error — numeric enums are not closed!

// const enum — erased at compile time; members replaced with their literal values inline.
// Zero runtime cost, but incompatible with isolated module compilation (esbuild, Babel):
const enum LogLevel { Debug = 0, Info = 1, Warn = 2, Error = 3 }
const level: LogLevel = LogLevel.Warn; // emits: const level = 2;

// Prefer discriminated unions or a "const object + keyof typeof" pattern for most use cases:
const Permissions = {
  Read:    0b001,
  Write:   0b010,
  Execute: 0b100,
} as const;
type Permission = typeof Permissions[keyof typeof Permissions]; // 1 | 2 | 4
```

**When to use `enum`:** simple closed sets of named constants (status codes, log levels) with no associated data and no serialization requirements. For anything requiring payload per variant, use a discriminated union instead.

## Example G — Numeric enum as bitwise flags

Analogous to Python's `Flag` enum, TypeScript uses numeric enums (or const objects) with powers-of-two values to compose bit-flags:

```typescript
const enum FilePermission {
  None    = 0,
  Read    = 1 << 0,   // 1
  Write   = 1 << 1,   // 2
  Execute = 1 << 2,   // 4
  ReadWrite = Read | Write,   // 3
  All       = Read | Write | Execute, // 7
}

function hasPermission(actual: FilePermission, required: FilePermission): boolean {
  return (actual & required) === required;
}

const userPerms = FilePermission.Read | FilePermission.Write;
console.log(hasPermission(userPerms, FilePermission.Read));    // true
console.log(hasPermission(userPerms, FilePermission.Execute)); // false

// To enumerate the set bits, check each flag individually:
function describePerms(p: FilePermission): string[] {
  const parts: string[] = [];
  if (hasPermission(p, FilePermission.Read))    parts.push("read");
  if (hasPermission(p, FilePermission.Write))   parts.push("write");
  if (hasPermission(p, FilePermission.Execute)) parts.push("execute");
  return parts;
}
```

Note: TypeScript's numeric enums do not enforce that only valid combinations are passed (see the `Status` gotcha above). If you need strict flag safety, use a branded type [→ T03](T03-newtypes-opaque.md) over the flag number.

## Example H — Runtime validation with type guards

TypeScript types are erased at runtime. When parsing JSON or accepting external input, you must validate the shape manually or use a library — there is no equivalent to Python's `OrderStatus(value)` that also provides a type-safe result:

```typescript
// Manual type guard — validates discriminant and required fields
function isPaymentStatus(value: unknown): value is PaymentStatus {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  if (v.kind === "pending")   return typeof v.amount === "number";
  if (v.kind === "completed") return typeof v.amount === "number" && typeof v.transactionId === "string";
  if (v.kind === "failed")    return typeof v.amount === "number" && typeof v.reason === "string";
  return false;
}

// Usage: safely parse an API response
const raw: unknown = JSON.parse('{"kind":"completed","amount":99,"transactionId":"tx-42"}');
if (isPaymentStatus(raw)) {
  // raw is PaymentStatus here — fully typed
  console.log(raw.kind); // "completed"
}
```

For production code, prefer a schema library over hand-written guards (see [Recommended Libraries](#recommended-libraries) below).

## 7. Common Compiler Errors and How to Read Them

### Non-exhaustive switch (missing variant)

```
Type '{ kind: "ellipse"; rx: number; ry: number }' is not assignable
to parameter of type 'never'.
```

**Cause:** A new variant was added to the union but the `switch` / `assertNever` call site was not updated.
**Fix:** Add a `case "ellipse":` branch handling the new variant.

### Property does not exist after narrowing

```
Property 'transactionId' does not exist on type
'{ kind: "pending"; amount: number }'.
```

**Cause:** Accessing a field that only exists on one variant while the type is still the full union (no narrowing happened yet).
**Fix:** Check the discriminant first (`if (status.kind === "completed") { status.transactionId }`) or move the access inside the appropriate `case` branch.

### Type is not assignable — literal widening

```
Type '{ kind: string; amount: number; }' is not assignable to
type 'PaymentStatus'.
  Type '{ kind: string; amount: number; }' is not assignable to
  type '{ kind: "pending"; amount: number; }'.
    Types of property 'kind' are incompatible.
      Type 'string' is not assignable to type '"pending"'.
```

**Cause:** The discriminant field was inferred as `string` instead of the specific literal. Common when constructing an object without a type annotation.
**Fix:** Annotate the variable as `PaymentStatus`, use `kind: "pending" as const`, or use `satisfies PaymentStatus`.

### Object literal may only specify known properties (excess property check)

```
Object literal may only specify known properties, and 'extra' does not
exist in type 'PaymentStatus'.
```

**Cause:** Passing a fresh object literal with fields not declared in any variant.
**Fix:** Remove the unknown field, or check whether you are constructing the wrong variant.

## Recommended Libraries

| Library | Role |
|---------|------|
| **ts-pattern** | Ergonomic `match` expression with exhaustiveness checking, guards, and deep pattern destructuring — fills the gap left by TypeScript's `switch`-only matching. |
| **zod** | Schema definition and runtime validation; `z.discriminatedUnion("kind", [...])` validates and types a discriminated union from external data in one declaration. |
| **io-ts** | Functional codecs that double as type guards; each codec is both a runtime validator and a TypeScript type, following fp-ts conventions. |
| **Effect / fp-ts** | Functional ADTs (`Option`, `Either`, `These`) with full type-safe combinator libraries — TypeScript equivalents of Rust's `Option<T>` / `Result<T, E>`. |

## 8. Use-Case Cross-References

- [→ UC-01](../usecases/UC01-invalid-states.md) Prevent invalid states by restricting values to named, valid variants
- [→ UC-02](../usecases/UC02-domain-modeling.md) Model domain concepts as closed sets of shapes with compiler-enforced handling
- [→ UC-03](../usecases/UC03-exhaustiveness.md) Exhaustive switch over all variants with the `never` check pattern
- [→ UC-13](../usecases/UC13-state-machines.md) Encode state machine states as discriminated union variants

## Source Anchors

- [TypeScript Handbook — Narrowing: Discriminated unions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions)
- [TypeScript Handbook — Narrowing: Exhaustiveness checking](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking)
- [TypeScript Handbook — Enums](https://www.typescriptlang.org/docs/handbook/enums.html)
- [TypeScript Handbook — Recursive type aliases](https://www.typescriptlang.org/docs/handbook/2/types-from-types.html)
- TypeScript source: `checker.ts` — `narrowTypeByDiscriminant`, `isDiscriminantProperty`
