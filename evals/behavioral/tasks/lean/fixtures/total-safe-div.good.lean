-- Total AND honest: the output is widened to Option, so "no answer" (b = 0)
-- becomes a case the caller must handle. `safeDiv 1 0 + 1` fails elaboration
-- (no HAdd instance for Option Int).
def safeDiv (a b : Int) : Option Int :=
  if b = 0 then none else some (a / b)
