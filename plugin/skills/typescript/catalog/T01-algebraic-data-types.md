# Discriminated Unions & ADTs

> **Since:** TypeScript 2.0 (discriminated unions officially documented)

## 1. What It Is

TypeScript's algebraic data type pattern is built on **discriminated unions** (also called tagged unions): a union of object types where each member carries a common literal-typed property — the *discriminant tag* — that distinguishes it from the others. The compiler uses control-flow analysis to narrow the union to the exact member type inside each branch of a `switch` or `if` chain. Recursive variants (linked lists, trees) are expressed by combining discriminated unions with self-referential type aliases. TypeScript has no native GADT equivalent; type-level constraints on constructors require workarounds with conditional types or phantom parameters.

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

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Union Types** [-> T02](T02-union-intersection.md) | Discriminated unions are a special case of union types where each member is an object type with a shared literal field; raw unions without discriminants still narrow but require `typeof`/`instanceof` guards. |
| **Null Safety** [-> T13](T13-null-safety.md) | An ADT variant can carry `T \| null` fields; narrowing inside a variant branch then further narrows nullable fields with `!== null` checks. |
| **Type Narrowing** [-> T14](T14-type-narrowing.md) | Discriminated union narrowing is the primary use case for TS's control-flow analysis; the `default: never` exhaustiveness check is the canonical pattern. |
| **Never / Bottom** [-> T34](T34-never-bottom.md) | `never` is the type of the expression in the default branch after all variants are handled; assigning to a `never`-typed variable is the compile-time exhaustiveness proof. |
| **Literal Types** [-> T52](T52-literal-types.md) | The discriminant field must be a literal type (string or number literal); literal widening must be suppressed with `as const` or explicit annotations. |
| **Phantom / Erased Types** [-> T27](T27-erased-phantom.md) | Phantom type parameters can be added to an ADT to track state (e.g., `Order<"draft">` vs `Order<"submitted">`) without changing runtime shape. |

## 5. Gotchas and Limitations

1. **No GADT support** — TypeScript cannot express constructor-level type constraints (e.g., a `List<number>` constructor that guarantees the head is positive). Workarounds with conditional types exist but are complex and fragile.
2. **Discriminant must be a literal** — using `string` or `number` (non-literal) as the tag field prevents narrowing entirely; always annotate with a specific literal type.
3. **Literal widening** — object literals infer widened types by default. `const x = { kind: "pending" }` infers `{ kind: string }` unless you write `{ kind: "pending" as const }` or annotate the variable.
4. **Open vs closed** — TypeScript unions are nominally closed in the sense that you list all members, but there is no sealed keyword; nothing prevents external code from constructing an object that matches multiple variants if the discriminant values are not unique.
5. **`instanceof` vs discriminant** — class-based unions use `instanceof` for narrowing, but discriminant-based unions require no class at all; mixing the two in one union makes narrowing awkward.
6. **Recursive types require `type`, not `interface`** — self-referential unions must be expressed with `type` aliases; `interface` supports recursive properties but cannot be used in a union that the same interface is a member of without a wrapping type alias.

## 6. Use-Case Cross-References

- [-> UC-01](../usecases/UC01-invalid-states.md) Prevent invalid states by restricting values to named, valid variants
- [-> UC-02](../usecases/UC02-domain-modeling.md) Model domain concepts as closed sets of shapes with compiler-enforced handling
- [-> UC-03](../usecases/UC03-exhaustiveness.md) Exhaustive switch over all variants with the `never` check pattern
- [-> UC-13](../usecases/UC13-state-machines.md) Encode state machine states as discriminated union variants
