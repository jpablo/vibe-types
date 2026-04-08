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
