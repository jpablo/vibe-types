# Existential Types

> **Since:** TypeScript community pattern

## 1. What It Is

An **existential type** expresses "there exists some type `T` satisfying this contract" without naming `T` at the point of use. TypeScript has no `exists T` syntax, but two patterns approximate the concept. **Pattern 1 — continuation/callback encoding:** a function `<T>(callback: (x: ExistentialContainer<T>) => Result) => Result` hands `T` to the callback without exposing what `T` is to the outer scope; the outer code knows only that the callback received *something* satisfying the contract. **Pattern 2 — interface hiding:** a class implements an interface; callers receive only the interface type and cannot name the concrete class. Both patterns allow mixing values of different underlying types in a collection where each element supports a common operation — the classic heterogeneous collection use case. Existential types are closely related to trait objects in Rust (`dyn Trait`) and to Haskell's `ExistentialQuantification` extension.

## 2. What Constraint It Lets You Express

**~Achievable — hide the concrete type while preserving the contract; compose values of different concrete types in a single collection that uniformly supports a shared operation.**

- A `Printable[]` array may contain `Dog` and `Cat` instances; the element type is "some type that has `print()`" without fixing it to `Dog | Cat`.
- The continuation encoding prevents the caller from extracting the inner type and using it unsafely outside the callback.
- Adding a new implementor of the interface does not require changing the collection's type — the interface is the only visible contract.

## 3. Minimal Snippet

```typescript
// --- Pattern 1: continuation / callback encoding ---
// The type T is introduced by the generic but hidden from the outside caller.
interface Measurable<T> {
  value: T;
  measure(): number;
}

function withMeasurable<Result>(
  run: <T>(m: Measurable<T>) => Result,
): Result {
  // The concrete T (string) is not visible to the caller of withMeasurable
  const concrete: Measurable<string> = {
    value: "hello world",
    measure() { return this.value.length; },
  };
  return run(concrete);
}

const length = withMeasurable(m => m.measure()); // OK — returns number
// const v = withMeasurable(m => m.value);       // OK but type is unknown to outer scope
//   v is inferred as `unknown` because T is hidden

// --- Pattern 2: interface hiding (structural existential) ---
interface Printable {
  print(): string;
}

class Dog implements Printable {
  constructor(private name: string) {}
  print() { return `Dog: ${this.name}`; }
  bark() { return "Woof!"; } // not part of Printable
}

class Cat implements Printable {
  constructor(private lives: number) {}
  print() { return `Cat with ${this.lives} lives`; }
  purr() { return "Purrr"; } // not part of Printable
}

// Heterogeneous collection — each element is "some Printable thing"
const animals: Printable[] = [new Dog("Rex"), new Cat(9)];

animals.forEach(a => {
  console.log(a.print()); // OK — all Printable values support print()
  // a.bark();            // error — bark() is not on Printable
});

// --- Pattern 3: opaque token (existential via function closure) ---
type Counter = {
  increment(): void;
  value(): number;
};

function makeCounter(): Counter {
  let count = 0; // hidden; the type Counter does not expose the raw number field
  return {
    increment() { count++; },
    value()     { return count; },
  };
}

const c = makeCounter();
c.increment();
c.increment();
console.log(c.value()); // OK — 2
// c.count;             // error — property 'count' does not exist on type Counter
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Interfaces & Structural Typing** [-> T05](T05-type-classes.md) | Interfaces are TypeScript's primary approximation of existential types; any value that satisfies the interface's structural shape is accepted, regardless of its concrete type. |
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | The continuation encoding uses a generic callback `<T>(x: T) => R` to introduce the hidden type variable; the caller cannot supply `T` explicitly — it is bound by the implementation. |
| **Trait Objects / Dynamic Dispatch** [-> T36](T36-trait-objects.md) | Interface-based existential types in TypeScript correspond directly to trait objects in Rust (`dyn Trait`); both erase the concrete type while retaining the vtable of allowed operations. |
| **Union types** [-> T02](T02-union-intersection.md) | `Dog \| Cat` is a **closed** discriminated union — callers can narrow to `Dog` and call `bark()`. An interface existential is **open** — new implementors can be added without changing the collection type. Use interfaces when openness matters, unions when exhaustiveness matters. |
| **Opaque / Newtype** [-> T03](T03-newtypes-opaque.md) | Opaque types hide a representation behind a brand; the closure-based counter pattern (Pattern 3) is a runtime opaque existential — the internal `count` field is inaccessible even through structural narrowing. |
| **Conditional Types** [-> T41](T41-conditional-types.md) | Conditional types can "open" a structural existential — `T extends Printable ? T['print'] : never` recovers the method signature, but cannot recover the hidden concrete type from a true continuation-encoded existential. |
| **`unknown` and type narrowing** [-> T14](T14-type-narrowing.md) | `unknown` is the type you get when the existential's witness type escapes its scope: a `<T>(m: M<T>) => T` callback that returns `T` to the outer caller loses the identity of `T`, resolving to `unknown`. Narrowing via `typeof` / `instanceof` can recover it, at the cost of breaking the abstraction. |

## 5. Gotchas and Limitations

1. **Structural typing leaks concrete shape** — TypeScript's structural system means that if the concrete type has extra properties, they may be visible through type inference at certain call sites; the interface hides them syntactically but not always from `typeof` or advanced conditional types.
2. **No true rank-2 quantification** — TypeScript does not fully support rank-2 types; the continuation encoding is an approximation and breaks down in some compositions (e.g., storing the callback for later use outside the function scope).
3. **Heterogeneous collection requires interface, not union** — `(Dog | Cat)[]` is not an existential type — it is a union, and callers can narrow to `Dog` and call `bark()`. To truly hide the concrete type, use the interface directly as the array element type.
4. **`instanceof` breaks encapsulation** — even with an interface-typed variable, `instanceof Dog` succeeds at runtime; the existential hiding is a compile-time guarantee only.
5. **`as` casts bypass the abstraction** — TypeScript has no runtime seal; `(animal as Dog).bark()` compiles and runs. The existential guarantee is purely a compile-time convention, not enforced by the runtime.
6. **Performance: interface array vs union array** — a `Printable[]` calls `print()` via dynamic dispatch; TypeScript does not optimize this at compile time (unlike a union where inline code can be emitted per variant).
7. **Structural leakage through `satisfies` and inference** — `const x = { print() { return "hi"; }, secret: 42 } satisfies Printable;` widens `x` to `Printable` in type position but the full object literal type (including `secret`) is retained by the compiler in some inference contexts. Explicit annotation (`const x: Printable = ...`) is safer.

## 6. Beginner Mental Model

Think of an interface as a **job description** rather than an identity card. The job description says "must be able to print." Anyone who can print qualifies — you do not need to know their species, breed, or other abilities. When you hold a `Printable`, you can call `print()` but you cannot ask it to `bark()` or `purr()` — that information is hidden behind the job description.

The continuation encoding is a **locked room with a service window**. You pass a callback; the implementation opens the room, hands your callback a value of a hidden type through the window, and returns only what your callback returns. The hidden type never leaves the room — you only get the result of the operation, not the raw value in its concrete form.

## 7. Example A — Heterogeneous Renderer (interface existential)

```typescript
// A real-world renderer pipeline where each node knows how to render itself.
// No renderer knows or cares about the concrete types of the other nodes.

interface RenderNode {
  render(ctx: CanvasRenderingContext2D): void;
  boundingBox(): { x: number; y: number; w: number; h: number };
}

class TextNode implements RenderNode {
  constructor(private text: string, private x: number, private y: number) {}
  render(ctx: CanvasRenderingContext2D) {
    ctx.fillText(this.text, this.x, this.y);
  }
  boundingBox() {
    return { x: this.x, y: this.y, w: this.text.length * 8, h: 16 };
  }
}

class ImageNode implements RenderNode {
  constructor(private src: string, private x: number, private y: number, private w: number, private h: number) {}
  render(ctx: CanvasRenderingContext2D) {
    const img = new Image();
    img.src = this.src;
    ctx.drawImage(img, this.x, this.y, this.w, this.h);
  }
  boundingBox() { return { x: this.x, y: this.y, w: this.w, h: this.h }; }
}

// The scene knows only RenderNode — adding a new node type requires no changes here.
class Scene {
  private nodes: RenderNode[] = [];

  add(node: RenderNode): this { this.nodes.push(node); return this; }

  renderAll(ctx: CanvasRenderingContext2D): void {
    for (const node of this.nodes) {
      node.render(ctx);       // OK — all RenderNodes support render()
      // node.src             // error — 'src' does not exist on type 'RenderNode'
    }
  }

  totalArea(): number {
    return this.nodes.reduce((sum, n) => {
      const bb = n.boundingBox();
      return sum + bb.w * bb.h;
    }, 0);
  }
}
```

## 8. Example B — Continuation Encoding for Safe Resource Access

The continuation encoding is useful when you want to guarantee a resource is used within a controlled scope (similar to Rust's `impl Trait` hiding or Lean's Sigma types restricting access to the witness).

```typescript
// A database connection that must not escape the transaction callback.
// The concrete Row type is existentially hidden — callers cannot store it.

interface Row<T> {
  columns: T;
  rowId: number;
}

interface QueryResult<T> {
  rows: Row<T>[];
  count: number;
}

function withTransaction<Result>(
  callback: <T>(query: (sql: string) => QueryResult<T>) => Result,
): Result {
  // In a real implementation, connection opens here and closes after callback.
  const query = <T>(sql: string): QueryResult<T> => {
    // Execute sql, return typed results ...
    return { rows: [], count: 0 };
  };
  const result = callback(query);
  // Connection closes here — the query function is invalid after this point.
  return result;
}

// Safe usage: the `query` function cannot escape the callback.
const count = withTransaction(query => {
  const result = query<{ name: string; age: number }>("SELECT name, age FROM users");
  return result.count;
});

// The concrete row shape `{ name: string; age: number }` never appears
// in the outer type — count is just `number`.
console.log(count);
```

## 9. Use-Case Cross-References

- [-> UC-14](../usecases/UC14-extensibility.md) Extensible plugin systems where each plugin is "some type implementing the plugin interface"
- [-> UC-05](../usecases/UC05-structural-contracts.md) Structural contracts that accept any conforming type without naming it at the call site
- [-> UC-01](../usecases/UC01-invalid-states.md) Hiding internal representation behind an interface prevents consumers from constructing or mutating values outside the defined contract
- [-> UC-10](../usecases/UC10-encapsulation.md) Closure-based opaque counters and state machines expose only the permitted operations, not the raw state

## 10. Source Anchors

- TypeScript Handbook — [Interfaces](https://www.typescriptlang.org/docs/handbook/2/objects.html)
- TypeScript Handbook — [Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html) (higher-rank callback pattern)
- TypeScript Deep Dive — [Type Compatibility](https://basarat.gitbook.io/typescript/type-system/type-compatibility) (structural typing as existential hiding)
- "Existential types in TypeScript" — community pattern documented in type-level TypeScript resources; no official specification because TypeScript encodes existentials via structural subtyping rather than a dedicated syntax
