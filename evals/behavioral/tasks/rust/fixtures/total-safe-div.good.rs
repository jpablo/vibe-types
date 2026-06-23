// Total: the output is widened to Option, so "no answer" (b == 0) becomes a case
// the caller must handle. `safe_div(1, 0) + 1` does not type-check (Option has no Add).
pub fn safe_div(a: i32, b: i32) -> Option<i32> {
    if b == 0 { None } else { Some(a / b) }
}
