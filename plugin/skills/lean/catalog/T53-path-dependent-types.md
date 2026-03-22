# Path-Dependent Types (Subsumed by Dependent Types)

> **Since:** Lean 4 (stable) -- dependent types have been foundational since Lean's inception

## What it is

Lean does not need a separate "path-dependent type" feature because its **dependent type system** is strictly more powerful. In Scala, path-dependent types let a type depend on a specific object instance (`x.Inner`). In Lean, any type can depend on any value — function return types, structure fields, and local definitions can all mention previous values in their types. What Scala achieves with path-dependent types is a natural special case of dependent functions and sigma types in Lean.

A structure with a type-valued field is Lean's direct analog of Scala's abstract type member. A sigma type `(x : A) ×' B x` (or the `Sigma` type) packages a value together with a type that depends on it — this is the "existential with path" that Scala encodes via abstract type members and path dependence.

## What constraint it enforces

**Any type can mention any in-scope value. The kernel checks that type-level expressions reduce correctly and rejects mismatches, giving you path-dependent patterns for free — and much more.**

- A function `(k : Key) -> k.ValueType -> Store` has a parameter whose type depends on the previous parameter — exactly path dependence.
- A structure field `data : F n` ties the field type to another field `n : Nat` — the "path" is the structure instance.
- Sigma types `Σ (n : Nat), Vector α n` bundle a value with a type that depends on it, analogous to an existential type member.

## Minimal snippet

```lean
structure Key where
  name : String
  ValueType : Type

def age : Key := { name := "age", ValueType := Nat }
def username : Key := { name := "username", ValueType := String }

-- The second argument's type depends on the first argument's value
def store (k : Key) (v : k.ValueType) : String :=
  s!"Stored {k.name}"

#check store age 30           -- OK: age.ValueType = Nat
#check store username "alice"  -- OK: username.ValueType = String
-- store age "thirty"          -- error: type mismatch, expected Nat, got String
```

## Interaction with other features

| Feature | How it composes |
|---------|-----------------|
| **Dependent types** [-> catalog/T09](T09-dependent-types.md) | Path-dependent types are a special case. T09 covers Pi types `(x : A) -> B x` and indexed families — the general mechanism that makes path dependence trivial. |
| **Type classes** [-> catalog/T05](T05-type-classes.md) | Type classes with `outParam` associated types behave like Rust/Scala associated types. `class Functor (F : Type -> Type)` where `F` is determined by the instance — a form of path dependence. |
| **Record types (structures)** [-> catalog/T31](T31-record-types.md) | Structures with type-valued fields are Lean's equivalent of Scala traits with abstract type members. Each instance carries its own types. |
| **Encapsulation** [-> catalog/T21](T21-encapsulation.md) | `opaque` definitions hide the body of a type-valued field. Clients see the abstract type but not its definition, mirroring Scala's abstract type members. |

## Gotchas and limitations

1. **Definitional vs propositional equality.** The kernel automatically reduces `age.ValueType` to `Nat`, but it will not reduce expressions that require a proof. If two paths are propositionally but not definitionally equal, you need an explicit `rw` or `subst`.

2. **Universe levels.** A structure field of type `Type` lives in `Type 1`. Mixing universe levels in dependent structures can trigger universe-level errors. Use `Type*` or explicit universe polymorphism.

3. **No runtime type dispatch.** Lean's dependent types are erased at runtime. You cannot branch on `k.ValueType` at runtime — the type-level information guides the compiler but vanishes in compiled code. Use `Decidable` instances or explicit tags for runtime dispatch.

4. **Proof obligations propagate.** When a function parameter's type depends on a value, callers must provide values that make the types match. This can create proof obligations that require tactics to discharge.

5. **Opaque definitions block reduction.** If `Key.ValueType` is defined behind `opaque`, the kernel cannot reduce `k.ValueType` to its concrete type. This is intentional for encapsulation but can surprise users expecting transparency.

## Beginner mental model

In Lean, **every function is already path-dependent**. When you write `def f (n : Nat) : Vector String n`, the return type `Vector String n` depends on the parameter `n` — this IS path dependence, except the "path" is just a function argument. Scala needed special syntax (`x.Inner`) to express what Lean does with ordinary function types. Think of Lean's type system as "Scala's path-dependent types, but everywhere and for everything."

## Example A — Structure with type-valued fields (Scala's abstract type members)

```lean
structure Container where
  ElemType : Type
  elements : List ElemType
  default  : ElemType

def intContainer : Container :=
  { ElemType := Nat, elements := [1, 2, 3], default := 0 }

def strContainer : Container :=
  { ElemType := String, elements := ["a", "b"], default := "" }

-- The field type depends on which container you access
#check intContainer.default   -- Nat
#check strContainer.default   -- String

-- intContainer and strContainer carry different types,
-- just like Scala's path-dependent type members.
```

## Example B — Sigma types as existential packages

```lean
-- A sigma type bundles a value with a dependent type
-- This is the "existential type member" pattern from Scala
def SomeContainer := Σ (E : Type), List E × E

def packInts : SomeContainer := ⟨Nat, [1, 2, 3], 0⟩
def packStrs : SomeContainer := ⟨String, ["hello"], ""⟩

-- Unpacking recovers the dependency
def count (c : SomeContainer) : Nat := c.2.1.length

#eval count packInts   -- 3
#eval count packStrs   -- 1
```

## Example C — Dependent function types (the full generalization)

```lean
structure TypedKey where
  name : String
  ValType : Type

def age : TypedKey := ⟨"age", Nat⟩
def email : TypedKey := ⟨"email", String⟩

-- A store that accepts key-dependent values
structure Entry (k : TypedKey) where
  value : k.ValType

def ageEntry : Entry age := ⟨30⟩
def emailEntry : Entry email := ⟨"alice@example.com"⟩

-- The entry type depends on the key — compiler rejects mismatches
-- def badEntry : Entry age := ⟨"thirty"⟩
-- error: type mismatch, expected Nat, got String

-- A function whose argument type depends on the key parameter
def display (k : TypedKey) (v : k.ValType) [ToString k.ValType] : String :=
  s!"{k.name} = {toString v}"

#eval display age 30            -- "age = 30"
#eval display email "alice@x"   -- "email = alice@x"
```

## Example D — Comparison with Scala's Graph pattern

```lean
structure Graph where
  Node : Type
  Edge : Type
  edges : Node -> List Edge
  target : Edge -> Node

def cityGraph : Graph where
  Node := String
  Edge := String × String × Nat
  edges city := [("A", "B", 10)]  -- simplified
  target e := e.2.1

-- Functions parameterized by a specific graph — path dependent
def neighbors (g : Graph) (n : g.Node) : List g.Node :=
  (g.edges n).map g.target

-- The compiler ensures you only pass nodes from the right graph
#check neighbors cityGraph "A"
-- neighbors cityGraph (42 : Nat) would be a type error
```

## Use-case cross-references

- [-> UC-02](../usecases/UC02-domain-modeling.md) -- Dependent structures model domain entities where field types depend on other fields.
- [-> UC-12](../usecases/UC12-compile-time.md) -- Type-level computation through dependent types happens during elaboration, catching errors before runtime.
- [-> UC-10](../usecases/UC10-encapsulation.md) -- Opaque definitions hide type-valued fields, giving clients an abstract type member they cannot inspect.

## Source anchors

- *Theorem Proving in Lean 4* -- Ch. 2 "Dependent Type Theory"
- *Functional Programming in Lean* -- "Structures" and "Dependent Types" sections
- *Lean 4 Reference* -- [Sigma Types](https://lean-lang.org/lean4/doc/expressions/sigma.html)
- *Lean 4 Reference* -- [Structures](https://lean-lang.org/lean4/doc/structures.html)
