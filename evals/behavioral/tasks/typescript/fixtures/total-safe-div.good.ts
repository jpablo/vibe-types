// Total: the output is widened to include undefined, so "no answer" (b === 0)
// becomes a case the caller must handle. `safeDiv(1, 0) + 1` does not
// type-check (the operand is possibly undefined).
export function safeDiv(a: number, b: number): number | undefined {
  if (b === 0) return undefined;
  return a / b;
}
