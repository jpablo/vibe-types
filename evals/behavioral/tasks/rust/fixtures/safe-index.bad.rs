// Not total: indexes directly and panics out of bounds. The caller receives a
// bare i32 and is never forced to consider the missing element, so
// `get(&v, 99) + 1` type-checks — the invariant is not in the types.
pub fn get(items: &[i32], index: usize) -> i32 {
    items[index]
}
