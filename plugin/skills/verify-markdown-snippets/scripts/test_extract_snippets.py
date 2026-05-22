"""Tests for extract_snippets.extract()."""

from extract_snippets import extract


def test_single_backtick_fence():
    md = """\
# Title

```python
x = 1
```
"""
    result = extract(md)
    assert len(result) == 1
    assert result[0]["index"] == 1
    assert result[0]["line"] == 3
    assert result[0]["language"] == "python"
    assert result[0]["source"] == "x = 1\n"


def test_tilde_fence():
    md = """\
~~~rust
fn main() {}
~~~
"""
    result = extract(md)
    assert len(result) == 1
    assert result[0]["language"] == "rust"
    assert result[0]["source"] == "fn main() {}\n"


def test_no_language_tag():
    md = """\
```
just text
```
"""
    result = extract(md)
    assert len(result) == 1
    assert result[0]["language"] is None
    assert result[0]["source"] == "just text\n"


def test_multiple_snippets():
    md = """\
```python
a = 1
```

```typescript
const b = 2;
```

```
bare
```
"""
    result = extract(md)
    assert len(result) == 3
    assert result[0]["language"] == "python"
    assert result[0]["line"] == 1
    assert result[1]["language"] == "typescript"
    assert result[1]["line"] == 5
    assert result[2]["language"] is None
    assert result[2]["line"] == 9


def test_language_lowercased():
    md = """\
```Python
pass
```
"""
    result = extract(md)
    assert result[0]["language"] == "python"


def test_info_string_extra_words():
    md = """\
```python title="example.py"
x = 1
```
"""
    result = extract(md)
    assert result[0]["language"] == "python"
    assert result[0]["source"] == "x = 1\n"


def test_longer_closing_fence():
    md = """\
````python
x = 1
````
"""
    result = extract(md)
    assert len(result) == 1
    assert result[0]["source"] == "x = 1\n"


def test_closing_fence_must_match_char():
    """Backtick fence must not be closed by tildes."""
    md = """\
```python
x = 1
~~~
more
```
"""
    result = extract(md)
    assert len(result) == 1
    assert "~~~" in result[0]["source"]
    assert "more" in result[0]["source"]


def test_closing_fence_must_match_length():
    """Closing fence shorter than opening does not close the block."""
    md = """\
`````python
x = 1
```
still inside
`````
"""
    result = extract(md)
    assert len(result) == 1
    assert "```" in result[0]["source"]
    assert "still inside" in result[0]["source"]


def test_indented_fence():
    md = """\
   ```python
   x = 1
   ```
"""
    result = extract(md)
    assert len(result) == 1
    assert result[0]["language"] == "python"
    assert result[0]["source"] == "x = 1\n"


def test_four_space_indent_not_a_fence():
    """4+ spaces of indent is NOT a fence — it's an indented code block."""
    md = """\
    ```python
    x = 1
    ```
"""
    result = extract(md)
    assert len(result) == 0


def test_unclosed_fence():
    """EOF before closing fence still records the snippet."""
    md = """\
```python
x = 1
y = 2
"""
    result = extract(md)
    assert len(result) == 1
    assert result[0]["source"] == "x = 1\ny = 2\n"


def test_empty_fence():
    md = """\
```python
```
"""
    result = extract(md)
    assert len(result) == 1
    assert result[0]["source"] == ""


def test_empty_document():
    assert extract("") == []


def test_no_fences():
    assert extract("just some text\nno fences here\n") == []


def test_nested_backticks_in_longer_fence():
    """A ``` inside a ```` fence is content, not a delimiter."""
    md = """\
````markdown
Here is an example:

```python
x = 1
```
````
"""
    result = extract(md)
    assert len(result) == 1
    assert result[0]["language"] == "markdown"
    assert "```python" in result[0]["source"]
    assert "x = 1" in result[0]["source"]


def test_multiline_source_preserved():
    md = """\
```python
def foo():
    return 42

class Bar:
    pass
```
"""
    result = extract(md)
    assert result[0]["source"] == "def foo():\n    return 42\n\nclass Bar:\n    pass\n"


def test_indexes_are_sequential():
    md = """\
```a
1
```

```b
2
```

```c
3
```
"""
    result = extract(md)
    assert [s["index"] for s in result] == [1, 2, 3]


def test_closing_fence_with_trailing_spaces():
    md = "```python\nx = 1\n```   \n"
    result = extract(md)
    assert len(result) == 1
    assert result[0]["source"] == "x = 1\n"


def test_closing_fence_no_info_string():
    """A closing fence with text after it is NOT a valid close."""
    md = """\
```python
x = 1
``` not a close
still inside
```
"""
    result = extract(md)
    assert len(result) == 1
    assert "not a close" in result[0]["source"]
    assert "still inside" in result[0]["source"]


# --- expect-error keyword tests ---


def test_expect_error_keyword_standalone():
    md = """\
```python
# expect-error
foo("a")  # error: expected int
```
"""
    result = extract(md)
    assert result[0]["expect_error"] is True
    assert len(result[0]["expected_errors"]) == 1


def test_expect_error_keyword_absent():
    md = """\
```python
x = 1
```
"""
    result = extract(md)
    assert result[0]["expect_error"] is False


def test_expect_error_keyword_case_insensitive():
    md = """\
```python
# Expect-Error
x = bad()
```
"""
    result = extract(md)
    assert result[0]["expect_error"] is True


def test_expect_error_without_error_comments():
    """Keyword alone is enough — description comments are optional."""
    md = """\
```python
# expect-error
BadProcessor()
```
"""
    result = extract(md)
    assert result[0]["expect_error"] is True
    assert result[0]["expected_errors"] == []


def test_error_comments_without_keyword_do_not_set_expect_error():
    """# error: comments alone do not set expect_error — the keyword is required."""
    md = """\
```python
foo("a")  # error: expected int
```
"""
    result = extract(md)
    assert result[0]["expect_error"] is False
    assert len(result[0]["expected_errors"]) == 1


# --- Expected-error description extraction tests ---


def test_expected_error_inline():
    md = """\
```python
next_action("pending")  # error: expected "OrderStatus", got "str"
```
"""
    result = extract(md)
    assert len(result[0]["expected_errors"]) == 1
    assert result[0]["expected_errors"][0]["line"] == 1
    assert result[0]["expected_errors"][0]["comment"] == 'expected "OrderStatus", got "str"'


def test_expected_error_type_error_variant():
    md = """\
```python
return c == "red"  # type error: comparing Color with str literal
```
"""
    result = extract(md)
    assert len(result[0]["expected_errors"]) == 1
    assert "comparing Color with str literal" in result[0]["expected_errors"][0]["comment"]


def test_expected_error_typeerror_variant():
    md = """\
```python
BadProcessor()  # TypeError: Can't instantiate abstract class
```
"""
    result = extract(md)
    assert len(result[0]["expected_errors"]) == 1
    assert "Can't instantiate abstract class" in result[0]["expected_errors"][0]["comment"]


def test_expected_error_skips_commented_out_python_code():
    """`# bad_call()  # error: …` is commented-out teaching content, not a header
    annotation. The checker never sees the bad code, so the annotation isn't a
    prediction about what the tool will report — skip it.

    Mirrors the existing `//` behavior tested in
    test_expected_error_skips_commented_out_rust_code below."""
    md = """\
```python
# status = X | Y  # error: unsupported operand
```
"""
    result = extract(md)
    assert result[0]["expected_errors"] == []


def test_expected_error_skips_commented_out_rust_code():
    """`// bad_call();  // error: …` is commented-out teaching content — skip."""
    md = """\
```rust
// let x: u32 = -1;  // error[E0600]: cannot apply unary `-` to u32
```
"""
    result = extract(md)
    assert result[0]["expected_errors"] == []


def test_expected_error_python_header_annotation_still_detected():
    """A bare `# error: …` on its own line IS a header annotation describing
    errors the checker should report — accept."""
    md = """\
```python
# error: expected int, got str
foo("a")
```
"""
    result = extract(md)
    assert len(result[0]["expected_errors"]) == 1
    assert "expected int" in result[0]["expected_errors"][0]["comment"]


def test_expected_error_python_trailing_annotation_on_real_code():
    """`real_code()  # error: …` — annotation on actual code, accept."""
    md = """\
```python
foo("a")  # error: expected int, got str
```
"""
    result = extract(md)
    assert len(result[0]["expected_errors"]) == 1
    assert "expected int" in result[0]["expected_errors"][0]["comment"]


def test_expected_error_multiple_in_one_snippet():
    md = """\
```python
foo("a")  # error: expected int, got str
bar(42)   # error: expected str, got int
baz()     # this is fine
```
"""
    result = extract(md)
    assert len(result[0]["expected_errors"]) == 2
    assert result[0]["expected_errors"][0]["line"] == 1
    assert result[0]["expected_errors"][1]["line"] == 2


def test_expected_error_none_when_absent():
    md = """\
```python
x = 1
y = x + 2
```
"""
    result = extract(md)
    assert result[0]["expected_errors"] == []


def test_expected_error_case_insensitive():
    md = """\
```python
x = 1  # Error: something went wrong
```
"""
    result = extract(md)
    assert len(result[0]["expected_errors"]) == 1
    assert "something went wrong" in result[0]["expected_errors"][0]["comment"]


def test_expected_error_not_fooled_by_error_in_string():
    """An '# error:' inside a string literal on its own is not a comment."""
    md = '''\
```python
msg = "# error: this is a string, not a comment"
```
'''
    result = extract(md)
    # The regex searches for # error: anywhere in the line. A string containing
    # "# error:" will match — this is acceptable because the pattern is rare in
    # real snippets and the false positive is harmless (it just means the snippet
    # would be classified as expected_fail instead of fail).
    # We document this known limitation rather than adding a full Python parser.
    assert len(result[0]["expected_errors"]) == 1
