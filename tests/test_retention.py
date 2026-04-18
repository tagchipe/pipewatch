"""Tests for pipewatch.retention."""
import pytest
from datetime import datetime, timedelta
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.retention import RetentionManager, RetentionPolicy


def make_metric(pipeline: str, age_seconds: float) -> PipelineMetric:
    ts = datetime.utcnow() - timedelta(seconds=age_seconds)
    return PipelineMetric(
        name="rows",
        pipeline=pipeline,
        value=1.0,
        status=MetricStatus.OK,
        timestamp=ts,
    )


@pytest.fixture
def manager() -> RetentionManager:
    return RetentionManager()


def test_no_policy_uses_default_24h(manager):
    fresh = make_metric("pipe", age_seconds=3600)
    result = manager.apply([fresh])
    assert fresh in result.kept
    assert result.evicted == []


def test_old_metric_evicted_by_default(manager):
    old = make_metric("pipe", age_seconds=90000)
    result = manager.apply([old])
    assert old in result.evicted
    assert result.kept == []


def test_custom_policy_evicts_early(manager):
    manager.register("fast", max_age_seconds=60)
    recent = make_metric("fast", age_seconds=30)
    stale = make_metric("fast", age_seconds=120)
    result = manager.apply([recent, stale])
    assert recent in result.kept
    assert stale in result.evicted


def test_mixed_pipelines(manager):
    manager.register("a", max_age_seconds=100)
    manager.register("b", max_age_seconds=10)
    m_a = make_metric("a", age_seconds=50)
    m_b = make_metric("b", age_seconds=50)
    result = manager.apply([m_a, m_b])
    assert m_a in result.kept
    assert m_b in result.evicted


def test_to_dict(manager):
    manager.register("p", max_age_seconds=60)
    metrics = [make_metric("p", 10), make_metric("p", 200)]
    result = manager.apply(metrics)
    d = result.to_dict()
    assert d["kept"] == 1
    assert d["evicted"] == 1


def test_register_returns_policy(manager):
    p = manager.register("pipe", 300)
    assert isinstance(p, RetentionPolicy)
    assert p.max_age_seconds == 300
