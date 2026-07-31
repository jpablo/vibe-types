-- Runtime state: one structure holds a state value and every operation is
-- always callable — nothing stops a wrong-state call.
-- `Conn.closed.send "hello"` elaborates — the protocol is not in the types.
inductive ConnState
  | closed
  | listening
  | established

structure Conn where
  state : ConnState

def Conn.closed : Conn := { state := .closed }

def Conn.listen (_c : Conn) : Conn := { state := .listening }

def Conn.accept (_c : Conn) : Conn := { state := .established }

def Conn.send (c : Conn) (_data : String) : Conn := c
