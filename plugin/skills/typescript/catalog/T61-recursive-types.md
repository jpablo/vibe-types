# Recursive Types

> **Since:** TypeScript 3.7 (recursive type aliases); interfaces always supported

## 1. What It Is

TypeScript supports self-referential types in two complementary ways. Recursive interfaces have always been valid: an interface can include properties whose type is the interface itself. Recursive `type` aliases required TypeScript 3.7, which introduced deferred type alias evaluation — before 3.7, the compiler eagerly expanded aliases and immediately detected the cycle as an error. Since 3.7 the compiler defers expansion, making `type JSON = string | number | boolean | null | JSON[] | { [key: string]: JSON }` valid. Recursive conditional types and recursive `infer` patterns are also supported, though TypeScript enforces a recursion depth limit (typically around 100 levels) to prevent non-terminating evaluation.

## 2. What Constraint It Lets You Express

**Types can be defined in terms of themselves; trees, nested structures, and JSON-like schemas type-check correctly.**

- A `Tree<T>` type ensures every node has the same shape as its children — no ad-hoc `any[]` escape hatches.
- The `JSON` type alias precisely captures the full JSON value space, letting functions that accept arbitrary JSON be typed without `unknown` or `any`.
- Recursive conditional types (e.g., `Flatten<T>`) compute types by unpeeling layers, enabling type-level algorithms over nested structures.

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
| **Conditional types** [-> T41](T41-match-types.md) | Recursive conditional types like `Flatten<T>` apply a pattern match at each level of nesting |
| **Generics & bounds** [-> T04](T04-generics-bounds.md) | Generic recursive types (`Tree<T>`) combine self-reference with type parameters for reusable structures |
| **Record types** [-> T31](T31-record-types.md) | Recursive records model JSON objects and nested config schemas |

## 5. Gotchas and Limitations

1. **Recursion depth limit** — TypeScript limits recursive type instantiation depth (typically ~100 levels); deeply nested real data structures may exceed this limit and produce `Type instantiation is excessively deep` errors.
2. **Pre-3.7 recursive type aliases** — code targeting TypeScript before 3.7 must use interfaces instead of `type` aliases for recursive types; mixing old code with new patterns causes surprising errors.
3. **Mutual recursion works but is verbose** — two types that reference each other must both be declared before use; `type` alias mutual recursion requires careful ordering or interface workarounds.
4. **Recursive conditional types can be slow** — the type checker evaluates them eagerly; complex recursive conditional types over large unions can make editor response times noticeably slower.
5. **`infer` in recursive position is limited** — not all recursive `infer` patterns are accepted; the compiler sometimes rejects valid-looking recursive `infer` uses that would require unbounded unification.

## 6. Use-Case Cross-References

- [-> UC-02](../usecases/UC02-parse-tree.md) Parse trees and AST nodes are naturally recursive types
- [-> UC-19](../usecases/UC19-generic-repository.md) JSON-typed payloads use the recursive `JSON` type alias
