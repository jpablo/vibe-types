// Typestate: the state lives in a type parameter, so `build` only exists once a
// URL has been set. `new().build()` is a compile error (no such method on NoUrl).
use std::marker::PhantomData;

pub struct NoUrl;
pub struct HasUrl;

pub struct RequestBuilder<S> {
    url: Option<String>,
    method: Option<String>,
    _state: PhantomData<S>,
}

impl RequestBuilder<NoUrl> {
    pub fn new() -> RequestBuilder<NoUrl> {
        RequestBuilder { url: None, method: None, _state: PhantomData }
    }
    pub fn url(self, url: String) -> RequestBuilder<HasUrl> {
        RequestBuilder { url: Some(url), method: self.method, _state: PhantomData }
    }
}

impl<S> RequestBuilder<S> {
    pub fn method(mut self, method: String) -> Self {
        self.method = Some(method);
        self
    }
}

impl RequestBuilder<HasUrl> {
    pub fn build(self) -> Request {
        Request { url: self.url.unwrap(), method: self.method }
    }
}

pub struct Request {
    pub url: String,
    pub method: Option<String>,
}
