# Typestate: each protocol state is its own class, so an operation only exists
# in the state where it's legal. `closed_conn().send(..)` is a pyright error
# (send only exists on an established connection).
class EstablishedConn:
    def send(self, data: str) -> "EstablishedConn":
        return self


class ListeningConn:
    def accept(self) -> EstablishedConn:
        return EstablishedConn()


class ClosedConn:
    def listen(self) -> ListeningConn:
        return ListeningConn()


def closed_conn() -> ClosedConn:
    return ClosedConn()
