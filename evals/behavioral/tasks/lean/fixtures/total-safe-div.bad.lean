-- Total but dishonest: Lean defines x / 0 = 0, so this returns a bare Int and
-- silently invents 0 for the b = 0 case. The caller gets a usable integer and
-- is never forced to consider the missing answer, so `safeDiv 1 0 + 1`
-- elaborates — the invariant is not in the types.
def safeDiv (a b : Int) : Int :=
  a / b
