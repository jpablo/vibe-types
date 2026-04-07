# Decorators & Metaprogramming

> **Since:** TypeScript 5.0 (stage-3 decorators, stable); experimental decorator syntax available since TypeScript 1.5 with `--experimentalDecorators`

## 1. What It Is

TypeScript's metaprogramming surface has two distinct layers. At runtime, **stage-3 decorators** (standardized in TypeScript 5.0) annotate classes, methods, accessors, and fields with functions that execute at class definition time — they can wrap methods, replace property initializers, or register metadata. The legacy experimental decorator API (`--experimentalDecorators`) still exists for compatibility with Angular and NestJS but differs from the standard. At the type level, TypeScript has no macro system; instead, **conditional types**, **mapped types**, and **template literal types** serve as a compile-time type transformation layer — the closest TypeScript equivalent to type-level code generation.

## 2. What Constraint It Lets You Express

**Decorators transform class definitions at definition time; conditional and mapped types transform type expressions at compile time — together they cover most metaprogramming needs without an explicit macro system.**

- A method decorator can wrap an implementation (e.g., logging, memoization, access control) without touching the call sites.
- A class decorator can register the class in a DI container, add metadata, or replace the constructor.
- Conditional types (`T extends U ? A : B`) compute new types from input types, enabling type-level pattern matching.
- Mapped types transform the shape of an object type key-by-key, enabling generic utilities like `Partial<T>`, `Required<T>`, and `Readonly<T>`.

## 3. Minimal Snippet

```typescript
// --- Stage-3 method decorator (TypeScript 5.0+) ---
function log(target: unknown, context: ClassMethodDecoratorContext) {
  const name = String(context.name);
  return function (this: unknown, ...args: unknown[]) {
    console.log(`Calling ${name} with`, args);
    return (target as Function).apply(this, args);
  };
}

class Calculator {
  @log
  add(a: number, b: number): number {
    return a + b;
  }
}

// --- Stage-3 class decorator ---
function sealed(target: unknown, context: ClassDecoratorContext) {
  context.addInitializer(function (this: unknown) {
    Object.seal(this);
  });
}

@sealed
class Config {
  host = "localhost";
  port = 3000;
}

// --- Type-level metaprogramming: conditional type ---
// Unwrap a Promise type to its inner value type
type Awaited<T> = T extends Promise<infer U> ? U : T;

type A = Awaited<Promise<string>>;  // OK — string
type B = Awaited<number>;           // OK — number

// --- Type-level metaprogramming: mapped type ---
// Make every property in T a getter (function returning T[K])
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

interface User { name: string; age: number }
type UserGetters = Getters<User>;
// OK — { getName: () => string; getAge: () => number }
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Conditional Types** [-> T41](T41-match-types.md) | Conditional types are the primary type-level metaprogramming tool; they allow computing new types based on structural relationships, mirroring what macros do at the value level in other languages. |
| **Mapped Types** [-> T62](T62-mapped-types.md) | Mapped types iterate over the keys of a type and transform each one, enabling bulk type transformations equivalent to code generation. |
| **Callable Typing** [-> T22](T22-callable-typing.md) | Method decorators wrap callable types; the decorator must preserve the signature of the original method to avoid breaking callers. |
| **Template Literal Types** [-> T63](T63-template-literal-types.md) | Template literal types compose with mapped types to rename keys (e.g., `get${Capitalize<K>}`) — a common metaprogramming pattern for generating getter/setter shapes. |

## 5. Gotchas and Limitations

1. **Stage-3 vs experimental decorators are incompatible** — `--experimentalDecorators` and the new stage-3 decorators have different APIs and cannot be used together in the same project; Angular/NestJS still require the experimental API as of early 2025.
2. **No `reflect-metadata` in stage-3** — the new decorator standard does not automatically emit type metadata; runtime reflection for DI frameworks still requires `reflect-metadata` and the experimental decorator mode.
3. **Decorators are not type-level** — decorators cannot change the TypeScript-visible type of a decorated class or method; you cannot use a decorator to add properties to a class's inferred type (you can work around this with explicit interface merging).
4. **Conditional type complexity** — deeply nested conditional types become unreadable and can hit TypeScript's instantiation depth limits; prefer named intermediate type aliases to keep them tractable.
5. **No hygienic macros** — TypeScript has no syntax-level macro system; there is no way to introduce new syntax or generate code that appears as if hand-written. Tools like `ts-morph` or compiler plugins (e.g., via `ttypescript`) exist but are fragile and unsupported by the core compiler.
6. **`addInitializer` ordering** — multiple decorators on the same target execute bottom-up (the decorator closest to the declaration runs first); `addInitializer` callbacks run in declaration order, which can produce surprising sequencing bugs.

## 6. Use-Case Cross-References

- [-> UC-19](../usecases/UC19-serialization.md) Use class decorators and metadata to drive JSON serialization/deserialization without hand-written schemas
- [-> UC-09](../usecases/UC09-builder-config.md) Method decorators enforce config validation or transformation in builder-pattern classes
