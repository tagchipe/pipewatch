import time
import pytest
from pipewatch.ratelimit import RateLimiter


@pytest.fixture
def limiter() -> RateLimiter:
    return RateLimiter()


def test_unregistered_key_always_allowed(limiter):
    for _ in range(20):
        assert limiter.is_allowed("unknown") is True


def test_allowed_within_limit(limiter):
    limiter.register("etl.rows", max_calls=3, window_seconds=10)
    assert limiter.is_allowed("etl.rows") is True
    assert limiter.is_allowed("etl.rows") is True
    assert limiter.is_allowed("etl.rows") is True


def test_blocked_when_limit_exceeded(limiter):
    limiter.register("etl.rows", max_calls=2, window_seconds=10)
    limiter.is_allowed("etl.rows")
    limiter.is_allowed("etl.rows")
    assert limiter.is_allowed("etl.rows") is False


def test_remaining_decrements(limiter):
    limiter.register("etl.rows", max_calls=3, window_seconds=10)
    assert limiter.remaining("etl.rows") == 3
    limiter.is_allowed("etl.rows")
    assert limiter.remaining("etl.rows") == 2


def test_remaining_none_for_unregistered(limiter):
    assert limiter.remaining("ghost") is None


def test_reset_clears_bucket(limiter):
    limiter.register("etl.rows", max_calls=1, window_seconds=10)
    limiter.is_allowed("etl.rows")
    assert limiter.is_allowed("etl.rows") is False
    limiter.reset("etl.rows")
    assert limiter.is_allowed("etl.rows") is True


def test_window_expiry_allows_new_calls(limiter):
    limiter.register("fast", max_calls=1, window_seconds=0.1)
    assert limiter.is_allowed("fast") is True
    assert limiter.is_allowed("fast") is False
    time.sleep(0.15)
    assert limiter.is_allowed("fast") is True


def test_multiple_keys_independent(limiter):
    limiter.register("a", max_calls=1, window_seconds=10)
    limiter.register("b", max_calls=1, window_seconds=10)
    limiter.is_allowed("a")
    assert limiter.is_allowed("a") is False
    assert limiter.is_allowed("b") is True
