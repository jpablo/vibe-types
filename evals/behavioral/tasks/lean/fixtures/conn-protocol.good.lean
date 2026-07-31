-- Typestate: the connection type is indexed by its protocol state, so each
-- operation only accepts the state where it's legal.
-- `Conn.closed.send "hello"` fails elaboration (Conn .closed vs .established).
inductive ConnState
  | closed
  | listening
  | established

structure Conn (s : ConnState)

def Conn.closed : Conn .closed := {}

def Conn.listen (_c : Conn .closed) : Conn .listening := {}

def Conn.accept (_c : Conn .listening) : Conn .established := {}

def Conn.send (c : Conn .established) (_data : String) : Conn .established := c
