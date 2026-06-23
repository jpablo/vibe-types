// Runtime-checked builder: one type holds Option fields and `build` is always
// callable, deferring the "url required" check to a runtime panic. `new().build()`
// type-checks (and would panic), so the invariant is NOT enforced by the types.
pub struct RequestBuilder {
    url: Option<String>,
    method: Option<String>,
}

impl RequestBuilder {
    pub fn new() -> RequestBuilder {
        RequestBuilder { url: None, method: None }
    }
    pub fn url(mut self, url: String) -> RequestBuilder {
        self.url = Some(url);
        self
    }
    pub fn method(mut self, method: String) -> Self {
        self.method = Some(method);
        self
    }
    pub fn build(self) -> Request {
        Request { url: self.url.expect("url is required"), method: self.method }
    }
}

pub struct Request {
    pub url: String,
    pub method: Option<String>,
}
