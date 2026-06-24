// Typestate: the connection's protocol state is a type parameter, so each
// operation only exists in the state where it's legal. `Conn::closed().send(..)`
// does not type-check (send is only on Conn<Established>).
use std::marker::PhantomData;

pub struct Closed;
pub struct Listening;
pub struct Established;

pub struct Conn<S> {
    _state: PhantomData<S>,
}

impl Conn<Closed> {
    pub fn closed() -> Conn<Closed> {
        Conn { _state: PhantomData }
    }
    pub fn listen(self) -> Conn<Listening> {
        Conn { _state: PhantomData }
    }
}

impl Conn<Listening> {
    pub fn accept(self) -> Conn<Established> {
        Conn { _state: PhantomData }
    }
}

impl Conn<Established> {
    pub fn send(self, _data: &str) -> Conn<Established> {
        self
    }
}
