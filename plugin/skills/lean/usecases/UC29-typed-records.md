# Typed Records

## The constraint

Represent structured data with named, typed fields. Lean 4 structures provide named fields, dot-notation access, inheritance via `extends`, and a dedicated update syntax for functional modifications -- all checked at compile time.

## Feature toolkit

- [-> T31-record-types](../catalog/T31-record-types.md) -- Structures with named fields, default values, and update syntax.
- [-> T06-derivation](../catalog/T06-derivation.md) -- `deriving Repr, BEq, Hashable` for automatic instance generation on structures.
- [-> T09-dependent-types](../catalog/T09-dependent-types.md) -- Structure fields can depend on other fields' values.
- [-> T21-encapsulation](../catalog/T21-encapsulation.md) -- `private` fields and opaque definitions for controlled access.

## Patterns

### Pattern A -- Basic structure with named fields

Define a structure with named, typed fields. Access via dot notation; construction via named arguments.

```lean
structure User where
  name   : String
  age    : Nat
  active : Bool

def alice : User := { name := "Alice", age := 30, active := true }

-- Typed field access:
#eval alice.name      -- "Alice"
#eval alice.age       -- 30

-- Pattern matching:
def greet (u : User) : String :=
  match u with
  | { name, active := true, .. } => s!"Hello, {name}!"
  | { name, .. }                 => s!"{name} is inactive"
```

### Pattern B -- Functional updates with structure update syntax

Use `{ s with field := newVal }` to create a new structure with selected fields changed. The original is untouched.

```lean
structure Config where
  host       : String
  port       : Nat
  ssl        : Bool
  maxRetries : Nat

def devConfig : Config :=
  { host := "localhost", port := 8080, ssl := false, maxRetries := 0 }

def prodConfig : Config :=
  { devConfig with host := "prod.example.com", ssl := true, maxRetries := 3 }

-- devConfig is unchanged:
#eval devConfig.host    -- "localhost"
#eval prodConfig.ssl    -- true
```

### Pattern C -- Inheritance with extends

Structures can extend other structures, inheriting all fields. This provides composition without subtype polymorphism.

```lean
structure Named where
  name : String

structure Aged where
  age : Nat

structure Person extends Named, Aged where
  email : String

def bob : Person :=
  { name := "Bob", age := 25, email := "bob@example.com" }

-- Access inherited fields directly:
#eval bob.name    -- "Bob"
#eval bob.age     -- 25
#eval bob.email   -- "bob@example.com"

-- Upcast to parent structure:
#eval bob.toNamed   -- { name := "Bob" }
```

### Pattern D -- Default field values

Provide defaults for fields that have a natural "zero" value. Callers can override or accept the default.

```lean
structure HttpRequest where
  method  : String := "GET"
  path    : String
  headers : List (String × String) := []
  body    : Option String := none

def simple : HttpRequest :=
  { path := "/api/health" }
-- method = "GET", headers = [], body = none — all defaults

def post : HttpRequest :=
  { method := "POST", path := "/api/data", body := some "{\"key\":1}" }
```

### Pattern E -- Dependent fields

Structure fields can depend on earlier fields, encoding invariants directly in the record type.

```lean
structure SizedArray (α : Type) where
  data : Array α
  size_eq : data.size = n

-- Or more idiomatically with a parameter:
structure BoundedList (α : Type) (max : Nat) where
  items : List α
  bounded : items.length ≤ max

def example : BoundedList Nat 3 :=
  { items := [1, 2], bounded := by simp }

-- Cannot construct with too many elements:
-- def bad : BoundedList Nat 2 :=
--   { items := [1, 2, 3], bounded := by simp }   -- simp can't prove 3 ≤ 2
```

### Pattern F -- Deriving instances from structure shape

Use `deriving` to auto-generate type class instances.

```lean
structure Point where
  x : Float
  y : Float
  deriving Repr, BEq, Inhabited

#eval Point.mk 1.0 2.0           -- { x := 1.000000, y := 2.000000 }
#eval Point.mk 1.0 2.0 == Point.mk 1.0 2.0   -- true
#eval (default : Point)           -- { x := 0.000000, y := 0.000000 }
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Named fields | Self-documenting; typed access; pattern matching | More ceremony than tuples for throwaway data |
| Update syntax | Immutable and concise | Deep nesting requires chained updates |
| `extends` | Reuses fields across structures; no duplication | Not subtype polymorphism; `extends` creates coercion functions |
| Default values | Reduces boilerplate at construction sites | Defaults may hide required-but-forgotten fields |
| Dependent fields | Compiler-enforced invariants in the record itself | Proof obligations at every construction site |

## When to use which feature

- **Domain entities** (users, configs, events) -> structures with named fields. This is the default.
- **Incremental modification** -> structure update syntax (`{ s with ... }`).
- **Shared field groups** (auditing fields, metadata) -> `extends` to compose structures.
- **Optional or defaultable fields** -> default values in the structure definition.
- **Invariant-carrying records** (sized containers, validated data) -> dependent fields with proof terms.

## Source anchors

- *Functional Programming in Lean* -- "Structures"
- *Theorem Proving in Lean 4* -- Ch. 9 "Structures and Records"
- Lean 4 source: `Init.Prelude` (structure syntax)
