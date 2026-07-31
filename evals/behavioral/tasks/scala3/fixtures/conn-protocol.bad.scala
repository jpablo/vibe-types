// Runtime state: one class holds a state enum and every operation is always
// callable, deferring "wrong state" to a runtime check (or nothing). So
// `Conn.closed().send(..)` compiles — the protocol is not enforced by types.
enum State {
  case Closed, Listening, Established
}

final class Conn private (private var state: State) {
  def listen(): Conn = { state = State.Listening; this }
  def accept(): Conn = { state = State.Established; this }
  def send(data: String): Conn = this
}

object Conn {
  def closed(): Conn = new Conn(State.Closed)
}
