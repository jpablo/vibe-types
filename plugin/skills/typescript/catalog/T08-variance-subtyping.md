# Variance & Subtyping

> **Since:** TypeScript 1.x (structural subtyping); `--strictFunctionTypes` since TypeScript 2.6; explicit `in`/`out` variance markers since TypeScript 4.7

## 1. What It Is

**Variance** describes how subtyping relationships on a generic type's type arguments relate to subtyping on the generic type itself. If `Dog extends Animal`, does `Box<Dog>` extend `Box<Animal>`? The answer depends on how `T` is used inside `Box`:

- **Covariant** (`out T`): `Box<Dog>` extends `Box<Animal>`. `T` appears only in output/return positions.
- **Contravariant** (`in T`): `Box<Animal>` extends `Box<Dog>`. `T` appears only in input/parameter positions.
- **Invariant**: neither direction is safe. `T` appears in both positions.
- **Bivariant**: both directions are allowed (unsound; TypeScript's pre-2.6 method behavior).

TypeScript **infers variance** from usage automatically. TypeScript 2.6's `--strictFunctionTypes` made function type parameters contravariant (but method signatures in interfaces/classes remain bivariant for compatibility). TypeScript 4.7 added **explicit variance markers** `out T` and `in T` on type parameters, which both serve as documentation and cause the compiler to verify the annotation matches actual usage.

## 2. What Constraint It Lets You Express

**Control whether a generic type can be used in a more-specific (covariant) or more-general (contravariant) position; catch unsound substitutions at compile time.**

- Marking `out T` prevents `T` from appearing in parameter positions; any attempt to use `T` as an input is a compile error.
- Marking `in T` prevents `T` from appearing in return positions; ensures the generic cannot be used covariantly.
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

const dogProducer: Producer<Dog> = { produce: () => new Dog() };
const animalProducer: Producer<Animal> = dogProducer; // OK — covariant

const animalConsumer: Consumer<Animal> = { consume: (a) => console.log(a.name) };
const dogConsumer: Consumer<Dog> = animalConsumer; // OK — contravariant
```

## 4. Interaction with Other Features

| Feature | How it composes |
|---|---|
| **Generics & Bounds** [-> T04](T04-generics-bounds.md) | Variance is a property of how type parameters are used within generic types; bounds constrain what types may be substituted, variance constrains in which direction substitution is safe. |
| **Interfaces & Structural Contracts** [-> T05](T05-type-classes.md) | Method signatures in interfaces remain bivariant even under `--strictFunctionTypes`; switching to function-property syntax (`method: (x: T) => void`) opts into contravariant checking. |
| **Union & Intersection Types** [-> T02](T02-union-intersection.md) | Union types behave covariantly: if `A extends B`, then `A \| C extends B \| C`. Intersection types are used to express invariant positions by requiring both `in` and `out` usage. |

## 5. Gotchas and Limitations

1. **Mutable arrays are covariant but unsound** — `Dog[]` is assignable to `Animal[]` even though pushing an `Animal` into `dogs` at runtime breaks the `Dog[]` invariant. TypeScript accepts this for pragmatic reasons; use `ReadonlyArray<Dog>` for true safe covariance.
2. **Method signatures remain bivariant** — `{ method(x: Dog): void }` is assignable to `{ method(x: Animal): void }` even under `--strictFunctionTypes`. This is a known soundness gap preserved for compatibility; use function-property syntax to get contravariant checking.
3. **Explicit variance markers are checked but not enforced on callers** — `out T` on a type parameter causes the compiler to verify usage within the type definition, but callers still use the type structurally; the markers do not change assignability rules (they only verify the declaration is consistent).
4. **Inferring variance can be slow** — for large, complex generic types the compiler may fall back to invariant checking to avoid expensive variance inference; explicit markers help performance and correctness.
5. **`in`/`out` markers require TypeScript 4.7+** — older codebases cannot use them; document variance with comments instead.
6. **Variance and `readonly`** — `readonly T[]` is a safe covariant array because the write method is absent; variance and immutability interact closely. Always consider whether a covariant generic should be `Readonly`.

## Coming from JavaScript

JavaScript has no notion of variance — all values are mutable and untyped. TypeScript's variance rules are entirely a static analysis concern; no runtime checks are performed. Understanding variance matters most when designing generic library types intended to be extended or substituted by consumers.

## 6. Use-Case Cross-References

- [-> UC-17](../usecases/UC17-variance.md) Covariant producers and contravariant consumers in generic API design
- [-> UC-04](../usecases/UC04-generic-constraints.md) Combining variance markers with generic bounds for safe substitution
