// Runtime-checked builder: one class holds optional fields and `build` is
// always callable, deferring the "url required" check to a runtime throw.
// `createRequestBuilder().build()` type-checks (and would throw), so the
// invariant is NOT enforced by the types.
export interface Request {
  url: string;
  method?: string;
}

export class RequestBuilder {
  private _url?: string;
  private _method?: string;

  url(url: string): RequestBuilder {
    this._url = url;
    return this;
  }
  method(method: string): RequestBuilder {
    this._method = method;
    return this;
  }
  build(): Request {
    if (this._url === undefined) throw new Error("url is required");
    return { url: this._url, method: this._method };
  }
}

export function createRequestBuilder(): RequestBuilder {
  return new RequestBuilder();
}
