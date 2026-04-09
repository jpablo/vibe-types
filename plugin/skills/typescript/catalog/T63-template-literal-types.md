# Template Literal Types

> **Since:** TypeScript 4.1

## 1. What It Is

Template literal types extend JavaScript template literal syntax to the type level. `` `prefix_${T}` `` where `T` is a string literal type (or a union of them) produces the union of all string combinations. When `T` is itself a union, TypeScript distributes automatically: `` `${"a" | "b"}${"X" | "Y"}` `` produces `"aX" | "aY" | "bX" | "bY"`. TypeScript 4.1 also introduced four built-in string manipulation utility types: `Uppercase<S>`, `Lowercase<S>`, `Capitalize<S>`, and `Uncapitalize<S>`. Combined with mapped types and the `as` key-remapping clause, template literal types enable renaming all properties of an object type using a computed naming convention. Common applications include type-safe event names, route parameter extraction, CSS-in-JS property names, SQL column selectors, and any API where string patterns carry semantic meaning.

## 2. What Constraint It Lets You Express

**Restrict string types to a specific pattern or computed set; strings that do not match the pattern are compile errors; combining unions generates all valid combinations automatically.**

- An event name like `"click"` can be constrained to `on${"click" | "focus" | "blur"}` so only `"onclick"`, `"onfocus"`, and `"onblur"` are valid.
- Route parameters can be extracted from a path string type: `` "/users/:id/posts/:postId" `` yields `{ id: string; postId: string }`.
- API method names can be derived from data model types, ensuring every field has a corresponding getter without manual listing.

## 3. Minimal Snippet

```typescript
// Type-safe event handler map
type EventName = "click" | "focus" | "blur";
type EventHandlerMap = {
  [K in EventName as `on${Capitalize<K>}`]: (event: Event) => void;
};
// { onClick: ...; onFocus: ...; onBlur: ... }

declare const handlers: EventHandlerMap;
handlers.onClick = (e) => console.log(e);  // OK
// handlers.onHover = () => {};             // error — not a valid key

// Route parameter extraction via conditional types
type ExtractParams<Path extends string> =
  Path extends `${string}:${infer Param}/${infer Rest}`
    ? { [K in Param | keyof ExtractParams<`/${Rest}`>]: string }
    : Path extends `${string}:${infer Param}`
    ? { [K in Param]: string }
    : Record<never, never>;

type Params = ExtractParams<"/users/:id/posts/:postId">;
// { id: string; postId: string }

function navigate<P extends string>(
  path: P,
  params: ExtractParams<P>
): string {
  return path; // OK
}

navigate("/users/:id", { id: "42" });         // OK
// navigate("/users/:id", { userId: "42" });   // error — wrong param name

// Getter interface derived from data type
interface User { id: number; name: string; email: string }

type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

type UserGetters = Getters<User>;
// { getId: () => number; getName: () => string; getEmail: () => string }
```

## 3a. Intrinsic String Manipulation Utility Types

TypeScript 4.1 ships four compiler-intrinsic helpers that operate on string literal types. They are built into the compiler; no import required.

| Utility | Effect |
|---|---|
| `Uppercase<S>` | `"hello"` → `"HELLO"` |
| `Lowercase<S>` | `"HELLO"` → `"hello"` |
| `Capitalize<S>` | `"hello"` → `"Hello"` |
| `Uncapitalize<S>` | `"Hello"` → `"hello"` |

All four distribute over unions automatically.

```typescript
type Direction = "north" | "south" | "east" | "west";

type UpperDirection = Uppercase<Direction>;
// "NORTH" | "SOUTH" | "EAST" | "WEST"

type CSSProperty = `border-${Direction}`;
// "border-north" | "border-south" | "border-east" | "border-west"

// Combine: camelCase CSS property names from a union
type CamelCSS = `border${Capitalize<Direction>}`;
// "borderNorth" | "borderSouth" | "borderEast" | "borderWest"
```

The utilities work only on string literal types (and `string` itself, which passes through unchanged). They are most useful inside mapped types to enforce naming conventions.

## 3b. Non-String Interpolation

Number, `bigint`, boolean, `null`, and `undefined` can all be interpolated — TypeScript converts them to their literal string representations.

```typescript
type Port = 80 | 443 | 8080;
type Origin = `http://localhost:${Port}`;
// "http://localhost:80" | "http://localhost:443" | "http://localhost:8080"

type Flag = `--verbose=${boolean}`;
// "--verbose=true" | "--verbose=false"

// Useful for CSS values
type Px = `${number}px`;          // any number followed by "px"
type Rem = `${number}rem`;

declare function setWidth(value: Px | Rem): void;
setWidth("16px");    // OK
setWidth("1.5rem");  // OK
// setWidth("16");   // error — missing unit
```

Note: `${number}` accepts *any* number, not just literals, so it broadens validation — use it to rule out obviously wrong shapes, not to constrain specific values.

## 3c. String Splitting and Parsing

Template literal types with recursive conditional types enable compile-time string parsing.

```typescript
// Split a dot-separated path into a tuple of segments
type Split<S extends string, Sep extends string> =
  S extends `${infer Head}${Sep}${infer Tail}`
    ? [Head, ...Split<Tail, Sep>]
    : [S];

type Parts = Split<"a.b.c", ".">;  // ["a", "b", "c"]

// Deep property access — derive the type at a dot path
type DeepGet<T, Path extends string> =
  Path extends `${infer Key}.${infer Rest}`
    ? Key extends keyof T
      ? DeepGet<T[Key], Rest>
      : never
    : Path extends keyof T
    ? T[Path]
    : never;

interface Config {
  db: { host: string; port: number };
  app: { debug: boolean };
}

type DbHost = DeepGet<Config, "db.host">;   // string
type AppDebug = DeepGet<Config, "app.debug">; // boolean
// type Bad = DeepGet<Config, "db.missing">; // never
```

## 3d. Discriminated Union Tags with Template Literals

Template literals are effective for namespacing discriminant tags, preventing accidental matches across unrelated union families.

```typescript
type HTTPMethod = "GET" | "POST" | "PUT" | "DELETE";
type HTTPAction = { type: `http:${HTTPMethod}`; url: string };

type WSEvent = "open" | "close" | "message";
type WSAction  = { type: `ws:${WSEvent}`; payload?: unknown };

type Action = HTTPAction | WSAction;

function dispatch(action: Action) {
  switch (action.type) {
    case "http:GET":    return fetch(action.url);
    case "ws:message":  return handle(action.payload);
    // TypeScript narrows correctly; cross-namespace matches are impossible
  }
}

// The `type` field can only ever be one of these six strings:
// "http:GET" | "http:POST" | "http:PUT" | "http:DELETE"
// | "ws:open" | "ws:close" | "ws:message"
declare function handle(p: unknown): void;
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Literal types** [-> T52](T52-literal-types.md) | String literal types are the atoms; template literals combine and constrain them |
| **Mapped types & keyof** [-> T62](T62-mapped-types.md) | The `as` key-remapping clause uses template literals to rename all properties of a type at once |
| **Discriminated unions** [-> T01](T01-algebraic-data-types.md) | Template literal discriminants (e.g., `"request:${Method}"`) create fine-grained discriminated union tags |
| **Conditional types** [-> T41](T41-match-types.md) | Conditional types with `infer` extract parts of a template literal (e.g., route parameter names) |

## 5. Gotchas and Limitations

1. **Distribution explosion** — combining large unions via template literals produces a union whose size is the product of all member counts; very large unions slow the type checker and may hit the `Type produces a union type that is too complex to represent` error.
2. **Only string/number/boolean/bigint/null/undefined are interpolatable** — attempting to interpolate an object type in a template literal type is an error; use `string & keyof T` to filter out non-string keys before interpolating.
3. **`infer` extraction is greedy then minimal** — in patterns like `` `${infer A}:${infer B}` ``, `A` captures as little as possible from the left; complex paths may require multiple recursive conditional types to parse correctly.
4. **No regex patterns** — template literal types express fixed-prefix/suffix patterns but cannot express arbitrary regular expressions; for regex-validated strings, a branded/opaque type with a runtime check is needed.
5. **Editor performance** — large object types with template literal key remapping can noticeably slow IntelliSense; prefer narrower source unions or splitting large mapped types.

## 6. Use-Case Cross-References

- [-> UC-02](../usecases/UC02-domain-modeling.md) AST node kind strings use template literal patterns for namespaced discriminants
- [-> UC-09](../usecases/UC09-builder-config.md) HTTP method + path template literals produce typed route parameter shapes
- [-> UC-05](../usecases/UC05-structural-contracts.md) Event handler maps derive `on${EventName}` keys from an event name union

## 7. When to Use It

Use template literal types when string patterns encode semantic meaning that should be enforced at compile time.

- **Derive related string sets automatically**: When you have a base set of strings and need variants with prefixes/suffixes or case transforms.
  ```typescript
  type Event = "click" | "focus";
  type HandlerKey = `on${Capitalize<Event>}`; // "onClick" | "onFocus"
  ```

- **Namespaces for discriminated unions**: When building multiple union families and accidental cross-family matches would be bugs.
  ```typescript
  type HttpAction = { type: `http:${'GET'|'POST'}` };
  type WsAction = { type: `ws:${'open'|'close'}` };
  // No collision possible between "http:GET" and "ws:open"
  ```

- **Extract data from string patterns**: When parsing structured strings like routes, CSS selectors, or dot-paths.
  ```typescript
  type Params<P extends string> = P extends `/:${infer ID}` ? { id: string } : never;
  ```

- **Validate string formats**: When a valid value must follow a specific shape like `${number}px`.
  ```typescript
  type Size = `${number}px` | `${number}rem`;
  function setWidth(s: Size) {} // rejects "16" (missing unit)
  ```

## 8. When Not to Use It

Avoid template literal types when they add complexity without tangible compile-time safety.

- **Simple string unions are sufficient**: When the pattern doesn't need to be derived or computed.
  ```typescript
  // PREFER this:
  type Status = "draft" | "published" | "archived";

  // AVOID this (unnecessary):
  type Status = `${'draft' | 'published' | 'archived'}`;
  ```

- **Validation requires regex or complex logic**: Template literals cannot express patterns like "email address" or "starts with vowel".
  ```typescript
  // CANNOT do: pattern matching @ symbol, domain suffix, etc.
  type Email = `${string}@${string}.${string}`; // too permissive, useless

  // PREFER runtime validation for complex patterns
  function isValidEmail(s: string): boolean { /* regex */ }
  ```

- **Union explosion risk**: When combining large unions where |A| × |B| exceeds ~50 members.
  ```typescript
  // AVOID: 26 × 26 = 676 members
  type AllPairs = `${'a'|'b'|...'z'}${'A'|'B'|...'Z'}`;

  // PREFER runtime checks or whitelist specific pairs
  ```

- **Overly clever parsing**: When conditional/infer chains exceed 3-4 levels, maintainability drops sharply.
  ```typescript
  // AVOID: hard to debug
  type Parse<S> = S extends `${infer A}${infer B}`
    ? B extends `${infer C}${infer D}` // ...
    : never;

  // PREFER: keep infer chains shallow or use string manipulation at runtime
  ```

## 9. Antipatterns When Using It

### Union Explosion

```typescript
// ❌ BAD: 12 months × 7 days × 24 hours × 60 minutes = 120,960 members
type EveryMoment = `${'Jan'|'Feb'|...'Dec'}-${'Mon'|...'Sun'}-${0|1|...23}-${0|...59}`;

// ✅ GOOD: keep unions small or use runtime validation
type Timestamp = string;
function isValidMoment(s: string): boolean { /* runtime regex */ }
```

### Overly Complex Infer Chaining

```typescript
// ❌ BAD: 5+ levels, hard to reason about
type ParseCSV<S> = S extends `${infer H1},${infer Rest1}`
  ? Rest1 extends `${infer H2},${infer Rest2}`
  ? Rest2 extends `${infer H3},${infer Rest3}`
  ? [H1, H2, H3, ...ParseCSV<Rest3>]
  : never
  : never;

// ✅ GOOD: shallow recursion or runtime parser
function parseCSV(s: string): string[] { return s.split(','); }
```

### Using `${number}` as a Catch-All

```typescript
// ❌ BAD: accepts anything numeric, including "999999999"
type Port = `${number}`;

// ✅ GOOD: restrict to known literals
type Port = "80" | "443" | "8080" | "3000";
type Url = `http://localhost:${Port}`;
```

### Case Transforms for Non-Constants

```typescript
// ❌ BAD: doesn't work on non-literal types
type Transform<T> = Uppercase<T>;
type Result = Transform<string>; // just "string", no transform

// ✅ GOOD: ensure literal type
type Transform<T extends string> = Uppercase<T>;
type Result = Transform<"hello">; // "HELLO"
```

## 10. Antipatterns with Other Techniques (Fixed by Template Literals)

### Runtime String Concatenation Without Validation

```typescript
// ❌ BAD: runtime typo possible
function getHandler(event: string) {
  return handlers[`on${event}`]; // "onClick" vs "onclick" inconsistency
}

// ✅ GOOD: compile-time derived keys
type Event = "click" | "focus";
type Handlers = { [K in `on${Capitalize<Event>}`]: () => void };
const handlers: Handlers = {
  onClick() {},
  onFocus() {},
  // handlers.onhover = ... // compile error
};
```

### Manual Enum Duplication

```typescript
// ❌ BAD: duplication and drift risk
enum Direction { North, South, East, West }
enum DirectionUpper { NORTH, SOUTH, EAST, WEST }
// Must keep both in sync manually

// ✅ GOOD: derive via template literals
type Direction = "north" | "south" | "east" | "west";
type DirectionUpper = Uppercase<Direction>; // derived, always in sync
```

### Magic String Switch Without Type Narrowing

```typescript
// ❌ BAD: no compile-time exhaustiveness
function handle(kind: string) {
  switch (kind) {
    case "user:create": // typo? no error
    case "user:delete":
  }
}

// ✅ GOOD: discriminated union with template literals
type Action = `user:${'create'|'delete'}` | `post:${'publish'|'draft'}`;
function handle(kind: Action) {
  switch (kind) {
    case "user:create": break;
    case "user:delete": break;
    // TypeScript enforces exhaustiveness
  }
}
```

### Partially Typed Config Keys

```typescript
// ❌ BAD: property renaming breaks type safety
type Options = { debugMode: boolean; apiVersion: number };
const config = { DEBUG_MODE: false, API_VERSION: 1 }; // untyped

// ✅ GOOD: typed key transformation
type Options = { debugMode: boolean; apiVersion: number };
type EnvVars<T> = { [K in keyof T as `APP_${Uppercase<string & K>}`]: T[K] };
type TypedConfig = EnvVars<Options>;
// Must provide: { APP_DEBUG_MODE: boolean; APP_API_VERSION: number }
```
