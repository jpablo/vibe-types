# Recursive Types

> **Since:** TypeScript 3.7 (recursive type aliases); interfaces always supported

## What it is

TypeScript supports self-referential types through **recursive type aliases** and **recursive interfaces**. An interface can reference itself in property types: `interface Tree { left: Tree; right: Tree }`. Recursive `type` aliases required TypeScript 3.7, which introduced deferred type alias evaluation — before 3.7, the compiler eagerly expanded aliases and immediately detected cycles as errors. Since 3.7 the compiler defers expansion until needed, making `type JSON = string | number | boolean | null | JSON[] | { [key: string]: JSON }` valid. TypeScript also supports **recursive conditional types** and **recursive `infer` patterns**, though it enforces a recursion depth limit (typically ~100 levels) to prevent non-terminating evaluation.

```typescript
// Recursive type alias (requires TypeScript 3.7+)
type JSONValue = 
  | string
  | number
  | boolean
  | null
  | JSONValue[]
  | { [key: string]: JSONValue };

// Recursive interface (always valid)
interface BinaryTree<T> {
  value: T;
  left?: BinaryTree<T>;
  right?: BinaryTree<T>;
}
```

## What constraint it enforces

**Types can be defined in terms of themselves; trees, nested structures, and JSON-like schemas type-check correctly. The type system ensures every recursive position conforms to the self-referential definition.**

- A `Tree<T>` type ensures every node has the same shape as its children — no ad-hoc `any[]` escape hatches.
- The `JSONValue` type alias precisely captures the full JSON value space, letting functions that accept arbitrary JSON be typed without `unknown` or `any`.
- Recursive conditional types (e.g., `Flatten<T>`) compute types by unpeeling layers, enabling type-level algorithms over nested structures.
- The compiler enforces recursion depth limits to prevent excessive complexity during type checking.

## Minimal snippet

```typescript
// Recursive type alias — JSON schema
type JSONValue = 
  | string
  | number
  | boolean
  | null
  | JSONValue[]
  | { [key: string]: JSONValue };

const valid: JSONValue = { users: [{ name: "Alice", active: true, tags: ["pro"] }] };
const invalid: JSONValue = new Date(); // error — Date is not a JSON value

// Recursive interface — binary tree
interface Tree<T> {
  value: T;
  left?: Tree<T>;
  right?: Tree<T>;
}

const tree: Tree<number> = {
  value: 1,
  left: { value: 2 },
  right: { value: 3, left: { value: 4 } },
};

// Recursive conditional type — flatten nested arrays
type Flatten<T> = T extends Array<infer U> ? Flatten<U> : T;

type A = Flatten<number[][][]>;  // number
type B = Flatten<string[]>;      // string
type C = Flatten<boolean>;       // boolean

// Recursive type with explicit base case
type NestedList<T> = T | Array<NestedList<T>>;
type D = NestedList<string>;     // string | string[] | string[][] | ...
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type aliases** [-> T23](T23-type-aliases.md) | Recursive `type` aliases require deferred evaluation (TS 3.7+). The alias name can appear in its own definition. |
| **Conditional types** [-> T41](T41-match-types.md) | Recursive conditional types like `Flatten<T>` apply pattern matching at each nesting level until reaching a base case. |
| **Generics & bounds** [-> T04](T04-generics-bounds.md) | Generic recursive types (`Tree<T>`, `LinkedList<T>`) combine self-reference with type parameters for reusable structures. |
| **Indexed access types** [-> T32](T32-indexed-access-types.md) | Recursive types with index signatures model JSON objects: `{ [key: string]: JSONValue }`. |
| **Tuple types** [-> T12](T12-tuple-types.md) | Recursive tuples are limited by depth but enable fixed-structure recursion patterns. |
| **Mapped types** [-> T51](T51-mapped-types.md) | Recursive mapped types transform each level of nested structures, e.g., `DeepPartial<T>`. |

## Gotchas and limitations

1. **Recursion depth limit.** TypeScript limits recursive type instantiation to ~100 levels. Deeply nested real data (e.g., `DeepPartial` on a 200-level nested object) produces `Type instantiation is excessively deep and possibly infinite` errors.

2. **Pre-3.7 compatibility.** Code targeting TypeScript before 3.7 must use `interface` instead of `type` for recursive definitions. Recursive type aliases are invalid in older versions.

3. **Mutual recursion is verbose.** Two types referencing each other require careful declaration ordering. `type` alias mutual recursion is awkward; prefer `interface` or declare both types before using them:
   ```typescript
   interface Expr { type: "num"; value: number } | { type: "bin"; left: Expr; right: Expr };
   interface Stmt { expr: Expr } | { block: Stmt[] };
   // Must declare both before use due to mutual reference
   ```

4. **Recursive conditional types are expensive.** The type checker evaluates them eagerly; complex recursive type operations over large unions or deeply nested types can make editor response times noticeably slower.

5. **No structural recursion checking.** Unlike Lean or Agda, TypeScript performs no verification that recursive functions terminate. Infinite recursion compiles without warning; termination is a runtime concern.

6. **No coinductive types.** TypeScript lacks native support for infinite structures (streams, infinite trees). Lazy evaluation patterns work at runtime but have no type-level distinction from regular recursive types.

7. **Type inference sometimes gives up.** In complex recursive scenarios, the compiler may infer `any` or fail to narrow types correctly, requiring explicit annotations.

## Beginner mental model

Think of a recursive type as a **Russian nesting doll** definition. A `Tree` is either a `Leaf` (the smallest doll containing a value) or a `Node` (a doll containing two smaller dolls, each of which is itself a `Tree`). The definition is self-referential — a tree is made of trees — but every concrete tree is finite (the nesting eventually reaches leaves).

Coming from Rust: TypeScript recursive types don't require `Box<T>` indirection because JavaScript objects are always references. Coming from Lean: TypeScript doesn't check termination or enforce structural recursion — the type system verifies shape, not behavior.

## Example A — Natural number arithmetic as recursive conditional types

```typescript
// Represent numbers as recursive types (Church encoding-ish)
type Zero = 0;
type Succ<N> = [Zero, ...N];

// Add two number types by peeling off successors
type Add<A, B> = A extends [infer _F, ...infer Rest]
  ? Succ<Add<Rest, B>>
  : B;

type Two = [Zero, Zero];
type Three = [Zero, Zero, Zero];
type Sum = Add<Two, Three>;  // [Zero, Zero, Zero, Zero, Zero]

// Runtime equivalent uses recursive structures
interface Nat {
  isZero: () => boolean;
  succ: () => Nat;
  pred: () => Nat;
}

const zero: Nat = {
  isZero: () => true,
  succ: () => ({
    isZero: () => false,
    succ: () => zero.succ().succ(),
    pred: () => zero,
  }),
  pred: () => zero,
};
```

## Example B — Expression AST with type-safe evaluation

```typescript
// Recursive union type for expressions
type Expr = 
  | { tag: "num"; value: number }
  | { tag: "var"; name: string }
  | { tag: "add"; left: Expr; right: Expr }
  | { tag: "mul"; left: Expr; right: Expr }
  | { tag: "neg"; inner: Expr };

// Type-safe evaluator using discriminated union
function evalExpr(expr: Expr, env: Map<string, number>): number {
  switch (expr.tag) {
    case "num":
      return expr.value;
    case "var":
      return env.get(expr.name) ?? 0;
    case "add":
      return evalExpr(expr.left, env) + evalExpr(expr.right, env);
    case "mul":
      return evalExpr(expr.left, env) * evalExpr(expr.right, env);
    case "neg":
      return -evalExpr(expr.inner, env);
    default:
      const _exhaustive: never = expr;
      throw new Error(`Unknown expression tag: ${_exhaustive}`);
  }
}

const expr: Expr = {
  tag: "add",
  left: { tag: "num", value: 1 },
  right: {
    tag: "mul",
    left: { tag: "num", value: 2 },
    right: { tag: "neg", inner: { tag: "num", value: 3 } },
  },
};

console.log(evalExpr(expr, new Map()));  // -5
```

## Example C — Mutually recursive types (JSON Schema-like)

```typescript
// Forward declaration pattern for mutual recursion
interface Schema;

interface StringSchema { type: "string"; pattern?: string }
interface NumberSchema { type: "number"; minimum?: number; maximum?: number }
interface ArraySchema { type: "array"; items: Schema }
interface ObjectSchema { type: "object"; properties: Record<string, Schema> }

type Schema = 
  | StringSchema
  | NumberSchema
  | ArraySchema
  | ObjectSchema;

// Usage
const userSchema: Schema = {
  type: "object",
  properties: {
    name: { type: "string", pattern: "^[a-zA-Z]+$" },
    age: { type: "number", minimum: 0, maximum: 150 },
    hobbies: {
      type: "array",
      items: { type: "string" },
    },
  },
};

// Recursive validation (type-checked)
function isValid(data: unknown, schema: Schema): boolean {
  switch (schema.type) {
    case "string":
      return typeof data === "string" && 
             (schema.pattern === undefined || new RegExp(schema.pattern).test(data));
    case "number":
      return typeof data === "number" &&
             (schema.minimum === undefined || data >= schema.minimum) &&
             (schema.maximum === undefined || data <= schema.maximum);
    case "array":
      return Array.isArray(data) && 
             data.every(item => isValid(item, schema.items));
    case "object":
      return typeof data === "object" && data !== null &&
             Object.keys(schema.properties).every(key => 
               isValid((data as object)[key], schema.properties[key])
             );
    default:
      const _exhaustive: never = schema;
      return false;
  }
}
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) — Discriminated recursive unions ensure all structural variants are handled via `never` exhaustiveness checks.
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Parse trees, AST nodes, and nested domain models are naturally expressed as recursive types.
- [-> UC-04](../usecases/UC04-generic-constraints.md) — Generic recursive types (`Tree<T>`, `LinkedList<T>`) propagate constraints through the recursive structure.
- [-> UC-19](../usecases/UC19-serialization.md) — JSON-typed payloads use the recursive `JSONValue` type alias for precise typing.
- [-> UC-26](../usecases/UC26-type-level-programming.md) — Recursive conditional types enable type-level compute: `Flatten<T>`, `DeepPartial<T>`, `TupleLength<T>`.

## Source anchors

- [TypeScript 3.7 Release Notes — Recursive Type Aliases](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-7.html#recursive-type-aliases)
- [TypeScript Handbook — Conditional Types](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-2-8.html#conditional-types)
- [TypeScript Handbook — Infer Keyword](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-2-8.html#infer-keyword)
- Microsoft TypeScript source: `src/compiler/types.ts` — type alias recursion handling
- Microsoft TypeScript source: `src/compiler/typeChecker.ts` — recursion depth limit enforcement
