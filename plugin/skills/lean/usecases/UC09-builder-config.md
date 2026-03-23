# Configuration and Builder Patterns

## The constraint

Define configuration with sensible defaults, ensure required fields are populated, and let callers override only what they need. Lean's structures with default values, `Inhabited` derivation, and partial field application replace builder patterns from object-oriented languages.

## Feature toolkit

- [→ T31-record-types](../catalog/T31-record-types.md) — Structures with default field values and field update syntax.
- [→ T05-type-classes](../catalog/T05-type-classes.md) — `Inhabited` and `default` provide zero-value construction.
- [→ T18-conversions-coercions](../catalog/T18-conversions-coercions.md) — Coercions between configuration types for layered defaults.

## Patterns

### Pattern A — Structures with default values

Lean structures support default field values. Callers specify only the fields they want to override.

```lean
structure ServerConfig where
  host     : String := "localhost"
  port     : Nat    := 8080
  maxConns : Nat    := 100
  logLevel : String := "info"

-- Override only what you need:
def devConfig : ServerConfig :=
  { port := 3000, logLevel := "debug" }

def prodConfig : ServerConfig :=
  { host := "0.0.0.0", maxConns := 10000 }

-- All defaults:
def defaultConfig : ServerConfig := {}
```

### Pattern B — Nested configuration with structure update

Use `{ base with field := newValue }` to derive new configs from existing ones.

```lean
structure DbConfig where
  host    : String := "localhost"
  port    : Nat    := 5432
  dbName  : String := "app"
  poolSize : Nat   := 10

structure AppConfig where
  server : ServerConfig := {}
  db     : DbConfig     := {}
  debug  : Bool         := false

def staging : AppConfig :=
  { server := { host := "staging.example.com" }
    db     := { dbName := "app_staging", poolSize := 5 }
    debug  := true }

-- Tweak from an existing config:
def stagingHighPool : AppConfig :=
  { staging with db := { staging.db with poolSize := 50 } }
```

### Pattern C — Inhabited for default instances

`Inhabited` provides a canonical `default` value. Deriving it gives you zero-argument construction.

```lean
structure Retry where
  maxAttempts : Nat := 3
  backoffMs   : Nat := 100
  deriving Inhabited

-- Use default anywhere an instance is needed:
def withRetry (cfg : Retry := default) (action : IO α) : IO α := do
  let mut attempts := 0
  let mut lastErr : Option IO.Error := none
  while attempts < cfg.maxAttempts do
    try
      return ← action
    catch
      | e =>
        lastErr := some e
        attempts := attempts + 1
  throw (lastErr.getD (IO.userError "retry exhausted"))

-- Caller can omit the config entirely:
-- withRetry (action := someIOAction)
-- Or override specific fields:
-- withRetry { maxAttempts := 5 } someIOAction
```

### Pattern D — Validated configuration

Combine default values with validation to ensure configs are well-formed at construction time.

```lean
structure ListenConfig where
  host : String
  port : Nat
  deriving Repr

def mkListenConfig (host : String := "localhost") (port : Nat := 8080)
    : Except String ListenConfig :=
  if port == 0 || port ≥ 65536 then
    .error s!"invalid port: {port}"
  else if host.isEmpty then
    .error "host cannot be empty"
  else
    .ok { host, port }

-- Smart constructor with defaults + validation:
-- mkListenConfig              → .ok { host := "localhost", port := 8080 }
-- mkListenConfig (port := 0)  → .error "invalid port: 0"
```

### Pattern E — Partial application of structure fields

Use functions with default arguments to simulate builder-style partial application.

```lean
def configureLogger
    (level : String := "info")
    (format : String := "json")
    (output : String := "stdout") : String :=
  s!"Logger(level={level}, format={format}, output={output})"

-- Partial application:
def debugLogger := configureLogger (level := "debug")
def fileLogger := configureLogger (output := "/var/log/app.log")
```

## Tradeoffs

| Pattern | Strength | Weakness |
|---------|----------|----------|
| Default field values | Zero boilerplate; familiar syntax | No validation at construction time |
| Structure update | Derives new configs concisely | Deep nesting can be verbose |
| `Inhabited` / `default` | Canonical default; works with type-class dispatch | Only one default per type |
| Validated constructors | Catches bad configs early | Extra wrapper (`Except`) at every construction site |

## When to use which feature

- **Simple configurations** → structures with default values (Pattern A).
- **Layered or environment-specific configs** → structure update syntax (Pattern B).
- **Library APIs that need a "zero config" option** → derive `Inhabited` (Pattern C).
- **Configs with invariants** (valid ports, non-empty strings) → validated constructors (Pattern D).
- **Functional builder style** → functions with named default arguments (Pattern E).

## Source anchors

- *Functional Programming in Lean* — "Structures"
- *Theorem Proving in Lean 4* — Ch. 6 "Structures and Records"
