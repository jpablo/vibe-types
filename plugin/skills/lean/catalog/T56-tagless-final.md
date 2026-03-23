# Tagless Final (via Type Class Abstraction)

> **Since:** Lean 4 (stable)

## What it is

Lean does not use the term "tagless final," but the same pattern — defining abstract interfaces as type classes and providing different implementations — is native to the language. You define a **type class** with operations parameterized by a monad `m`, write programs constrained by that class, and swap implementations by providing different instances. This achieves the same separation of description from execution that tagless final provides in Scala.

In Lean, this is simply **polymorphic programming with type classes**. A class like `class Console (m : Type → Type)` declares operations (`readLine`, `printLine`). Generic functions constrained by `[Console m] [Monad m]` work over any monad that provides those operations. For production, `m = IO`; for testing, `m` can be a pure state monad.

Lean's metaprogramming stack is itself an example: `MetaM`, `TermElabM`, and `TacticM` are monads with different capabilities exposed through type classes like `MonadMCtx`, `MonadEnv`, and `MonadLCtx`.

## What constraint it enforces

**Functions constrained by type-class bounds can only use the operations declared in those classes. The compiler rejects any direct use of concrete monad operations not provided by the class, ensuring the code is truly polymorphic over the implementation.**

## Minimal snippet

```lean
class Console (m : Type → Type) where
  readLine : m String
  printLine : String → m Unit

def greet [Monad m] [Console m] : m Unit := do
  Console.printLine "What is your name?"
  let name ← Console.readLine
  Console.printLine s!"Hello, {name}!"

-- Production: instance for IO
instance : Console IO where
  readLine := IO.getStdin >>= (·.getLine)
  printLine := IO.println
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Type classes** [-> T05](T05-type-classes.md) | Algebras are type classes. Interpreters are instances. Instance resolution wires the correct implementation automatically. |
| **Functor/Applicative/Monad** [-> T54](T54-functor-applicative-monad.md) | Programs require `[Monad m]` alongside the algebra class, enabling `do`-notation for sequencing operations. |
| **Monad transformers** [-> T55](T55-monad-transformers.md) | Interpreters can target transformer stacks. `MonadLift` lifts inner operations through the stack. |
| **Dependent types** [-> T09](T09-dependent-types.md) | Type-class methods can have dependent signatures, enabling algebras where return types depend on input values — something impossible in most tagless final encodings. |
| **Scoped instances** | `scoped instance` limits an interpreter's visibility to the current namespace, enabling different interpretations in different modules without global conflicts. |

## Gotchas and limitations

1. **Not a named pattern in Lean.** The Lean community does not use the term "tagless final." If you search Lean documentation for it, you will find nothing. The concept is simply "programming with type classes and monadic abstraction."

2. **Instance coherence.** Lean has no orphan rules. Multiple instances of the same class for the same monad can coexist, leading to ambiguity. Use `scoped instance` or explicit instance arguments (`@`) to control which interpretation is used.

3. **No `FunctionK` / natural transformations.** Lean does not have a standard `~>` (natural transformation) type. If you need to transform between interpreters, you define the mapping manually.

4. **Universes can complicate things.** When type-class methods return types in different universes, universe unification errors can arise. Annotate universe levels explicitly when this happens.

5. **Performance.** Type-class dispatch in Lean is resolved at elaboration time and compiled to direct calls in most cases, so overhead is minimal. However, very polymorphic code may inhibit some optimizations.

## Beginner mental model

Think of a type class as a **contract** and an instance as a **vendor** fulfilling that contract. Your program is written against the contract: "I need something that can read lines and print lines." For production, the IO vendor fulfills the contract using real console I/O. For testing, a mock vendor uses a list of scripted inputs. The program does not know or care which vendor is active — it just calls the contract's operations.

Coming from Scala: replace `trait Algebra[F[_]]` with `class Algebra (m : Type → Type)`, and `given` instances with Lean `instance` declarations. The pattern is identical; only the syntax differs.

## Example A -- Testable logging

```lean
class Logger (m : Type → Type) where
  logInfo  : String → m Unit
  logError : String → m Unit

-- Production: log to IO
instance : Logger IO where
  logInfo msg  := IO.println s!"[INFO] {msg}"
  logError msg := IO.eprintln s!"[ERROR] {msg}"

-- Test: accumulate logs in StateT
instance : Logger (StateT (List String) Id) where
  logInfo msg  := modify (· ++ [s!"[INFO] {msg}"])
  logError msg := modify (· ++ [s!"[ERROR] {msg}"])

def processItem [Monad m] [Logger m] (item : String) : m Unit := do
  Logger.logInfo s!"Processing {item}"
  if item == "bad" then
    Logger.logError s!"Bad item: {item}"
  else
    Logger.logInfo s!"Item OK: {item}"

-- Test:
-- (processItem "good" |>.run []).snd == ["[INFO] Processing good", "[INFO] Item OK: good"]
```

## Example B -- Abstract repository pattern

```lean
class UserRepo (m : Type → Type) where
  findUser : Nat → m (Option String)
  saveUser : Nat → String → m Unit

def renameUser [Monad m] [UserRepo m] [Logger m] (id : Nat) (newName : String) : m Bool := do
  match ← UserRepo.findUser id with
  | none =>
    Logger.logError s!"User {id} not found"
    pure false
  | some oldName =>
    Logger.logInfo s!"Renaming {oldName} to {newName}"
    UserRepo.saveUser id newName
    pure true
```

## Use-case cross-references

- [-> UC-01](../usecases/UC01-invalid-states.md) -- Type-class constraints ensure only valid operations are available in each context.
- [-> UC-04](../usecases/UC04-generic-constraints.md) -- Multiple class constraints express the exact capabilities required by a function.
- [-> UC-11](../usecases/UC11-effect-tracking.md) -- The type-class bounds in the signature reveal which effects a computation may perform.

## Source anchors

- *Functional Programming in Lean* -- "Type Classes" and "Monads" chapters
- *Theorem Proving in Lean 4* -- Ch. 10 "Type Classes"
- Lean 4 source: `Init.Prelude` (Monad class definition)
- Lean 4 source: `Lean.Elab.Term` (TermElabM as example of class-based abstraction)
