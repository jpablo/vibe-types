// Not total: indexes directly and claims a bare number. Out of bounds yields
// undefined at runtime, but the type never says so, so `get(v, 99) + 1`
// type-checks — the invariant is not in the types. (Compiles under the L2
// flags: vanilla --strict without --noUncheckedIndexedAccess; see score.py.)
export function get(items: number[], index: number): number {
  return items[index];
}
