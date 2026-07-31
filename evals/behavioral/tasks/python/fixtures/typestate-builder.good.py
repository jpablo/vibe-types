# Typestate: the builder's state lives in the class, so `build` only exists
# once a URL has been set. `create_request_builder().build()` is a pyright
# error (no such attribute on the no-url state).
from dataclasses import dataclass


@dataclass(frozen=True)
class Request:
    url: str
    method: str | None = None


class RequestBuilderWithUrl:
    def __init__(self, url: str, method: str | None = None) -> None:
        self._url = url
        self._method = method

    def method(self, method: str) -> "RequestBuilderWithUrl":
        return RequestBuilderWithUrl(self._url, method)

    def build(self) -> Request:
        return Request(self._url, self._method)


class RequestBuilderNoUrl:
    def url(self, url: str) -> RequestBuilderWithUrl:
        return RequestBuilderWithUrl(url)


def create_request_builder() -> RequestBuilderNoUrl:
    return RequestBuilderNoUrl()
