# Not total: indexes directly and claims a bare int. Out of bounds raises
# IndexError at runtime, but the type never says so, so `get(items, 99) + 1`
# type-checks — the invariant is not in the types.
def get(items: list[int], index: int) -> int:
    return items[index]
