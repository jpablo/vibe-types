# Serialization (Limited Built-in Support)

## The constraint

Convert values to and from external representations (strings, JSON, binary). Lean 4 has limited built-in serialization support -- `Repr`, `ToString`, and `Lean.Json` cover basic needs, but there is no general-purpose `Serialize`/`Deserialize` framework comparable to Rust's serde or Haskell's aeson. Custom serializers fill the gap.

## Feature toolkit

- [-> T06-derivation](../catalog/T06-derivation.md) -- `deriving Repr, BEq, Hashable` for automatic instance generation.
- [-> T05-type-classes](../catalog/T05-type-classes.md) -- `ToString`, `Repr`, `FromJson`, `ToJson` as type-class interfaces.
- [-> T31-record-types](../catalog/T31-record-types.md) -- Structures provide the named-field shape that serializers traverse.
- [-> T01-algebraic-data-types](../catalog/T01-algebraic-data-types.md) -- Inductive types require variant-aware serialization.

## Patterns

### Pattern A -- Repr and ToString for display

`Repr` produces a Lean-syntax representation (for `#eval` output). `ToString` produces a human-readable string. Both can be derived.

```lean
structure Point where
  x : Float
  y : Float
  deriving Repr

#eval Point.mk 1.0 2.0   -- { x := 1.000000, y := 2.000000 }

instance : ToString Point where
  toString p := s!"({p.x}, {p.y})"

#eval s!"{Point.mk 1.0 2.0}"   -- "(1.000000, 2.000000)"
```

### Pattern B -- Lean.Json for JSON serialization

Lean ships with `Lean.Json` and the `FromJson`/`ToJson` type classes. Derive them for structures.

```lean
import Lean.Data.Json

structure Config where
  host : String
  port : Nat
  ssl  : Bool
  deriving Lean.FromJson, Lean.ToJson

def example : IO Unit := do
  let cfg := Config.mk "localhost" 8080 false
  let json := Lean.toJson cfg
  IO.println (toString json)
  -- {"host":"localhost","port":8080,"ssl":false}

  match Lean.Json.parse "{\"host\":\"x\",\"port\":443,\"ssl\":true}" with
  | .ok j =>
    match Lean.fromJson? j (α := Config) with
    | .ok c  => IO.println s!"parsed: {c.host}:{c.port}"
    | .error e => IO.println s!"decode error: {e}"
  | .error e => IO.println s!"parse error: {e}"
```

### Pattern C -- Custom serializers for inductive types

For inductive types (sum types), write explicit `ToJson`/`FromJson` instances.

```lean
import Lean.Data.Json

inductive Status where
  | active
  | suspended (reason : String)
  | deleted

instance : Lean.ToJson Status where
  toJson
    | .active        => Lean.Json.mkObj [("tag", "active")]
    | .suspended r   => Lean.Json.mkObj [("tag", "suspended"), ("reason", r)]
    | .deleted       => Lean.Json.mkObj [("tag", "deleted")]

instance : Lean.FromJson Status where
  fromJson? j := do
    let tag ← j.getObjValAs? String "tag"
    match tag with
    | "active"    => return .active
    | "suspended" => return .suspended (← j.getObjValAs? String "reason")
    | "deleted"   => return .deleted
    | other       => throw s!"unknown tag: {other}"
```

### Pattern D -- Binary-style serialization via ByteArray

For compact representations, serialize to `ByteArray` with manual encode/decode functions.

```lean
structure Header where
  version : UInt8
  length  : UInt32

def Header.encode (h : Header) : ByteArray :=
  let buf := ByteArray.mkEmpty 5
  let buf := buf.push h.version
  let buf := buf.append (ByteArray.mk #[
    (h.length >>> 24).toUInt8,
    (h.length >>> 16).toUInt8,
    (h.length >>> 8).toUInt8,
    h.length.toUInt8
  ])
  buf

def Header.decode (bs : ByteArray) : Option Header := do
  guard (bs.size >= 5)
  let version := bs.get! 0
  let length := (bs.get! 1).toUInt32 <<< 24
    ||| (bs.get! 2).toUInt32 <<< 16
    ||| (bs.get! 3).toUInt32 <<< 8
    ||| (bs.get! 4).toUInt32
  return { version, length }
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| `Repr` / `ToString` | Trivial to derive; good for debugging | Not round-trippable; not a serialization format |
| `Lean.Json` | Ships with Lean; derivable for structures | No automatic derivation for sum types; limited format options |
| Custom serializers | Full control over format and error handling | Boilerplate; manual sync between encode and decode |
| `ByteArray` | Compact; suitable for binary protocols | Entirely manual; no schema evolution support |

## When to use which feature

- **Debugging and REPL output** -> `deriving Repr` and custom `ToString`.
- **JSON APIs and config files** -> `Lean.Json` with `FromJson`/`ToJson`.
- **Sum types** -> manual `ToJson`/`FromJson` instances with a tag field.
- **Binary protocols** -> manual `ByteArray` encode/decode; consider a codec combinator library if complexity grows.
- **Production serialization needs** -> evaluate community libraries (e.g., `Aesop`, `ProtoLean`) as the ecosystem matures.

## Source anchors

- Lean 4 source: `Lean.Data.Json`, `Lean.Data.Json.FromToJson`
- *Functional Programming in Lean* -- "Type Classes" (Repr, ToString)
