// Runtime state: one struct holds a state enum and every operation is always
// callable, deferring "wrong state" to a runtime check (or nothing). So
// `Conn::closed().send(..)` type-checks — the protocol is not enforced by types.
pub enum State {
    Closed,
    Listening,
    Established,
}

pub struct Conn {
    state: State,
}

impl Conn {
    pub fn closed() -> Conn {
        Conn { state: State::Closed }
    }
    pub fn listen(mut self) -> Conn {
        self.state = State::Listening;
        self
    }
    pub fn accept(mut self) -> Conn {
        self.state = State::Established;
        self
    }
    pub fn send(self, _data: &str) -> Conn {
        self
    }
}
