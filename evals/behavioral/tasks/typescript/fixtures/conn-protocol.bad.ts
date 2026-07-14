// Runtime state: one class holds a state field and every operation is always
// callable, deferring "wrong state" to a runtime throw (or nothing). So
// `closedConn().send(..)` type-checks — the protocol is not enforced by types.
type State = "closed" | "listening" | "established";

export class Conn {
  private state: State = "closed";

  listen(): Conn {
    if (this.state !== "closed") throw new Error("not closed");
    this.state = "listening";
    return this;
  }
  accept(): Conn {
    if (this.state !== "listening") throw new Error("not listening");
    this.state = "established";
    return this;
  }
  send(_data: string): Conn {
    if (this.state !== "established") throw new Error("not established");
    return this;
  }
}

export function closedConn(): Conn {
  return new Conn();
}
