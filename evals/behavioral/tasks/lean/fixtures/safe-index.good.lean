-- Total: out-of-bounds is widened into Option, so the caller must handle the
-- missing element. `get [1, 2, 3] 99 + 1` fails elaboration (no HAdd instance
-- for Option Int).
def get (items : List Int) (index : Nat) : Option Int :=
  items[index]?
