# Runtime state: one class holds a state string and every operation is always
# callable, deferring "wrong state" to a runtime raise. `closed_conn().send(..)`
# type-checks — the protocol is not enforced by the types.
class Conn:
    def __init__(self) -> None:
        self._state = "closed"

    def listen(self) -> "Conn":
        if self._state != "closed":
            raise RuntimeError("can only listen on a closed connection")
        self._state = "listening"
        return self

    def accept(self) -> "Conn":
        if self._state != "listening":
            raise RuntimeError("can only accept on a listening connection")
        self._state = "established"
        return self

    def send(self, data: str) -> "Conn":
        if self._state != "established":
            raise RuntimeError("can only send on an established connection")
        return self


def closed_conn() -> Conn:
    return Conn()
