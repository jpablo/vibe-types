# Not total: returns a bare int and raises ZeroDivisionError at runtime for
# b == 0. The caller gets a "usable" number and is never forced to consider the
# missing answer, so `safe_div(1, 0) + 1` type-checks.
def safe_div(a: int, b: int) -> int:
    return a // b
