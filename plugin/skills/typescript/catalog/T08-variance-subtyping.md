# Variance & Subtyping

> **Since:** TypeScript 1.x (structural subtyping); `--strictFunctionTypes` since TypeScript 2.6; explicit `in`/`out`/`in out` variance markers since TypeScript 4.7

## 1. What It Is

**Variance** describes how subtyping relationships on a generic type's type arguments relate to subtyping on the generic type itself. If `Dog extends Animal`, does `Box<Dog>` extend `Box<Animal>`? The answer depends on how `T` is used inside `Box`:

- **Covariant** (`out T`): `Box<Dog>` extends `Box<Animal>`. `T` appears only in output/return positions.
- **Contravariant** (`in T`): `Box<Animal>` extends `Box<Dog>`. `T` appears only in input/parameter positions.
- **Invariant** (`in out T`): neither direction is safe. `T` appears in both positions.
- **Bivariant**: both directions are allowed (unsound; TypeScript's pre-2.6 method behavior).

TypeScript **infers variance** from usage automatically. TypeScript 2.6's `--strictFunctionTypes` made function type parameters contravariant (but method signatures in interfaces/classes remain bivariant for compatibility). TypeScript 4.7 added **explicit variance markers** `out T`, `in T`, and `in out T` on type parameters, which both serve as documentation and cause the compiler to verify the annotation matches actual usage.

## 2. What Constraint It Lets You Express

**Control whether a generic type can be used in a more-specific (covariant) or more-general (contravariant) position; catch unsound substitutions at compile time.**

- Marking `out T` prevents `T` from appearing in parameter positions; any attempt to use `T` as an input is a compile error.
- Marking `in T` prevents `T` from appearing in return positions; ensures the generic cannot be used covariantly.
- Marking `in out T` explicitly requires invariance; the compiler verifies that `T` genuinely appears in both positions.
- `--strictFunctionTypes` ensures that `(animal: Animal) => void` is not assignable to `(dog: Dog) => void` (contravariance of parameters in function types).

## 3. Minimal Snippet

```typescript
// Covariant array: Dog[] is assignable to Animal[] (but writing is unsafe!)
class Animal { name = "animal" }
class Dog extends Animal { breed = "labrador" }

const dogs: Dog[] = [new Dog()];
const animals: Animal[] = dogs; // OK — arrays are covariant in TS (but mutable, so unsound)
animals.push(new Animal());     // Runtime problem: dogs now contains a non-Dog!

// Contravariant function parameter: Animal callback is assignable to Dog callback
type Handler<T> = (value: T) => void;
const handleAnimal: Handler<Animal> = (a) => console.log(a.name);
const handleDog: Handler<Dog> = handleAnimal; // OK under --strictFunctionTypes (contravariant)
// const handleAnimalFromDog: Handler<Animal> = ((_: Dog) => {}); // error — Dog callback not assignable to Animal callback

// Explicit variance markers (TypeScript 4.7)
interface Producer<out T> {  // T is covariant — only returned, never consumed
  produce(): T;
  // consume(value: T): void; // error — 'out T' cannot appear in parameter position
}

interface Consumer<in T> {   // T is contravariant — only consumed, never returned
  consume(value: T): void;
  // produce(): T;           // error — 'in T' cannot appear in return position
}

interface ReadWrite<in out T> {  // T is invariant — both read and written
  get(): T;
  set(value: T): void;
}

const dogProducer: Producer<Dog> = { produce: () => new Dog() };
const animalProducer: Producer<Animal> = dogProducer; // OK — covariant

const animalConsumer: Consumer<Animal> = { consume: (a) => console.log(a.name) };
const dogConsumer: Consumer<Dog> = animalConsumer; // OK — contravariant

const dogReadWrite: ReadWrite<Dog> = { get: () => new Dog(), set: (_) => {} };
// const animalReadWrite: ReadWrite<Animal> = dogReadWrite; // error — invariant
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | Variance is a property of how type parameters are used within generic types; bounds constrain what types may be substituted, variance constrains in which direction substitution is safe. |
| **Interfaces & Structural Contracts** [-> T05](T05-type-classes.md) | Method signatures in interfaces remain bivariant even under `--strictFunctionTypes`; switching to function-property syntax (`method: (x: T) => void`) opts into contravariant checking. |
| **Union & Intersection Types** [-> T02](T02-union-intersection.md) | Union types behave covariantly: if `A extends B`, then `A \| C extends B \| C`. Intersection types are used to express invariant positions by requiring both `in` and `out` usage. |
| **`ReadonlyArray<T>` vs `Array<T>`** | `ReadonlyArray<Dog>` is safely assignable to `ReadonlyArray<Animal>` (covariant) because no write methods exist. `Array<T>` is mutable and therefore unsoundly covariant in TypeScript. Prefer `ReadonlyArray` / `readonly T[]` for parameters that only read. |
| **Function types** | `(arg: T) => R` is contravariant in `T` and covariant in `R` under `--strictFunctionTypes`. This is the canonical mixed-variance example: a broader-input function can substitute for a narrower-input one. |

## 5. Gotchas and Limitations

1. **Mutable arrays are covariant but unsound** — `Dog[]` is assignable to `Animal[]` even though pushing an `Animal` into `dogs` at runtime breaks the `Dog[]` invariant. TypeScript accepts this for pragmatic reasons; use `ReadonlyArray<Dog>` for true safe covariance.
2. **Method signatures remain bivariant** — `{ method(x: Dog): void }` is assignable to `{ method(x: Animal): void }` even under `--strictFunctionTypes`. This is a known soundness gap preserved for compatibility; use function-property syntax to get contravariant checking:
   ```typescript
   // Bivariant (method syntax — unsound):
   interface BivariantHandler { handle(x: Dog): void }
   // Contravariant (property syntax — sound under --strictFunctionTypes):
   interface ContravariantHandler { handle: (x: Dog) => void }
   ```
3. **Explicit variance markers are checked but not enforced on callers** — `out T` on a type parameter causes the compiler to verify usage within the type definition, but callers still use the type structurally; the markers do not change assignability rules (they only verify the declaration is consistent).
4. **Inferring variance can be slow** — for large, complex generic types the compiler may fall back to invariant checking to avoid expensive variance inference; explicit markers help performance and correctness.
5. **`in`/`out`/`in out` markers require TypeScript 4.7+** — older codebases cannot use them; document variance with comments instead.
6. **Variance and `readonly`** — `readonly T[]` is a safe covariant array because the write method is absent; variance and immutability interact closely. Always consider whether a covariant generic should be `Readonly`.

## 6. Beginner Mental Model

Variance answers the question: **"If `Dog` is a subtype of `Animal`, is `Box<Dog>` a subtype of `Box<Animal>`?"**

- **Covariant (`out T`)**: Yes — a box of dogs is a box of animals. Works for read-only containers (you only take things out). `ReadonlyArray<Dog>` is safely assignable to `ReadonlyArray<Animal>`.
- **Contravariant (`in T`)**: The direction reverses — a handler of animals can stand in for a handler of dogs. Works for consumer/callback types (you only put things in). `(a: Animal) => void` is safely assignable to `(d: Dog) => void`.
- **Invariant (`in out T`)**: Neither — a mutable box of dogs is not a mutable box of animals, because someone could put a non-Dog in through the `Animal` reference. Mutable containers require exact type matches.

The Liskov Substitution Principle is the formal justification: if `Dog extends Animal`, any code expecting an `Animal` must work correctly when given a `Dog`. Variance annotations tell the compiler which generic types preserve this substitutability and in which direction.

## Example A — Read-only vs mutable container

`ReadonlyArray<T>` is TypeScript's analogue of Python's `Sequence[T]`: it exposes only read methods so it is safely covariant. Plain `Array<T>` has both read and write methods and is therefore invariant in a sound type system (TypeScript makes it covariant for pragmatic reasons, which is a known unsoundness).

```typescript
class Animal { name = "animal" }
class Dog extends Animal { breed = "labrador" }
class Cat extends Animal { indoor = true }

// ✓ ReadonlyArray is covariant: Dog[] <: ReadonlyArray<Animal>
function printAll(animals: ReadonlyArray<Animal>): void {
  for (const a of animals) console.log(a.name);
}
const dogs: Dog[] = [new Dog()];
printAll(dogs); // OK — safe because printAll never writes

// ✗ Array is mutable — the following is unsound (TypeScript accepts it, but shouldn't)
function addAnimal(animals: Animal[]): void {
  animals.push(new Cat()); // pushes a Cat into what is actually Dog[]
}
addAnimal(dogs); // TypeScript allows this; at runtime dogs[1] is a Cat

// ✓ The correct signature prevents the problem:
function addDog(dogs: Dog[]): void {
  dogs.push(new Dog()); // OK — writes exactly what is promised
}
```

**Lesson**: use `ReadonlyArray<T>` / `readonly T[]` in function parameters that only read from a collection. This makes the parameter safely covariant and documents intent.

## Example B — Contravariant event handler

A handler that can process any `Animal` event is strictly more capable than one that only processes `Dog` events. Contravariance captures this: `Handler<Animal>` is a subtype of `Handler<Dog>`.

```typescript
interface ClickEvent { x: number; y: number }
interface MouseEvent extends ClickEvent { button: number }

// Handler<T> is contravariant in T (T appears only in parameter position)
type Handler<in T> = (event: T) => void;

const genericHandler: Handler<MouseEvent> = (e) =>
  console.log(`button ${e.button} at ${e.x},${e.y}`);

// Narrowing the event type — this is WRONG:
// const clickHandler: Handler<ClickEvent> = genericHandler;
// If called with a plain ClickEvent, accessing e.button would be undefined.

// Widening the event type — this is CORRECT (contravariance):
const widened: Handler<MouseEvent> = (e: MouseEvent) => console.log(e.x);
// Handler<MouseEvent> can be used wherever Handler<MouseEvent> is expected — trivially.

// The real payoff: a handler for the base type substitutes for a handler of the derived type
const baseHandler: Handler<ClickEvent> = (e) => console.log(e.x);
const derivedHandler: Handler<MouseEvent> = baseHandler; // OK — contravariant
// baseHandler accepts ClickEvent; every MouseEvent is a ClickEvent, so this is safe.
```

## Common Type-Checker Errors

### `Type 'X<Dog>' is not assignable to type 'X<Animal>'`

The generic type is **invariant** in that parameter. TypeScript infers invariance when `T` appears in both input and output positions.

```typescript
class MutableBox<T> {
  constructor(private value: T) {}
  get(): T { return this.value; }
  set(v: T) { this.value = v; }
}

const dogBox = new MutableBox(new Dog());
const animalBox: MutableBox<Animal> = dogBox;
// error: Type 'MutableBox<Dog>' is not assignable to type 'MutableBox<Animal>'.
//   Types of property 'set' are incompatible.

// Fix: use a read-only interface for the covariant usage:
interface ReadableBox<out T> { get(): T }
const readable: ReadableBox<Animal> = dogBox; // OK
```

### `Type 'out' modifier cannot appear on a mutable property`

You annotated `out T` but `T` is used in a setter or mutable field.

```typescript
// error:
interface Bad<out T> {
  set(value: T): void; // T in input position — violates 'out'
}

// Fix: remove the setter or change the marker to 'in out':
interface Good<in out T> {
  get(): T;
  set(value: T): void;
}
```

### `Argument of type '(d: Dog) => void' is not assignable to parameter of type '(a: Animal) => void'`

You passed a **narrower-input** callback where a **broader-input** one is required. Function parameters are contravariant under `--strictFunctionTypes`.

```typescript
function applyToAnimal(handler: (a: Animal) => void) {
  handler(new Animal());
}

const dogOnly = (d: Dog) => console.log(d.breed);
applyToAnimal(dogOnly);
// error: Argument of type '(d: Dog) => void' is not assignable to parameter of type
//   '(a: Animal) => void'. Types of parameters 'd' and 'a' are incompatible.
//   Property 'breed' is missing in type 'Animal' but required in type 'Dog'.

// Fix: widen the parameter type
const anyAnimal = (a: Animal) => console.log(a.name);
applyToAnimal(anyAnimal); // OK
```

### Bivariant method vs. contravariant function property

```typescript
interface Bivariant {
  handle(x: Dog): void; // method — bivariant under --strictFunctionTypes
}
interface Contravariant {
  handle: (x: Dog) => void; // property — contravariant under --strictFunctionTypes
}

const animalHandler = { handle: (x: Animal) => {} };
const b: Bivariant = animalHandler;      // OK (bivariant)
const c: Contravariant = animalHandler;  // OK (Animal is wider than Dog — sound)

const dogOnlyHandler = { handle: (x: Dog) => console.log(x.breed) };
const d: Bivariant = dogOnlyHandler;      // OK (bivariant — unsound!)
const e: Contravariant = dogOnlyHandler;  // error — Dog callback can't handle Animal
```

## Coming from JavaScript

JavaScript has no notion of variance — all values are mutable and untyped. TypeScript's variance rules are entirely a static analysis concern; no runtime checks are performed. Understanding variance matters most when designing generic library types intended to be extended or substituted by consumers.

## 7. Use-Case Cross-References

- [-> UC-17](../usecases/UC17-variance.md) Covariant producers and contravariant consumers in generic API design
- [-> UC-04](../usecases/UC04-generic-constraints.md) Combining variance markers with generic bounds for safe substitution

## When to Use It

- **Designing generic producer types**: Mark `out T` when `T` only appears in return positions (e.g., iterators, factories).
- **Designing generic consumer types**: Mark `in T` when `T` only appears in parameter positions (e.g., handlers, callbacks, sinks).
- **Read-only collections**: Use `ReadonlyArray<T>` or `readonly T[]` to enable safe covariance.
- **Event systems / callbacks**: Leverage contravariance for handler hierarchies where a broader handler substitutes for a narrower one.
- **Immutable data structures**: Covariant wrappers for read-only state (e.g., `Record<string, T>`, `Map.Immutable<T>`).

```typescript
// ✓ Use 'out' for pure producers
interface Iterator<out T> {
  next(): T | undefined;
}

// ✓ Use 'in' for pure consumers
interface Sink<in T> {
  write(value: T): void;
}

// ✓ Use readonly arrays for covariant parameters
function processItems(items: readonly Item[]): void { ... }
```

## When Not to Use It

- **Mutable containers**: Do not mark `out` on types that mutate or accept `T` (e.g., `Array`, `Map`, `Set`).
- **Bidirectional access**: When a type both reads and writes `T`, do not use `in` or `out` (use `in out` or no marker).
- **Internal implementation details**: Variance annotations are for public API contracts, not internal classes.
- **When TypeScript version < 4.7**: You cannot use explicit `in`/`out` markers; variance is inferred only.

```typescript
// ✗ Don't mark mutable containers as covariant
interface BadMutableList<out T> {
  get(index: number): T;
  set(index: number, value: T): void; // error: T in parameter position
}

// ✓ Correct: invariant for mutable containers
interface MutableList<in out T> {
  get(index: number): T;
  set(index: number, value: T): void;
}
```

## Antipatterns When Using Variance

### Wrong marker for actual usage

```typescript
// error: 'T' appears in input position but marked 'out'
interface Bad<out T> {
  setValue(t: T): void;
}

// Fix: match annotation to usage
interface Correct<in out T> {
  getValue(): T;
  setValue(t: T): void;
}
```

### Over-constraining with `in out`

```typescript
// ❌ Unnecessary invariance blocks safe assignments
interface UnnecessaryInvariant<in out T> {
  getValue(): T;
}

// OK: DogVal is not assignable to AnimalVal even though safe
const dogVal: UnnecessaryInvariant<Dog> = { getValue: () => new Dog() };
const animalVal: UnnecessaryInvariant<Animal> = dogVal; // error

// ✓ Use 'out' when only reading
interface Correct<out T> {
  getValue(): T;
}
const goodAnimal: Correct<Animal> = { getValue: () => new Dog() }; // OK!
```

### Using variance markers without understanding subtyping

```typescript
// Confusing variance direction: expecting covariance but getting contravariance
type Callback<in T> = (t: T) => void;

const animalCb: Callback<Animal> = (a) => {};
const dogCb: Callback<Dog> = animalCb; // OK (contravariant—opposite of what beginners expect)

// Not the other way:
// const wrong: Callback<Animal> = (d: Dog) => {}; // error
```

## Antipatterns Where Variance Fixes the Code

### Using `any` to bypass variance errors

```typescript
// ❌ Using `any` loses type safety
type BadHandler = (data: any) => void;

// ✓ Correct variance captures the real subtype relationship
type SafeHandler<in T> = (data: T) => void;

// A generic handler can handle specific events
const generic: SafeHandler<Event> = (e) => console.log(e.type);
const clickHandler: SafeHandler<ClickEvent> = generic; // OK!
```

### Manually checking types instead of leveraging variance

```typescript
// ❌ Manual type guards needed due to invariant container
function processData(items: { get(): Data }) {
  const data = items.get();
  if (data instanceof SpecificData) {
    // unsafe: can't treat items.get() as SpecificData consistently
  }
}

// ✓ Covariant producer eliminates guards
interface Producer<out T> {
  get(): T;
}

function processData2(p: Producer<SpecificData>) {
  const data: SpecificData = p.get(); // type is guaranteed!
}
```

### Copying data to match invariant types

```typescript
// ❌ Workaround: copy data just to satisfy type checker
function sum(numbers: Array<number>): number {
  return numbers.reduce((a, b) => a + b, 0);
}

const readonlyNumbers: readonly number[] = [1, 2, 3];
sum([...readonlyNumbers]); // forced copy

// ✓ Accept readonly (covariant) parameter
function sumCorrect(numbers: readonly number[]): number {
  return numbers.reduce((a, b) => a + b, 0);
}

sumCorrect(readonlyNumbers); // no copy needed!
```

### Using wrapper objects to work around invariance

```typescript
// ❌ Creating intermediate wrappers
interface DogReader {
  getDog(): Dog;
}

function takeAnimalReader(r: AnimalReader): void { ... }

// Can't directly pass DogReader even though safe:
// takeAnimalReader({ getDog: () => new Dog() }); // error

// Workaround: create wrapper
const wrapper: AnimalReader = {
  getAnimal: () => ({ getDog: () => new Dog() }).getDog()
};
takeAnimalReader(wrapper);

// ✓ Use variance annotation
interface AnimalReader<out T extends Animal> {
  get(): T;
}

interface DogReaderV2 extends AnimalReader<Dog> {
  get(): Dog;
}

// Now DogReaderV2 < : AnimalReader<Animal>
```

## Source Anchors

- [TypeScript 2.6 release notes — `--strictFunctionTypes`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-2-6.html)
- [TypeScript 4.7 release notes — Explicit variance annotations](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-7.html)
- [TypeScript Handbook — Type Compatibility](https://www.typescriptlang.org/docs/handbook/type-compatibility.html)
- [TypeScript FAQ — Why are function parameters bivariant?](https://github.com/microsoft/TypeScript/wiki/FAQ#why-are-function-parameters-bivariant)
