// Typestate: the state lives in a phantom type parameter, so `build` is only
// available once a URL has been set (extension on RequestBuilder[HasUrl]).
// `RequestBuilder().build()` is a compile error.
sealed trait NoUrl
sealed trait HasUrl

final case class Request(url: String, method: Option[String])

final class RequestBuilder[S] private (
    private val urlOpt: Option[String],
    private val methodOpt: Option[String],
) {
  def url(url: String): RequestBuilder[HasUrl] =
    new RequestBuilder(Some(url), methodOpt)
  def method(method: String): RequestBuilder[S] =
    new RequestBuilder(urlOpt, Some(method))
}

object RequestBuilder {
  def apply(): RequestBuilder[NoUrl] = new RequestBuilder(None, None)
  extension (b: RequestBuilder[HasUrl])
    def build(): Request = Request(b.urlOpt.getOrElse(""), b.methodOpt)
}
