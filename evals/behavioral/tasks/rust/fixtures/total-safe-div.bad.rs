// Not total: returns a bare i32, inventing 0 for the b == 0 case. The caller gets
// a usable integer and is never forced to consider the missing answer, so
// `safe_div(1, 0) + 1` type-checks — the invariant is not in the types.
pub fn safe_div(a: i32, b: i32) -> i32 {
    if b == 0 { 0 } else { a / b }
}
