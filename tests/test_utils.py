from agents.utils import retry_on_failure, extract_text


def test_retry_on_failure_retries_then_succeeds():
    calls = {"count": 0}

    @retry_on_failure(max_attempts=3, delay=0)
    def flaky():
        calls["count"] += 1
        if calls["count"] < 3:
            raise ValueError("not yet")
        return "ok"

    assert flaky() == "ok"
    assert calls["count"] == 3


def test_extract_text_handles_plain_string():
    assert extract_text("hello") == "hello"


def test_extract_text_handles_block_list():
    blocks = [{"type": "text", "text": "hello "}, {"type": "text", "text": "world"}]
    assert extract_text(blocks) == "hello world"
    