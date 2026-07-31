-- Runtime-checked builder: one structure holds Option fields and `build` is
-- always callable, inventing a default for the missing url.
-- `RequestBuilder.new.build` elaborates (and would return garbage), so the
-- invariant is NOT enforced by the types.
structure Request where
  url : String
  method : Option String

structure RequestBuilder where
  url? : Option String := none
  method? : Option String := none

def RequestBuilder.new : RequestBuilder := {}

def RequestBuilder.url (b : RequestBuilder) (url : String) : RequestBuilder :=
  { b with url? := some url }

def RequestBuilder.method (b : RequestBuilder) (method : String) : RequestBuilder :=
  { b with method? := some method }

def RequestBuilder.build (b : RequestBuilder) : Request :=
  { url := b.url?.getD "", method := b.method? }
