You are an expert in ESLint plugin development and TypeScript static analysis. Your task is to read a TypeScript knowledge file and identify every antipattern that can be detected as a deterministic ESLint rule.

## ESLint Rule Categories

Before analyzing, understand these three categories:

### 1. syntactic (no type information needed)
The rule only looks at the **shape of the code in the parse tree (AST)**. It does NOT know what TypeScript type an expression has — it only sees identifiers, operators, node types, and structure. These rules are fast and require no special configuration.

Examples of syntactic patterns:
- An `interface` with 3 or more `isXxx: boolean` fields (count AST nodes by name pattern and type keyword)
- A `switch` default branch containing `as any` (literal keyword in a specific AST position)
- `||` where the left operand uses optional chaining `?.` (operator + child node type check)
- A union type where two members share the same literal value on a property (collect and compare literals)

### 2. type-aware (requires TypeScript type checker)
The rule needs to call into TypeScript's compiler API to ask "what is the TypeScript type of this expression?" This requires the consumer to configure `parserOptions: { project: "./tsconfig.json" }` in their ESLint config. Slower but more precise.

Examples of type-aware patterns:
- Knowing whether the discriminant field of a `switch` is typed as a union type (not just any string)
- Detecting that a value returned from `JSON.parse` is being cast to a specific branded type
- Verifying that a function parameter accepting `unknown` is not passed to a typed function without a check

### 3. intent-based (cannot be an ESLint rule)
The pattern depends on understanding the developer's intent, business domain, or data-flow across module boundaries. No deterministic algorithm can reliably detect these without an LLM or manual review.

Examples of intent-based patterns:
- Deciding whether a developer "should" use a branded type for a particular string field
- Detecting that all creation paths for a type go through its smart constructor
- Knowing whether two separate types should be merged into one

## Your Task

Read the knowledge file provided below. Find every antipattern described in it (look in sections titled "Antipatterns", "Gotchas", "When NOT to Use", code blocks showing "Bad:" vs "Good:", numbered antipattern lists, etc.).

For each antipattern:
1. Decide: is it `syntactic`, `type-aware`, or `intent-based`?
2. If `syntactic` or `type-aware`: create a rule spec entry.
3. If `intent-based`: still create an entry, but set `detectability` to `"intent-based"` and fill in `skip_reason` explaining why.

## Output Format

Write a JSON array to the file path specified at the end of this prompt. Each element has this exact shape:

```json
{
  "rule_name": "no-parallel-boolean-flags",
  "catalog_id": "T01",
  "antipattern_summary": "interface/type with 3+ isXxx boolean fields instead of a discriminated union",
  "detectability": "syntactic",
  "skip_reason": "",
  "antipattern_snippet": "interface Payment {\n  isPending: boolean;\n  isCompleted: boolean;\n  isFailed: boolean;\n}",
  "correct_snippet": "type Payment =\n  | { kind: \"pending\" }\n  | { kind: \"completed\"; transactionId: string }\n  | { kind: \"failed\"; reason: string };",
  "ast_nodes_to_visit": ["TSInterfaceBody", "TSTypeLiteral"],
  "detection_algorithm": "Visit each TSInterfaceBody and TSTypeLiteral. Collect TSPropertySignature members where the property name matches /^is[A-Z]/ and the type annotation is TSBooleanKeyword. If the count is >= 3 (configurable), report on the interface/type declaration node."
}
```

Field rules:
- `rule_name`: kebab-case, prefixed with `no-`, `require-`, or `prefer-`. Must be unique across all entries.
- `catalog_id`: the ID from the knowledge file filename (e.g., `T01`, `UC03`).
- `antipattern_summary`: one sentence describing what the antipattern is.
- `detectability`: exactly `"syntactic"`, `"type-aware"`, or `"intent-based"`.
- `skip_reason`: empty string `""` for `syntactic`/`type-aware`; a sentence for `intent-based`.
- `antipattern_snippet`: a minimal TypeScript code snippet that VIOLATES the rule (copy from the knowledge file if possible).
- `correct_snippet`: a minimal TypeScript code snippet that FOLLOWS the correct pattern.
- `ast_nodes_to_visit`: array of TypeScript ESTree node type names (e.g., `TSPropertySignature`, `TSUnionType`, `SwitchCase`, `LogicalExpression`). Look up the correct node type names.
- `detection_algorithm`: plain English description of the algorithm. Be precise: name the exact node types, property names, and conditions to check.

## Important Rules

- Every distinct antipattern in the file gets its own entry. One antipattern = one rule.
- Do NOT invent antipatterns not described in the knowledge file.
- Do NOT merge two different antipatterns into one rule.
- Keep rule names unique and descriptive. If the same antipattern appears in multiple files, use the catalog ID as a suffix (e.g., `no-as-any-t01`).
- Prefer `syntactic` over `type-aware` when the pattern can be detected structurally without type information.
- For `detection_algorithm`, be specific enough that a developer could implement it without reading the knowledge file again.

## Common TypeScript ESTree Node Types Reference

Useful node types for TypeScript rules:
- `TSInterfaceDeclaration` — `interface Foo { ... }`
- `TSInterfaceBody` — the `{ ... }` body of an interface
- `TSTypeAliasDeclaration` — `type Foo = ...`
- `TSTypeLiteral` — `{ a: string; b: number }` inline type
- `TSPropertySignature` — a property in an interface or type literal
- `TSUnionType` — `A | B | C`
- `TSIntersectionType` — `A & B`
- `TSLiteralType` — a literal type like `"pending"` or `42`
- `TSBooleanKeyword` — the `boolean` type keyword
- `TSStringKeyword` — the `string` type keyword
- `TSNullKeyword` — the `null` type
- `TSUndefinedKeyword` — the `undefined` type
- `TSAnyKeyword` — the `any` type
- `TSNeverKeyword` — the `never` type
- `TSAsExpression` — `x as SomeType` (type assertion)
- `TSNonNullExpression` — `x!` (non-null assertion)
- `TSConditionalType` — `A extends B ? C : D`
- `TSTemplateLiteralType` — template literal type like `` `prefix-${string}` ``
- `SwitchStatement` — a `switch(x) { ... }` statement
- `SwitchCase` — a `case X:` or `default:` within a switch; `test` is `null` for `default:`
- `LogicalExpression` — `a || b`, `a && b`, `a ?? b`; `operator` is `"||"`, `"&&"`, or `"??"`
- `ChainExpression` — wraps optional chaining: `a?.b`
- `MemberExpression` — property access; `optional: true` if using `?.`

