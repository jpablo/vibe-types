// Runtime-checked builder: one type holds Option fields and `build` is always
// callable, deferring the "url required" check to a runtime throw.
// `RequestBuilder().build()` compiles (and would throw), so the invariant is
// NOT enforced by the types.
final case class Request(url: String, method: Option[String])

final class RequestBuilder {
  private var urlOpt: Option[String] = None
  private var methodOpt: Option[String] = None

  def url(url: String): RequestBuilder = { urlOpt = Some(url); this }
  def method(method: String): RequestBuilder = { methodOpt = Some(method); this }
  def build(): Request =
    Request(urlOpt.getOrElse(throw new IllegalStateException("url is required")), methodOpt)
}

object RequestBuilder {
  def apply(): RequestBuilder = new RequestBuilder
}
