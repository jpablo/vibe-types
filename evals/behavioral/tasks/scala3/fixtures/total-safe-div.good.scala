// Total: the output is widened to Option, so "no answer" (b == 0) becomes a case
// the caller must handle. `safeDiv(1, 0) + 1` does not compile (Option has no +).
def safeDiv(a: Int, b: Int): Option[Int] =
  if b == 0 then None else Some(a / b)
