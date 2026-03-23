# Extensibility

## The constraint

Design extension points so that new behavior can be added without modifying existing code. Type classes serve as the primary extensibility mechanism, with scoped and open instances controlling where and how extensions take effect.

## Feature toolkit

- [→ T05-type-classes](../catalog/T05-type-classes.md) — Type classes define overridable behavior; instance resolution extends them retroactively.
- [→ T39-notation-attributes](../catalog/T39-notation-attributes.md) — `scoped instance` limits visibility; attributes control resolution behavior.
- [→ T18-conversions-coercions](../catalog/T18-conversions-coercions.md) — Coercions provide automatic conversions at extension boundaries.

## Patterns

### Pattern A — Type classes as extension points

Define a type class for the extensible behavior. New types participate by providing instances, without modifying the original definition.

```lean
class Render (α : Type) where
  render : α → String

instance : Render Nat where
  render n := toString n

instance : Render Bool where
  render | true => "yes" | false => "no"

-- Third-party type gains Render without modifying its source:
structure Point where x : Float; y : Float

instance : Render Point where
  render p := s!"({p.x}, {p.y})"

-- Generic code works with any Render instance:
def renderAll [Render α] (xs : List α) : String :=
  String.intercalate ", " (xs.map Render.render)
```

### Pattern B — Scoped instances for controlled extension

`scoped instance` limits an instance's visibility to the enclosing namespace. This prevents global pollution and lets different modules provide different behavior for the same type.

```lean
namespace JsonFormat

scoped instance : Render Point where
  render p := s!"\{\"x\": {p.x}, \"y\": {p.y}}"

end JsonFormat

namespace HumanFormat

scoped instance : Render Point where
  render p := s!"Point at ({p.x}, {p.y})"

end HumanFormat

-- Default instance is used unless a namespace is opened:
-- open JsonFormat → render uses JSON format
-- open HumanFormat → render uses human-readable format
```

### Pattern C — Class hierarchy for layered extension

Use `extends` to build type-class hierarchies. Providing a more specific instance automatically satisfies the parent class constraints.

```lean
class Encode (α : Type) where
  encode : α → ByteArray

class Codec (α : Type) extends Encode α where
  decode : ByteArray → Except String α

-- Providing Codec also gives Encode:
instance : Codec Nat where
  encode n := sorry   -- implementation
  decode bs := sorry

-- Functions requiring only Encode accept Codec instances:
def store [Encode α] (x : α) : IO Unit :=
  let bytes := Encode.encode x
  IO.println s!"stored {bytes.size} bytes"
```

### Pattern D — Default method implementations

Type classes can provide default implementations. Instances only need to override what they specialize.

```lean
class Pretty (α : Type) where
  pretty : α → String
  prettyList : List α → String := fun xs =>
    "[" ++ String.intercalate ", " (xs.map pretty) ++ "]"

instance : Pretty Nat where
  pretty := toString

-- prettyList gets the default behavior:
#eval Pretty.prettyList [1, 2, 3]  -- "[1, 2, 3]"

-- Override the default when needed:
instance : Pretty Char where
  pretty c := toString c
  prettyList cs := String.mk cs   -- "abc" instead of "[a, b, c]"
```

### Pattern E — Open instances for plugin-style extension

Instances defined at the top level (non-scoped) act as open extensions. Any module that imports them gains the behavior. This enables a plugin-style architecture.

```lean
-- Core library defines the class:
class Plugin (α : Type) where
  name : String
  run : α → IO Unit

-- Plugin A (in its own module):
structure LogPlugin where
  level : String

instance : Plugin LogPlugin where
  name := "logger"
  run lp := IO.println s!"[{lp.level}] plugin active"

-- Plugin B (in another module):
structure MetricsPlugin where
  endpoint : String

instance : Plugin MetricsPlugin where
  name := "metrics"
  run mp := IO.println s!"reporting to {mp.endpoint}"

-- Core can work with any plugin generically:
def activate [Plugin α] (p : α) : IO Unit := do
  IO.println s!"activating: {Plugin.name (α := α)}"
  Plugin.run p
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Type classes | Retroactive; no modification of existing types | Global instances can conflict |
| Scoped instances | No pollution; multiple interpretations coexist | Requires explicit `open` at use sites |
| Class hierarchy | Reuse; subclass provides superclass automatically | Deep hierarchies slow instance resolution |
| Default methods | Less boilerplate for instance authors | Defaults may not be obvious to readers |
| Open instances | Plugin architecture; decentralized extension | Risk of orphan instance conflicts |

## When to use which feature

- **Retroactive behavior on third-party types** → type class + instance (Pattern A).
- **Context-dependent behavior** (JSON vs human-readable rendering) → scoped instances (Pattern B).
- **Algebraic structure hierarchies** (semigroup/monoid/group) → class hierarchy with `extends` (Pattern C).
- **Reducing boilerplate** for common instance patterns → default method implementations (Pattern D).
- **Plugin architectures** where modules contribute independently → open instances (Pattern E).

## Source anchors

- *Functional Programming in Lean* — "Type Classes"
- *Theorem Proving in Lean 4* — Ch. 10 "Type Classes"
