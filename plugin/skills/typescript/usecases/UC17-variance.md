# Variance

## The Constraint

Generic type parameters have a direction. A type parameter used only in output (return) positions is covariant — a more-specific argument type yields a more-specific generic; used only in input (parameter) positions it is contravariant — a more-general argument type is required. TypeScript infers variance structurally and, with `--strictFunctionTypes`, enforces contravariance on function-typed parameters. Explicit `in`/`out` markers (TypeScript 4.7) let you document and verify intent at declaration time.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Variance & subtyping** | The core mechanism — covariant `out T`, contravariant `in T`, invariant, and bivariant; includes explicit 4.7 markers | [-> T08](../catalog/T08-variance-subtyping.md) |
| **Generics & bounds** | Generic type parameters that carry variance annotations and upper-bound constraints | [-> T04](../catalog/T04-generics-bounds.md) |
| **Interfaces** | Variance annotations live on interface type parameters; structural comparison follows the inferred or declared direction | [-> T05](../catalog/T05-type-classes.md) |
| **Union types** | Interact with covariance: `Cat \| Dog <: Animal` propagates through covariant type parameters | [-> T02](../catalog/T02-union-intersection.md) |

## Patterns

### Pattern A — Covariant output position

A generic type is covariant in `T` when `T` appears only in return/output positions. If `Cat extends Animal`, then `Producer<Cat>` is assignable to `Producer<Animal>` — you can read a more specific thing wherever a more general thing is read.

```typescript
class Animal { species = "animal" }
class Cat    extends Animal { purr() { return "purrr" } }
class Dog    extends Animal { bark() { return "woof"  } }

// out T — T appears only in output position (return type)
interface Producer<out T> {
  produce(): T;
}

const catProducer: Producer<Cat> = { produce: () => new Cat() };

// OK — Producer<Cat> is assignable to Producer<Animal> (covariant)
const animalProducer: Producer<Animal> = catProducer;
console.log(animalProducer.produce().species); // "animal"

// Arrays are covariant in TypeScript's structural system:
const cats: Cat[] = [new Cat()];
const animals: Animal[] = cats; // OK — Cat[] assignable to Animal[]

// ⚠️  Known unsoundness: TypeScript's array covariance is not runtime-safe.
// After widening, the type checker permits pushing a Dog into what is
// actually a Cat[] in memory:
animals.push(new Dog()); // compiles — but cats[1] is now a Dog at runtime!

// Prefer readonly arrays to get sound covariance:
const readonlyCats: readonly Cat[] = [new Cat()];
const readonlyAnimals: readonly Animal[] = readonlyCats; // OK — and safe
```

### Pattern B — Contravariant input position

A generic type is contravariant in `T` when `T` appears only in parameter/input positions. If `Cat extends Animal`, then `Consumer<Animal>` is assignable to `Consumer<Cat>` — a handler that accepts any animal can safely be used wherever a cat-only handler is expected.

```typescript
// in T — T appears only in input position (parameter)
interface Consumer<in T> {
  consume(value: T): void;
}

function describeAnimal(a: Animal): void {
  console.log(`Species: ${a.species}`);
}

function describeCat(c: Cat): void {
  console.log(`Purr: ${c.purr()}`);
}

const animalConsumer: Consumer<Animal> = { consume: describeAnimal };
const catConsumer:    Consumer<Cat>    = { consume: describeCat    };

// OK — Consumer<Animal> is assignable to Consumer<Cat> (contravariant):
// An animal handler can always handle a cat, because Cat is-an Animal.
const safeCatSlot: Consumer<Cat> = animalConsumer;
safeCatSlot.consume(new Cat()); // OK

// error — Consumer<Cat> is NOT assignable to Consumer<Animal>:
// The handler calls .purr(), which Animal does not have.
const unsafeAnimalSlot: Consumer<Animal> = catConsumer; // error: Type 'Consumer<Cat>' is not assignable to type 'Consumer<Animal>'

// Function parameters: --strictFunctionTypes makes these contravariant
type Handler<T> = (value: T) => void;

const handleAnimal: Handler<Animal> = (a) => console.log(a.species);
const handleCat:    Handler<Cat>    = (c) => c.purr();

const slot: Handler<Cat> = handleAnimal; // OK — Animal handler can handle Cat
const bad:  Handler<Animal> = handleCat; // error — Cat handler cannot handle any Animal
```

### Pattern C — Invariant (read + write position)

A type parameter used in both input and output positions is invariant — neither direction of substitution is safe. The canonical example is a mutable container: you can read from it (covariant), but you can also write to it (contravariant), so both directions must match exactly.

```typescript
// No variance marker — T is invariant (appears in both positions)
interface MutableBox<T> {
  get(): T;        // output — covariant pressure
  set(v: T): void; // input  — contravariant pressure
  // Both together → invariant: only MutableBox<T> is assignable to MutableBox<T>
}

declare const catBox: MutableBox<Cat>;

// error — MutableBox<Cat> is NOT assignable to MutableBox<Animal>
// because the set() input position would allow writing a Dog,
// which would later be read back as a Cat.
const animalBox: MutableBox<Animal> = catBox; // error

// error — MutableBox<Animal> is NOT assignable to MutableBox<Cat>
// because produce() would return an Animal, but callers expect a Cat.
declare const animalBox2: MutableBox<Animal>;
const catBox2: MutableBox<Cat> = animalBox2; // error

// Only exact match is safe:
const sameBox: MutableBox<Cat> = catBox; // OK
```

### Pattern D — Explicit `in`/`out` markers (TypeScript 4.7)

Adding `out` or `in` to a type parameter serves two purposes: it documents the intent, and the compiler verifies the annotation matches actual usage. This also speeds up the type checker on large generic hierarchies by skipping structural inference.

```typescript
// out T — compiler verifies T is used only in output positions
interface ReadStream<out T> {
  read(): T;
  peek(): T | undefined;
  // set(v: T): void; // error: Type parameter 'T' is declared as covariant
  //                  // but is used contravariantly
}

// in T — compiler verifies T is used only in input positions
interface WriteStream<in T> {
  write(value: T): void;
  writeAll(values: readonly T[]): void;
  // read(): T; // error: Type parameter 'T' is declared as contravariant
  //            // but is used covariantly
}

// in out T — explicit invariant (same as no annotation; documents intent)
interface Transform<in out T> {
  apply(input: T): T;
}

// Covariant substitution on ReadStream:
declare const catStream: ReadStream<Cat>;
const animalStream: ReadStream<Animal> = catStream; // OK — covariant

// Contravariant substitution on WriteStream:
declare const animalSink: WriteStream<Animal>;
const catSink: WriteStream<Cat> = animalSink; // OK — contravariant
```

### Pattern E — Method signature bivariance gotcha

TypeScript's method shorthand syntax (`method(x: T): R`) is bivariant — the compiler does not enforce strict contravariance on the parameter. Only function property syntax (`method: (x: T) => R`) respects `--strictFunctionTypes`. This is a deliberate compatibility trade-off and a common source of unsound but compiling code.

```typescript
interface WithMethod {
  handle(a: Animal): void; // method syntax — bivariant (unsound)
}

interface WithProperty {
  handle: (a: Animal) => void; // property syntax — contravariant (sound)
}

const catHandler = {
  handle: (c: Cat) => c.purr(),
};

// Method syntax: both directions compile (bivariant — unsound)
const m: WithMethod = catHandler;   // OK (but potentially unsafe at runtime)

// Property syntax: only safe direction compiles (contravariant — sound)
const p: WithProperty = catHandler; // error: Types of parameters 'a' and 'c' are incompatible

// Best practice: declare callbacks as function properties in interfaces,
// reserve method syntax for operations that are genuinely designed to be
// overridden covariantly (e.g., class methods with intentional override variance).
```

### Pattern F — Union types and covariant widening

Because `Cat | Dog` is a subtype of `Animal`, union types propagate naturally through covariant type parameters. This lets you combine two differently-typed covariant containers and express the result without inventing a common wrapper type.

```typescript
interface Producer<out T> {
  produce(): T;
}

const catProducer: Producer<Cat> = { produce: () => new Cat() };
const dogProducer: Producer<Dog> = { produce: () => new Dog() };

// TypeScript infers T as Cat | Dog; the result widens safely to Animal (covariant):
function pickRandom<T>(a: Producer<T>, b: Producer<T>): T {
  return Math.random() < 0.5 ? a.produce() : b.produce();
}

const mixed: Animal = pickRandom(catProducer, dogProducer); // OK

// Explicit widening through union, then covariance:
const unionProducer: Producer<Cat | Dog> = catProducer;  // OK — Cat <: Cat | Dog
const animalProducer: Producer<Animal>   = unionProducer; // OK — Cat | Dog <: Animal

// The same chain is illegal for invariant (mutable) containers:
declare const mutableCatBox: MutableBox<Cat>;
// const mutableUnionBox: MutableBox<Cat | Dog> = mutableCatBox; // error — invariant
```

### Pattern G — Phantom type parameters

A phantom type parameter does not appear in any runtime field but is used purely for type-level discrimination. This is the TypeScript analogue to Rust's `PhantomData<T>`: you add a phantom `readonly` field (or use the `in`/`out` marker) to give the type parameter a variance direction even though no method actually touches it.

```typescript
// Phantom `Unit` parameter — only the `value` field exists at runtime.
// `out` makes it covariant: Quantity<Metres> <: Quantity<string>.
interface Quantity<out Unit extends string> {
  readonly value: number;
  readonly _phantom?: Unit; // never written; exists only for type checking
}

type Metres    = "metres";
type Kilograms = "kilograms";

const metres    = (n: number): Quantity<Metres>    => ({ value: n });
const kilograms = (n: number): Quantity<Kilograms> => ({ value: n });

function addMetres(a: Quantity<Metres>, b: Quantity<Metres>): Quantity<Metres> {
  return { value: a.value + b.value };
}

const dist = metres(5);
const mass = kilograms(10);

addMetres(dist, dist); // OK
// addMetres(dist, mass); // error: Quantity<"kilograms"> is not assignable to Quantity<"metres">

// Covariance is preserved — Quantity<Metres> widens to Quantity<string>:
const generic: Quantity<string> = dist; // OK

// For invariant phantom tags (e.g., opaque IDs that must not widen),
// use `in out` to prevent both directions of substitution:
interface Tagged<in out Tag extends string> {
  readonly value: number;
  readonly _tag?: Tag;
}
type UserId  = Tagged<"UserId">;
type OrderId = Tagged<"OrderId">;

declare const uid: UserId;
// const oid: OrderId = uid; // error — invariant, cannot widen or narrow
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| **Inferred variance** (structural, `--strict`) | Zero boilerplate; works for most cases | Invisible — must read code to understand the direction |
| **Explicit `in`/`out` markers (4.7+)** | Compiler-verified intent; self-documenting; speeds up deep generics | Requires TS 4.7+; fails loudly if usage contradicts annotation |
| **`in out` (invariant)** | Safest for mutable containers; prevents unsound substitution | May be too restrictive for read-only or write-only use-sites |
| **Function property syntax** | Sound contravariant enforcement under `--strictFunctionTypes` | More verbose than method shorthand |
| **Method shorthand** | Familiar class-style syntax | Bivariant — silently unsound for callback parameters |
| **Mutable arrays (covariant)** | Familiar JavaScript semantics | Structurally unsound — mutation via widened reference is unchecked |
| **`readonly` arrays** | Sound covariance — write operations are eliminated by the type | Cannot `push`/`pop` — must reconstruct to extend |

## JavaScript / pre-TypeScript Comparison

| Technique | JavaScript | TypeScript |
|---|---|---|
| Covariant containers | `Cat[]` assigned to `animal` variable with no check — silent mutation bugs if a `Dog` is later pushed | `Cat[]` assignable to `Animal[]` (covariant read); mutation unsoundness exists but is a known TS trade-off |
| Function parameter direction | Any function is assignable anywhere — `(cat) => cat.purr()` passed where `(animal) => …` is expected compiles and crashes at runtime | `--strictFunctionTypes` enforces contravariance on function-typed values; incompatible parameter types are a compile error |
| Generic containers | No generics at all; type of elements is unknown | `MutableBox<Cat>` vs `MutableBox<Animal>` are distinct invariant types; unsound assignment is a compile error |
| Documenting intent | JSDoc `@template` has no variance annotations | `in`/`out` markers make variance explicit and compiler-checked |
| Method vs property callbacks | No distinction | Method shorthand is bivariant; function property is contravariant — choose syntax intentionally |

## When to Use Which Feature

**Let TypeScript infer variance** in most cases — structural typing handles covariant and contravariant positions automatically when `--strict` (which includes `--strictFunctionTypes`) is enabled.

**Add explicit `in`/`out` markers** (Pattern D) when building large generic hierarchies or public library APIs: the annotation acts as self-documentation, causes the compiler to validate your intent, and can measurably speed up type-checking in deeply nested generic chains.

**Declare callbacks as function properties**, not method shorthand (Pattern E), whenever the callback is passed in as a parameter. Method syntax silently disables strictness for parameter types — an easy source of runtime crashes that compile cleanly.

**Design mutable containers as invariant** (Pattern C) and separate read and write interfaces with `out`/`in` if you want to offer flexibility at use-sites without sacrificing safety.

**Prefer `readonly` arrays** over mutable arrays when passing arrays as covariant values. TypeScript's mutable `T[]` is covariant for compatibility, but it is structurally unsound — widening to `Animal[]` and then pushing a `Dog` into a `Cat[]` compiles. `readonly T[]` / `ReadonlyArray<T>` is sound covariance with the same assignability rules.

**Use union types with covariant generics** (Pattern F) to express "one of several element types" without a wrapper. `Cat | Dog <: Animal` propagates through `out T`, so `Producer<Cat | Dog>` is assignable to `Producer<Animal>` with no extra machinery.

**Use phantom type parameters** (Pattern G) when you need type-level discrimination without runtime overhead — branded IDs, unit-of-measure types, or type-state markers. Use `out` for covariant phantom tags (e.g., read-only quantities) and `in out` for invariant phantom tags (e.g., opaque IDs that must not widen).
