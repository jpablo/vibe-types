-- Typestate: the builder type is indexed by its state, so `build` only accepts
-- a with-url builder. `RequestBuilder.new.build` fails elaboration (type
-- mismatch: RequestBuilder .noUrl vs RequestBuilder .hasUrl).
inductive UrlState
  | noUrl
  | hasUrl

structure Request where
  url : String
  method : Option String

structure RequestBuilder (s : UrlState) where
  url? : Option String := none
  method? : Option String := none

def RequestBuilder.new : RequestBuilder .noUrl := {}

def RequestBuilder.url {s : UrlState} (b : RequestBuilder s) (url : String) :
    RequestBuilder .hasUrl :=
  { url? := some url, method? := b.method? }

def RequestBuilder.method {s : UrlState} (b : RequestBuilder s) (method : String) :
    RequestBuilder s :=
  { b with method? := some method }

def RequestBuilder.build (b : RequestBuilder .hasUrl) : Request :=
  { url := b.url?.getD "", method := b.method? }
