// Typestate: the connection's protocol state is a phantom type parameter, so
// each operation only exists in the state where it's legal (extensions on the
// right instantiation). `Conn.closed().send(..)` does not compile.
sealed trait Closed
sealed trait Listening
sealed trait Established

final class Conn[S] private ()

object Conn {
  def closed(): Conn[Closed] = new Conn
  extension (c: Conn[Closed]) def listen(): Conn[Listening] = new Conn
  extension (c: Conn[Listening]) def accept(): Conn[Established] = new Conn
  extension (c: Conn[Established]) def send(data: String): Conn[Established] = c
}
