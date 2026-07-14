// Not total: returns a bare number. In JS, 1 / 0 is Infinity and 0 / 0 is NaN —
// no error, no signal — so the caller gets a "usable" number and is never
// forced to consider the missing answer; `safeDiv(1, 0) + 1` type-checks.
export function safeDiv(a: number, b: number): number {
  return a / b;
}
