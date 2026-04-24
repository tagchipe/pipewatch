"""Tests for pipewatch.quota."""
import time
import pytest

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.quota import QuotaManager, QuotaResult


def make_metric(pipeline: str = "etl", value: float = 1.0) -> PipelineMetric:
    return PipelineMetric(
        name="row_count",
        pipeline=pipeline,
        value=value,
        status=MetricStatus.OK,
        timestamp=time.time(),
    )


@pytest.fixture
def manager() -> QuotaManager:
    return QuotaManager(default_limit=3, default_window=60)


def test_first_metric_accepted(manager):
    result = manager.check(make_metric())
    assert result.accepted is True


def test_accepted_increments_used(manager):
    result = manager.check(make_metric())
    assert result.used == 1


def test_blocked_when_limit_exceeded(manager):
    now = time.time()
    for _ in range(3):
        manager.check(make_metric(), _now=now)
    result = manager.check(make_metric(), _now=now)
    assert result.accepted is False
    assert result.used == 3


def test_remaining_decrements(manager):
    now = time.time()
    assert manager.remaining("etl", _now=now) == 3
    manager.check(make_metric(), _now=now)
    assert manager.remaining("etl", _now=now) == 2


def test_window_resets_after_expiry(manager):
    now = time.time()
    for _ in range(3):
        manager.check(make_metric(), _now=now)
    future = now + 61
    result = manager.check(make_metric(), _now=future)
    assert result.accepted is True


def test_custom_limit_per_pipeline(manager):
    manager.register("special", limit=1, window_seconds=60)
    now = time.time()
    r1 = manager.check(make_metric(pipeline="special"), _now=now)
    r2 = manager.check(make_metric(pipeline="special"), _now=now)
    assert r1.accepted is True
    assert r2.accepted is False


def test_to_dict_keys(manager):
    result = manager.check(make_metric())
    d = result.to_dict()
    assert set(d.keys()) == {"pipeline", "accepted", "used", "limit", "window_seconds"}


def test_different_pipelines_independent(manager):
    now = time.time()
    for _ in range(3):
        manager.check(make_metric(pipeline="a"), _now=now)
    result = manager.check(make_metric(pipeline="b"), _now=now)
    assert result.accepted is True
