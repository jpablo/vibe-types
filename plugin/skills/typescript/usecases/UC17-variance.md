# Variance

## The Constraint

Generic type parameters have a direction. A type parameter used only in output (return) positions is covariant — a more-specific argument type yields a more-specific generic; used only in input (parameter) positions it is contravariant — a more-general argument type is required. TypeScript infers variance structurally and, with `--strictFunctionTypes`, enforces contravariance on function-typed parameters. Explicit `in`/`out` markers (TypeScript 4.7) let you document and verify intent at declaration time.

## Feature Toolkit

| Feature | Role | Link |
|---|---|---|
| **Variance & subtyping** | The core mechanism — covariant `out T`, contravariant `in T`, invariant, and bivariant; includes explicit 4.7 markers | [-> T08](../catalog/T08-variance-subtyping.md) |
| **Generics & bounds** | Generic type parameters that carry variance annotations and upper-bound constraints | [-> T04](../catalog/T04-generics-bounds.md) |
| **Interfaces** | Variance annotations live on interface type parameters; structural comparison follows the inferred or declared direction | [-> T05](../catalog/T05-type-classes.md) |

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

// Reading a Cat as an Animal is always safe — Cat has everything Animal has.
// Writing is where covariance breaks down (see Pattern C — invariant).
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
