# Runtime-checked builder: one class holds Optional attributes and `build` is
# always callable, deferring the "url required" check to a runtime raise.
# `create_request_builder().build()` type-checks (and would raise), so the
# invariant is NOT enforced by the types.
from dataclasses import dataclass


@dataclass(frozen=True)
class Request:
    url: str
    method: str | None = None


class RequestBuilder:
    def __init__(self) -> None:
        self._url: str | None = None
        self._method: str | None = None

    def url(self, url: str) -> "RequestBuilder":
        self._url = url
        return self

    def method(self, method: str) -> "RequestBuilder":
        self._method = method
        return self

    def build(self) -> Request:
        if self._url is None:
            raise ValueError("url is required")
        return Request(self._url, self._method)


def create_request_builder() -> RequestBuilder:
    return RequestBuilder()
