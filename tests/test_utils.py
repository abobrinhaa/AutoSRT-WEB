import pytest

app = pytest.importorskip("app")


def test_format_line():
    text = "this is a simple sentence that should wrap"
    wrapped = app.format_line(text, width=10)
    lines = wrapped.split("\n")
    for line in lines:
        assert len(line) <= 10


def test_clean_text():
    dirty = "<b>Hello</b>\u200b\ufeff😊"
    cleaned = app.clean_text(dirty)
    assert cleaned == "Hello"
