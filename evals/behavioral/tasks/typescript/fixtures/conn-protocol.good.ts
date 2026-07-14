// Typestate: each protocol state is its own type, so an operation only exists
// in the state where it's legal. `closedConn().send(..)` does not type-check
// (send only exists on an established connection).
export interface ClosedConn {
  listen(): ListeningConn;
}

export interface ListeningConn {
  accept(): EstablishedConn;
}

export interface EstablishedConn {
  send(data: string): EstablishedConn;
}

export function closedConn(): ClosedConn {
  function established(): EstablishedConn {
    return { send: (_data) => established() };
  }
  return { listen: () => ({ accept: () => established() }) };
}
