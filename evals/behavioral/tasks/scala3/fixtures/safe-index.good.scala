// Total: out-of-bounds is widened into Option, so the caller must handle the
// missing element. `get(items, 99) + 1` does not compile (Option has no +).
def get(items: List[Int], index: Int): Option[Int] =
  items.lift(index)
