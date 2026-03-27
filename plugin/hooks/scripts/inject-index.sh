#!/usr/bin/env bash
# Detect project language and inject the matching vibe-types quick index.
# Runs as a SessionStart hook — outputs JSON with additionalContext.

set -euo pipefail

langs=()

# Detect languages from files in the working directory
if compgen -G "*.py" >/dev/null 2>&1 || [ -f pyproject.toml ] || [ -f setup.py ]; then
  langs+=(python)
fi
if [ -f Cargo.toml ] || compgen -G "*.rs" >/dev/null 2>&1; then
  langs+=(rust)
fi
if [ -f lakefile.lean ] || compgen -G "*.lean" >/dev/null 2>&1; then
  langs+=(lean)
fi
if [ -f build.sbt ] || [ -f build.sc ] || compgen -G "*.scala" >/dev/null 2>&1; then
  langs+=(scala3)
fi

# If no language detected, exit silently (no context to inject)
if [ ${#langs[@]} -eq 0 ]; then
  exit 0
fi

# --- Snippet definitions (one per language) ---

read -r -d '' PYTHON_SNIPPET << 'PYEOF' || true
## Python type-safety quick index (vibe-types)
- Basic annotations & None handling: enforce types on params/returns; require None checks → `T13-null-safety`
- Union & Literal types: restrict values to declared alternatives; Literal for exact values → `T02-union-intersection`
- TypedDict: enforce dict key names, value types, and required/optional presence → `T31-record-types`
- Protocol (structural subtyping): static duck typing — verify method/attr presence without inheritance → `T07-structural-typing`
- Generics & TypeVar: preserve type relationships; bounds restrict acceptable types → `T04-generics-bounds`
- ParamSpec: preserve function signatures through decorators → `T45-paramspec-variadic`
- TypeGuard & TypeIs: custom narrowing functions; exhaustive branch handling → `T14-type-narrowing`
- Final & frozen dataclass: prevent reassignment, override, and mutation → `T32-immutability-markers`, `T06-derivation`
- Preventing invalid states: enums, Literal, NewType, Union — make invalid states unrepresentable → `UC01-invalid-states`
- Gradual adoption: add types incrementally; --strict mode; py.typed marker → `UC27-gradual-adoption`
PYEOF

read -r -d '' RUST_SNIPPET << 'RSEOF' || true
## Rust type-safety quick index (vibe-types)
- Ownership & moves: prevent use-after-free, double-free → `T10-ownership-moves`
- Borrowing & lifetimes: prevent data races, dangling references → `T11-borrowing-mutability`, `T48-lifetimes`
- Enums + exhaustive match: force handling all variants; make invalid states unrepresentable → `T01-algebraic-data-types`
- Newtypes: prevent mixing up same-typed values (UserId vs OrderId) → `T03-newtypes-opaque`
- Traits as bounds: constrain generic APIs to required capabilities → `T04-generics-bounds`, `T05-type-classes`
- Send/Sync: enforce thread-safety at compile time → `T50-send-sync`
- Const generics: encode sizes/dimensions/capacities in types → `T15-const-generics`
- Typestate & phantom types: make invalid state transitions unrepresentable → `UC01-invalid-states`
- Ownership-safe APIs: encode resource lifecycle in signatures → `UC20-ownership-apis`
- Value-level invariants: encode lengths/shapes in types to catch mismatches → `UC18-type-arithmetic`
RSEOF

read -r -d '' LEAN_SNIPPET << 'LNEOF' || true
## Lean 4 type-safety quick index (vibe-types)
- Inductive types & pattern matching: closed variants with exhaustive matching → `T01-algebraic-data-types`
- Dependent types & Pi types: types depend on values; compiler checks index consistency → `T09-dependent-types`
- Propositions as types (Prop): encode invariants; compiler requires proof terms → `T29-propositions-as-types`
- Subtypes & refinement types: attach predicates to types; construction requires proof → `T26-refinement-types`
- Termination checking: every recursive function must provably terminate → `T28-termination`
- Type classes & instances: constrain generic code to types with required capabilities → `T05-type-classes`
- Monads & IO: side effects tracked in the type; pure code cannot perform IO → `T12-effect-tracking`
- Proof automation (simp, omega, decide): automate proof obligations at construction sites → `T30-proof-automation`
- Preventing invalid states: inductive types, subtypes, dependent types → `UC01-invalid-states`
- Domain modeling: model domain invariants as type-level constraints → `UC02-domain-modeling`
LNEOF

read -r -d '' SCALA3_SNIPPET << 'SCEOF' || true
## Scala 3 type-safety quick index (vibe-types)
- Opaque types: zero-cost distinct types; prevent value mix-ups without boxing → `T03-newtypes-opaque`
- Enums, ADTs, GADTs: closed variants with exhaustive matching; per-branch type refinement → `T01-algebraic-data-types`
- Union & intersection types: type-safe alternatives without class hierarchies → `T02-union-intersection`
- Givens & using clauses: type-class dispatch; compiler supplies evidence automatically → `T05-type-classes`
- Match types: compute types from types; type-level conditional logic → `T41-match-types`
- Inline + compiletime: move checks and branching to compile time → `T16-compile-time-ops`
- Capture checking & CanThrow: track effects and capabilities at type level → `T12-effect-tracking`
- Preventing invalid states: ADTs, opaque types, phantom types, GADTs → `UC01-invalid-states`
- Protocol & state machines: enforce valid call ordering at compile time → `UC13-state-machines`
- DSL & builder patterns: type-safe DSLs where invalid compositions are compile errors → `UC09-builder-config`
SCEOF

# --- Build combined context string ---

context=""
sep=""
for lang in "${langs[@]}"; do
  snippet=""
  case "$lang" in
    python) snippet="$PYTHON_SNIPPET" ;;
    rust)   snippet="$RUST_SNIPPET" ;;
    lean)   snippet="$LEAN_SNIPPET" ;;
    scala3) snippet="$SCALA3_SNIPPET" ;;
  esac
  context+="${sep}${snippet}"
  sep=$'\n\n'
done

# Build JSON using python for reliable escaping (available on all target platforms)
python3 -c "
import json, sys
ctx = sys.stdin.read()
ctx += '\n\nWhen a topic ID is referenced (e.g. T13-null-safety), read the full guide from the vibe-types plugin skill catalog for detailed patterns and examples.'
print(json.dumps({
  'hookSpecificOutput': {
    'hookEventName': 'SessionStart',
    'additionalContext': ctx
  }
}, indent=2))
" <<< "$context"

exit 0
