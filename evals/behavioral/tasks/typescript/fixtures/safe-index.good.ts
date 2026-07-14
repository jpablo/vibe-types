// Total: out-of-bounds is widened into `number | undefined`, so the caller
// must handle the missing element. `get(v, 99) + 1` does not type-check
// (the operand is possibly undefined).
export function get(items: number[], index: number): number | undefined {
  return index >= 0 && index < items.length ? items[index] : undefined;
}
