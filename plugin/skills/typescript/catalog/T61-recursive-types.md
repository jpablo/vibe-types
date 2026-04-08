# Recursive Types

> **Since:** TypeScript 3.7 (recursive type aliases); interfaces always supported

## 1. What It Is

TypeScript supports self-referential types in two complementary ways. Recursive interfaces have always been valid: an interface can include properties whose type is the interface itself. Recursive `type` aliases required TypeScript 3.7, which introduced deferred type alias evaluation — before 3.7, the compiler eagerly expanded aliases and immediately detected the cycle as an error. Since 3.7 the compiler defers expansion, making `type JSON = string | number | boolean | null | JSON[] | { [key: string]: JSON }` valid. Recursive conditional types and recursive `infer` patterns are also supported, though TypeScript enforces a recursion depth limit (typically around 100 levels) to prevent non-terminating evaluation.

The idiomatic way to model recursive **sum types** (variants with different shapes) is via **discriminated unions**: a `type` alias that is a union of object types each carrying a `kind` or `tag` discriminant. This combines the power of recursive type aliases with exhaustive narrowing in `switch` statements.

Mutually recursive types — where `A` references `B` which references `A` — are supported for both interfaces and (since 3.7) type aliases, as long as the mutual references are in non-immediately-expanded positions (i.e., inside object properties or generic arguments, not as a bare alias).

## 2. What Constraint It Lets You Express

**Types can be defined in terms of themselves; trees, nested structures, and JSON-like schemas type-check correctly.**

- A `Tree<T>` type ensures every node has the same shape as its children — no ad-hoc `any[]` escape hatches.
- The `JSON` type alias precisely captures the full JSON value space, letting functions that accept arbitrary JSON be typed without `unknown` or `any`.
- Recursive conditional types (e.g., `Flatten<T>`) compute types by unpeeling layers, enabling type-level algorithms over nested structures.
- Discriminated recursive unions give TypeScript the equivalent of sealed ADTs: the compiler enforces exhaustive handling of every variant.

## 3. Minimal Snippet

```typescript
// Recursive type alias (requires TypeScript 3.7+)
type JSON =
  | string
  | number
  | boolean
  | null
  | JSON[]
  | { [key: string]: JSON };

const data: JSON = { users: [{ name: "Alice", active: true }] }; // OK

// error — Date is not a JSON value
// const bad: JSON = new Date();

// Recursive interface (always valid)
interface BinaryTree<T> {
  value: T;
  left?: BinaryTree<T>;
  right?: BinaryTree<T>;
}

const tree: BinaryTree<number> = {
  value: 1,
  left: { value: 2 },
  right: { value: 3, left: { value: 4 } },
}; // OK

// Recursive conditional type — flatten nested arrays
type Flatten<T> = T extends Array<infer Item> ? Flatten<Item> : T;

type A = Flatten<number[][][]>; // number
type B = Flatten<string[]>;     // string
type C = Flatten<boolean>;      // boolean
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Type aliases** [-> T23](T23-type-aliases.md) | Recursive `type` aliases are the key feature; the deferred evaluation added in TS 3.7 made them possible |
| **Discriminated unions** [-> T02](T02-union-intersection.md) | Recursive discriminated unions give TypeScript sealed-ADT behavior: each variant carries a `kind` tag, enabling exhaustive narrowing |
| **Type narrowing** [-> T14](T14-type-narrowing.md) | `switch (node.kind)` or `if` checks narrow a recursive union to a specific variant, enabling safe recursive traversal |
| **Conditional types** [-> T41](T41-match-types.md) | Recursive conditional types like `Flatten<T>` apply a pattern match at each level of nesting |
| **Generics & bounds** [-> T04](T04-generics-bounds.md) | Generic recursive types (`Tree<T>`) combine self-reference with type parameters for reusable structures |
| **Record types** [-> T31](T31-record-types.md) | Recursive records model JSON objects and nested config schemas |

## 5. Gotchas and Limitations

1. **Recursion depth limit** — TypeScript limits recursive type instantiation depth (typically ~100 levels); deeply nested real data structures may exceed this limit and produce `Type instantiation is excessively deep` errors.
2. **Pre-3.7 recursive type aliases** — code targeting TypeScript before 3.7 must use interfaces instead of `type` aliases for recursive types; mixing old code with new patterns causes surprising errors.
3. **Mutual recursion works but is verbose** — two types that reference each other must both be declared before use; `type` alias mutual recursion requires careful ordering or interface workarounds.
4. **Recursive conditional types can be slow** — the type checker evaluates them eagerly; complex recursive conditional types over large unions can make editor response times noticeably slower.
5. **`infer` in recursive position is limited** — not all recursive `infer` patterns are accepted; the compiler sometimes rejects valid-looking recursive `infer` uses that would require unbounded unification.
6. **Stack overflow on deep structures** — JavaScript runtimes do not perform tail-call optimization (TCO is specified in ES2015 but not implemented in V8/SpiderMonkey). Recursive functions over deeply nested recursive types can throw `RangeError: Maximum call stack size exceeded`. Use iterative algorithms with explicit stacks for production code operating on user-controlled depth.
7. **No structural recursion check** — unlike Lean or Agda, TypeScript does not verify that recursive functions terminate. Infinite loops over recursive types compile without warning.
8. **Recursive type aliases cannot be bare self-references** — `type T = T` and `type T = { v: T }` where the object level is missing are rejected. Self-reference must appear inside an object property, array, or generic argument.

## 6. Beginner Mental Model

Think of a recursive type as a **Russian nesting doll** (matryoshka). A `Tree<number>` is either a `Leaf` (the smallest doll, containing a number) or a `Branch` (a doll containing two smaller dolls, each of which is itself a `Tree<number>`). The definition is circular — a tree is made of trees — but every concrete value you construct is finite.

Unlike Rust, TypeScript (running on a garbage-collected runtime) requires no `Box` or explicit heap indirection: every object is already a reference. Unlike Lean, TypeScript places no termination requirement on functions over recursive types — you can write an infinite loop and the compiler won't stop you.

The practical implication: model your recursive data with discriminated union `type` aliases (for sum types with distinct shapes) or interfaces (for uniform structures like trees). Handle all variants exhaustively in a `switch` statement to get the same safety as sealed ADTs in Scala or Rust.

## Example A — Binary tree with discriminated union

Using a discriminated union makes exhaustive handling checkable at compile time.

```typescript
type Tree<T> =
  | { kind: "leaf"; value: T }
  | { kind: "branch"; left: Tree<T>; right: Tree<T> };

function depth<T>(tree: Tree<T>): number {
  switch (tree.kind) {
    case "leaf":
      return 0;
    case "branch":
      return 1 + Math.max(depth(tree.left), depth(tree.right));
  }
}

function sum(tree: Tree<number>): number {
  switch (tree.kind) {
    case "leaf":
      return tree.value;
    case "branch":
      return sum(tree.left) + sum(tree.right);
  }
}

const tree: Tree<number> = {
  kind: "branch",
  left: { kind: "leaf", value: 1 },
  right: {
    kind: "branch",
    left: { kind: "leaf", value: 2 },
    right: { kind: "leaf", value: 3 },
  },
};

console.log(depth(tree)); // 2
console.log(sum(tree));   // 6
```

## Example B — Expression AST with evaluation

```typescript
type Expr =
  | { kind: "num"; value: number }
  | { kind: "add"; left: Expr; right: Expr }
  | { kind: "mul"; left: Expr; right: Expr }
  | { kind: "neg"; inner: Expr };

function evaluate(expr: Expr): number {
  switch (expr.kind) {
    case "num":
      return expr.value;
    case "add":
      return evaluate(expr.left) + evaluate(expr.right);
    case "mul":
      return evaluate(expr.left) * evaluate(expr.right);
    case "neg":
      return -evaluate(expr.inner);
  }
}

function prettyPrint(expr: Expr): string {
  switch (expr.kind) {
    case "num":
      return String(expr.value);
    case "add":
      return `(${prettyPrint(expr.left)} + ${prettyPrint(expr.right)})`;
    case "mul":
      return `(${prettyPrint(expr.left)} * ${prettyPrint(expr.right)})`;
    case "neg":
      return `-${prettyPrint(expr.inner)}`;
  }
}

// (1 + (2 * -(3)))
const expr: Expr = {
  kind: "add",
  left: { kind: "num", value: 1 },
  right: {
    kind: "mul",
    left: { kind: "num", value: 2 },
    right: { kind: "neg", inner: { kind: "num", value: 3 } },
  },
};

console.log(prettyPrint(expr)); // (1 + (2 * -3))
console.log(evaluate(expr));    // -5
```

## Example C — Mutually recursive types

Types `A` and `B` that each reference the other must be declared together (interfaces) or in compatible alias positions.

```typescript
// Mutually recursive: Expr contains Stmt (via block), Stmt contains Expr
interface Stmt {
  kind: "assign";
  name: string;
  value: Expr;
}

type Expr =
  | { kind: "num"; value: number }
  | { kind: "var"; name: string }
  | { kind: "add"; left: Expr; right: Expr }
  | { kind: "block"; stmts: Stmt[]; body: Expr };

type Env = Record<string, number>;

function evalExpr(expr: Expr, env: Env): number {
  switch (expr.kind) {
    case "num":
      return expr.value;
    case "var":
      return env[expr.name] ?? 0;
    case "add":
      return evalExpr(expr.left, env) + evalExpr(expr.right, env);
    case "block": {
      const inner = { ...env };
      for (const stmt of expr.stmts) {
        inner[stmt.name] = evalExpr(stmt.value, inner);
      }
      return evalExpr(expr.body, inner);
    }
  }
}

const program: Expr = {
  kind: "block",
  stmts: [{ kind: "assign", name: "x", value: { kind: "num", value: 10 } }],
  body: { kind: "add", left: { kind: "var", name: "x" }, right: { kind: "num", value: 5 } },
};

console.log(evalExpr(program, {})); // 15
```

## 7. Use-Case Cross-References

- [-> UC-01](../usecases/UC01-invalid-states.md) — Discriminated recursive unions ensure all structural variants are handled; a missing `case` is a type error (with `noImplicitReturns` or `never` assertion)
- [-> UC-02](../usecases/UC02-domain-modeling.md) — Parse trees and AST nodes are naturally recursive types
- [-> UC-19](../usecases/UC19-serialization.md) — JSON-typed payloads use the recursive `JSON` type alias

## Source Anchors

- [TypeScript 3.7 Release Notes — Recursive Type Aliases](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-7.html#more-recursive-type-aliases)
- [TypeScript Handbook — Recursive Types](https://www.typescriptlang.org/docs/handbook/2/objects.html#the-array-type) (see "Recursive Types" section)
- [TypeScript Deep Dive — Type Aliases](https://basarat.gitbook.io/typescript/type-system/type-alias)
