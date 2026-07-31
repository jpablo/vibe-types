# Total: out-of-bounds is widened into `int | None`, so the caller must handle
# the missing element. `get(items, 99) + 1` does not type-check
# (reportOptionalOperand).
def get(items: list[int], index: int) -> int | None:
    if 0 <= index < len(items):
        return items[index]
    return None
