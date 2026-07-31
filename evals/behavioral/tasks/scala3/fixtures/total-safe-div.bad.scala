// Not total: returns a bare Int, inventing 0 for the b == 0 case. The caller
// gets a usable integer and is never forced to consider the missing answer, so
// `safeDiv(1, 0) + 1` compiles — the invariant is not in the types.
def safeDiv(a: Int, b: Int): Int =
  if b == 0 then 0 else a / b
