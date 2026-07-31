-- Not honest: the panicking accessor returns a bare Int (out of bounds panics
-- at runtime via Inhabited). The caller is never forced to consider the
-- missing element, so `get [1, 2, 3] 99 + 1` elaborates — the invariant is
-- not in the types.
def get (items : List Int) (index : Nat) : Int :=
  items[index]!
