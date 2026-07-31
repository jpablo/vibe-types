// Not total: indexes directly and throws IndexOutOfBoundsException out of
// bounds. The caller receives a bare Int and is never forced to consider the
// missing element, so `get(items, 99) + 1` compiles — the invariant is not in
// the types.
def get(items: List[Int], index: Int): Int =
  items(index)
