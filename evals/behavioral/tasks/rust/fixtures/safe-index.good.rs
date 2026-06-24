// Total: out-of-bounds is widened into Option, so the caller must handle the
// missing element. `get(&v, 99) + 1` does not type-check (Option has no Add).
pub fn get(items: &[i32], index: usize) -> Option<i32> {
    items.get(index).copied()
}
