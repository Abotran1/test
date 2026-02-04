import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from main import _approx_token_count
from services.memory_store import MemoryStore
from services.rate_limit import RateLimiter
from services.safety import SafetyFilter


def test_memory_store_tracks_messages_and_trims():
    store = MemoryStore(max_history_messages=2)
    session_id = store.create_session()

    store.append_message(session_id, "user", "hello")
    store.append_message(session_id, "assistant", "hi")
    store.append_message(session_id, "user", "how are you")

    messages = store.get_messages(session_id)
    assert len(messages) == 2
    assert messages[0].content == "hi"
    assert messages[1].content == "how are you"


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    key = "client"

    assert limiter.check(key).allowed is True
    assert limiter.check(key).allowed is True
    status = limiter.check(key)

    assert status.allowed is False
    assert status.retry_after_seconds is not None
    assert status.retry_after_seconds >= 1


def test_safety_filter_blocks_terms():
    safety = SafetyFilter()
    ok, reason = safety.check("This is illegal content")

    assert ok is False
    assert "policy" in reason.lower()


def test_approx_token_count_handles_blank():
    assert _approx_token_count("") == 1
    assert _approx_token_count("one two") == 2
