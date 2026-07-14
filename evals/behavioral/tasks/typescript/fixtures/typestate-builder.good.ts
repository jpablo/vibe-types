// Typestate: the builder's state lives in the type, so `build` only exists
// once a URL has been set. `createRequestBuilder().build()` is a compile error
// (no such method on the no-url state).
export interface Request {
  url: string;
  method?: string;
}

export interface RequestBuilderNoUrl {
  url(url: string): RequestBuilderWithUrl;
}

export interface RequestBuilderWithUrl {
  method(method: string): RequestBuilderWithUrl;
  build(): Request;
}

export function createRequestBuilder(): RequestBuilderNoUrl {
  const withUrl = (url: string, method?: string): RequestBuilderWithUrl => ({
    method: (m) => withUrl(url, m),
    build: () => ({ url, method }),
  });
  return { url: (u) => withUrl(u) };
}
