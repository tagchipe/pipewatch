"""Tests for pipewatch.healthcheck."""
import pytest

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.healthcheck import HealthChecker, HealthCheckResult


def make_metric(pipeline: str, name: str, status: MetricStatus, value: float = 1.0) -> PipelineMetric:
    return PipelineMetric(pipeline=pipeline, name=name, value=value, status=status)


@pytest.fixture()
def checker() -> HealthChecker:
    return HealthChecker()


# ---------------------------------------------------------------------------
# check() – single pipeline
# ---------------------------------------------------------------------------

def test_check_returns_none_for_empty(checker):
    result = checker.check("pipe_a", [])
    assert result is None


def test_check_returns_none_for_wrong_pipeline(checker):
    m = make_metric("pipe_b", "rows", MetricStatus.OK)
    result = checker.check("pipe_a", [m])
    assert result is None


def test_all_ok_is_healthy(checker):
    metrics = [make_metric("pipe_a", f"m{i}", MetricStatus.OK) for i in range(5)]
    result = checker.check("pipe_a", metrics)
    assert result is not None
    assert result.state == "healthy"
    assert result.score == pytest.approx(100.0)
    assert result.ok_count == 5
    assert result.warning_count == 0
    assert result.critical_count == 0


def test_all_critical_is_unhealthy(checker):
    metrics = [make_metric("pipe_a", f"m{i}", MetricStatus.CRITICAL) for i in range(4)]
    result = checker.check("pipe_a", metrics)
    assert result is not None
    assert result.state == "unhealthy"
    assert result.score == pytest.approx(0.0)


def test_mixed_warning_gives_degraded(checker):
    # 2 ok (weight 1.0 each) + 2 warning (weight 0.5 each) → weighted_sum=3, total=4 → score=75
    metrics = [
        make_metric("pipe_a", "m1", MetricStatus.OK),
        make_metric("pipe_a", "m2", MetricStatus.OK),
        make_metric("pipe_a", "m3", MetricStatus.WARNING),
        make_metric("pipe_a", "m4", MetricStatus.WARNING),
    ]
    result = checker.check("pipe_a", metrics)
    assert result is not None
    assert result.state == "degraded"
    assert result.score == pytest.approx(75.0)


def test_score_below_50_is_unhealthy(checker):
    # 1 ok + 3 critical → weighted_sum=1, total=4 → score=25
    metrics = [
        make_metric("pipe_a", "m1", MetricStatus.OK),
        make_metric("pipe_a", "m2", MetricStatus.CRITICAL),
        make_metric("pipe_a", "m3", MetricStatus.CRITICAL),
        make_metric("pipe_a", "m4", MetricStatus.CRITICAL),
    ]
    result = checker.check("pipe_a", metrics)
    assert result is not None
    assert result.state == "unhealthy"
    assert result.score == pytest.approx(25.0)


# ---------------------------------------------------------------------------
# check_all()
# ---------------------------------------------------------------------------

def test_check_all_groups_by_pipeline(checker):
    metrics = [
        make_metric("pipe_a", "rows", MetricStatus.OK),
        make_metric("pipe_b", "rows", MetricStatus.CRITICAL),
        make_metric("pipe_a", "lag", MetricStatus.WARNING),
    ]
    results = checker.check_all(metrics)
    pipelines = {r.pipeline for r in results}
    assert pipelines == {"pipe_a", "pipe_b"}


def test_check_all_empty_returns_empty(checker):
    assert checker.check_all([]) == []


# ---------------------------------------------------------------------------
# to_dict / to_json
# ---------------------------------------------------------------------------

def test_to_dict_keys(checker):
    m = make_metric("pipe_a", "rows", MetricStatus.OK)
    result = checker.check("pipe_a", [m])
    d = result.to_dict()
    assert set(d.keys()) == {"pipeline", "state", "total", "ok_count", "warning_count", "critical_count", "score"}


def test_to_json_is_valid(checker):
    import json
    m = make_metric("pipe_a", "rows", MetricStatus.WARNING)
    result = checker.check("pipe_a", [m])
    parsed = json.loads(result.to_json())
    assert parsed["pipeline"] == "pipe_a"
