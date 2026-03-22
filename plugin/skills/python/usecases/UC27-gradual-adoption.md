# Gradual Adoption

## The constraint

Incrementally add type safety to an untyped codebase without requiring
all-or-nothing migration — unannotated code must coexist with typed code, and
each module's type coverage can increase independently.

## Feature toolkit

| Feature | Role | Link |
|---|---|---|
| Basic annotations | Entry point: annotate function signatures one at a time | [-> catalog/01](../catalog/T13-null-safety.md) |
| `TypeAlias` / `type` statement | Organize and name complex types for readability | [-> catalog/17](../catalog/T23-type-aliases.md) |
| `Any` / inference / strict mode | Control how much the checker infers vs requires | [-> catalog/20](../catalog/T47-gradual-typing.md) |

## Patterns

### A — Module boundary typing first

Start by annotating public function signatures at module boundaries.
Internal helpers can remain untyped initially — the checker treats them as
`Any` and focuses enforcement on the annotated surfaces.

```python
# payments.py — public API is typed, internals are not

def charge_customer(customer_id: str, amount_cents: int) -> bool:
    """Public API — typed signature, checker enforces callers."""
    record = _build_charge_record(customer_id, amount_cents)  # OK — returns Any
    return _submit_charge(record)                              # OK — Any flows into bool

def _build_charge_record(customer_id, amount_cents):
    """Internal — no annotations yet. Checker treats as Any."""
    return {"id": customer_id, "amount": amount_cents}

def _submit_charge(record):
    """Internal — untyped. Will be annotated in a later pass."""
    return True

# callers.py
from payments import charge_customer

charge_customer("cust_123", 5000)      # OK
charge_customer(123, "five thousand")  # error: int not assignable to str
```

### B — `py.typed` marker and stub files

For libraries, a `py.typed` marker file signals that the package ships type
information. For third-party code, stub files (`.pyi`) add types without
modifying source.

```
# Package layout with py.typed marker:
mypackage/
    __init__.py
    py.typed          # empty file — tells checkers this package is typed
    core.py           # fully annotated source
    legacy.py         # partially annotated — checker handles gracefully

# Stub file for untyped third-party code:
# stubs/thirdparty.pyi
def parse(data: bytes) -> dict[str, str]: ...
def connect(host: str, port: int) -> None: ...
```

```python
# Using the stub — checker sees typed signatures even though
# the actual thirdparty module has no annotations:
import thirdparty

result: dict[str, str] = thirdparty.parse(b"data")   # OK
thirdparty.connect("localhost", "8080")                # error: str not assignable to int
```

### C — `--strict` mode progression

Gradually tighten checker strictness as coverage grows.
Start permissive, then enable stricter flags module by module.

```toml
# pyproject.toml — mypy configuration
[tool.mypy]
# Phase 1: baseline — just catch obvious errors
warn_return_any = false
disallow_untyped_defs = false
check_untyped_defs = true

# Phase 2: require annotations on new code
# disallow_untyped_defs = true          # uncomment when ready

# Phase 3: full strict mode
# strict = true                          # uncomment when fully typed

# Per-module overrides for gradual rollout:
[[tool.mypy.overrides]]
module = "myapp.api.*"
disallow_untyped_defs = true             # API layer is fully typed

[[tool.mypy.overrides]]
module = "myapp.legacy.*"
ignore_errors = true                     # legacy code — not yet migrated
```

```toml
# pyproject.toml — pyright configuration
[tool.pyright]
# Phase 1
typeCheckingMode = "basic"

# Phase 2
# typeCheckingMode = "standard"

# Phase 3
# typeCheckingMode = "strict"
```

### D — `TYPE_CHECKING` for import-only types

Use `typing.TYPE_CHECKING` to import types that are only needed for
annotations — avoiding circular imports and runtime overhead.

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # These imports only exist at check time, not at runtime:
    from myapp.models import User
    from myapp.services import PaymentService

class OrderProcessor:
    def __init__(self, payment: PaymentService) -> None:
        self._payment = payment

    def process(self, user: User, amount: int) -> bool:
        # Checker sees the full types from the conditional import.
        return self._payment.charge(user.id, amount)   # OK

# At runtime, the User and PaymentService imports never execute,
# so circular import chains are broken.
```

## Tradeoffs

| Approach | Strength | Weakness |
|---|---|---|
| Boundary typing | Immediate value at call sites; low effort | Internal bugs remain uncaught until internals are typed |
| `py.typed` + stubs | Types for code you cannot modify; library publishing | Stubs can drift from source; maintenance burden |
| `--strict` progression | Controlled rollout; no big-bang migration | Per-module config can be complex; inconsistent coverage |
| `TYPE_CHECKING` | Breaks circular imports; zero runtime cost | Requires `from __future__ import annotations` or string literals |

## When to use which feature

**Start with boundary typing** on day one. Annotate the public functions of
your most-imported modules. This gives the checker the most leverage for the
least effort — every caller of those functions immediately gets checking.

**Add `py.typed` and stubs** when publishing a typed library, or when you depend
on untyped third-party code. Stubs let you add type information externally
without waiting for upstream changes.

**Progress through strict modes** as team confidence grows. A practical sequence:
1. `check_untyped_defs = true` (catch errors even in unannotated functions)
2. `disallow_untyped_defs = true` per module (require annotations on new code)
3. `strict = true` project-wide (full enforcement)

**Use `TYPE_CHECKING`** from the start in any project with layered architecture.
It prevents circular imports and keeps runtime fast while giving the checker
full type visibility.

### Practical migration strategy

1. **Install a checker** (`mypy` or `pyright`) with default/basic settings.
2. **Run on CI** with `--warn-unused-ignores` so suppressions do not accumulate.
3. **Annotate boundaries** of 3-5 core modules. Fix the errors this surfaces.
4. **Enable `disallow_untyped_defs`** on those modules.
5. **Expand outward**: repeat steps 3-4 for the next ring of modules.
6. **Enable `strict`** project-wide when untyped modules are below ~10%.

## Source anchors

- [PEP 484 — Gradual typing](https://peps.python.org/pep-0484/#gradual-typing)
- [PEP 561 — py.typed and stub packages](https://peps.python.org/pep-0561/)
- [mypy docs: Existing codebase](https://mypy.readthedocs.io/en/stable/existing_code.html)
- [mypy docs: Configuration file](https://mypy.readthedocs.io/en/stable/config_file.html)
- [pyright docs: Configuration](https://microsoft.github.io/pyright/#/configuration)
- [typing spec: Gradual types](https://typing.readthedocs.io/en/latest/spec/concepts.html#gradual-types)
