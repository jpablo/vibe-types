# Total: the output is widened to include None, so "no answer" (b == 0) becomes
# a case the caller must handle. `safe_div(1, 0) + 1` does not type-check
# (reportOptionalOperand).
def safe_div(a: int, b: int) -> int | None:
    if b == 0:
        return None
    return a // b
