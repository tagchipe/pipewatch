import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.scorer import PipelineScorer, ScoredPipeline
from datetime import datetime


def make_metric(pipeline: str, status: MetricStatus, name: str = "m") -> PipelineMetric:
    return PipelineMetric(
        name=name,
        pipeline=pipeline,
        value=1.0,
        status=status,
        timestamp=datetime.utcnow(),
    )


@pytest.fixture
def scorer():
    return PipelineScorer()


def test_score_returns_none_for_empty(scorer):
    assert scorer.score([]) is None


def test_all_ok_gives_100(scorer):
    metrics = [make_metric("p", MetricStatus.OK) for _ in range(3)]
    result = scorer.score(metrics)
    assert result is not None
    assert result.score == pytest.approx(100.0)


def test_all_critical_gives_0(scorer):
    metrics = [make_metric("p", MetricStatus.CRITICAL) for _ in range(3)]
    result = scorer.score(metrics)
    assert result.score == pytest.approx(0.0)


def test_mixed_score(scorer):
    metrics = [
        make_metric("p", MetricStatus.OK),
        make_metric("p", MetricStatus.WARNING),
        make_metric("p", MetricStatus.CRITICAL),
    ]
    result = scorer.score(metrics)
    # (1.0 + 0.5 + 0.0) / 3 * 100 = 50.0
    assert result.score == pytest.approx(50.0)
    assert result.ok == 1
    assert result.warning == 1
    assert result.critical == 1
    assert result.total == 3


def test_score_all_groups_by_pipeline(scorer):
    metrics = [
        make_metric("a", MetricStatus.OK),
        make_metric("b", MetricStatus.CRITICAL),
        make_metric("a", MetricStatus.OK),
    ]
    results = scorer.score_all(metrics)
    by_pipeline = {r.pipeline: r for r in results}
    assert "a" in by_pipeline
    assert "b" in by_pipeline
    assert by_pipeline["a"].score == pytest.approx(100.0)
    assert by_pipeline["b"].score == pytest.approx(0.0)


def test_to_dict_keys(scorer):
    metrics = [make_metric("p", MetricStatus.OK)]
    result = scorer.score(metrics)
    d = result.to_dict()
    assert set(d.keys()) == {"pipeline", "score", "total", "ok", "warning", "critical"}
