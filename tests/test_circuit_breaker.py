"""Tests for pipewatch.circuit_breaker."""
from datetime import datetime, timedelta

import pytest

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.circuit_breaker import CircuitBreaker, BreakerState


def make_metric(pipeline: str, status: MetricStatus, value: float = 1.0) -> PipelineMetric:
    return PipelineMetric(
        name="row_count",
        pipeline=pipeline,
        value=value,
        status=status,
        timestamp=datetime.utcnow(),
    )


@pytest.fixture
def breaker() -> CircuitBreaker:
    return CircuitBreaker(threshold=3, recovery_seconds=60.0)


def test_first_failure_is_allowed(breaker):
    result = breaker.check(make_metric("pipe_a", MetricStatus.WARNING))
    assert result.allowed is True
    assert result.state == BreakerState.CLOSED
    assert result.failure_count == 1


def test_ok_metric_always_allowed(breaker):
    result = breaker.check(make_metric("pipe_a", MetricStatus.OK))
    assert result.allowed is True
    assert result.state == BreakerState.CLOSED


def test_trips_open_after_threshold(breaker):
    for _ in range(2):
        r = breaker.check(make_metric("pipe_a", MetricStatus.CRITICAL))
        assert r.allowed is True
    result = breaker.check(make_metric("pipe_a", MetricStatus.CRITICAL))
    assert result.allowed is False
    assert result.state == BreakerState.OPEN


def test_open_breaker_blocks_subsequent_alerts(breaker):
    for _ in range(3):
        breaker.check(make_metric("pipe_a", MetricStatus.CRITICAL))
    result = breaker.check(make_metric("pipe_a", MetricStatus.CRITICAL))
    assert result.allowed is False
    assert result.state == BreakerState.OPEN


def test_ok_resets_open_breaker(breaker):
    for _ in range(3):
        breaker.check(make_metric("pipe_a", MetricStatus.CRITICAL))
    result = breaker.check(make_metric("pipe_a", MetricStatus.OK))
    assert result.allowed is True
    assert result.state == BreakerState.CLOSED
    assert result.failure_count == 0


def test_half_open_allows_probe_on_ok(breaker):
    for _ in range(3):
        breaker.check(make_metric("pipe_a", MetricStatus.CRITICAL))
    entry = breaker.state_for("pipe_a")
    # Manually backdate opened_at to simulate recovery window elapsed
    entry.opened_at = datetime.utcnow() - timedelta(seconds=120)
    result = breaker.check(make_metric("pipe_a", MetricStatus.OK))
    assert result.allowed is True
    assert result.state == BreakerState.CLOSED


def test_half_open_re_opens_on_failure(breaker):
    for _ in range(3):
        breaker.check(make_metric("pipe_a", MetricStatus.CRITICAL))
    entry = breaker.state_for("pipe_a")
    entry.opened_at = datetime.utcnow() - timedelta(seconds=120)
    result = breaker.check(make_metric("pipe_a", MetricStatus.WARNING))
    assert result.allowed is False
    assert result.state == BreakerState.OPEN


def test_reset_clears_entry(breaker):
    for _ in range(3):
        breaker.check(make_metric("pipe_a", MetricStatus.CRITICAL))
    breaker.reset("pipe_a")
    assert breaker.state_for("pipe_a") is None


def test_independent_pipelines(breaker):
    for _ in range(3):
        breaker.check(make_metric("pipe_a", MetricStatus.CRITICAL))
    result_b = breaker.check(make_metric("pipe_b", MetricStatus.CRITICAL))
    assert result_b.allowed is True
    assert result_b.state == BreakerState.CLOSED
