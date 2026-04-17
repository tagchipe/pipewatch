"""Tests for pipewatch.baseline."""
import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.baseline import BaselineEntry, BaselineChecker, DeviationResult
import datetime


def make_metric(name="row_count", value=100.0, pipeline="etl"):
    return PipelineMetric(
        pipeline=pipeline,
        name=name,
        value=value,
        status=MetricStatus.OK,
        timestamp=datetime.datetime.utcnow(),
    )


@pytest.fixture
def checker():
    c = BaselineChecker()
    c.register(BaselineEntry(pipeline="etl", name="row_count", expected=100.0, tolerance=0.1))
    return c


def test_within_baseline(checker):
    result = checker.check(make_metric(value=105.0))
    assert result is not None
    assert result.within_baseline is True


def test_outside_baseline(checker):
    result = checker.check(make_metric(value=200.0))
    assert result is not None
    assert result.within_baseline is False
    assert result.deviation == pytest.approx(1.0)


def test_exact_expected(checker):
    result = checker.check(make_metric(value=100.0))
    assert result.deviation == pytest.approx(0.0)
    assert result.within_baseline is True


def test_unregistered_metric_returns_none(checker):
    m = make_metric(name="unknown_metric")
    assert checker.check(m) is None


def test_check_all_filters_unregistered(checker):
    metrics = [make_metric(value=90.0), make_metric(name="other", value=5.0)]
    results = checker.check_all(metrics)
    assert len(results) == 1
    assert results[0].metric.name == "row_count"


def test_to_dict_keys(checker):
    result = checker.check(make_metric(value=110.0))
    d = result.to_dict()
    for key in ("pipeline", "name", "value", "expected", "tolerance", "deviation", "within_baseline"):
        assert key in d


def test_zero_expected_deviation():
    entry = BaselineEntry(pipeline="p", name="n", expected=0.0, tolerance=0.1)
    assert entry.deviation(0.5) == pytest.approx(0.5)
    assert entry.is_within(0.05) is True
    assert entry.is_within(0.5) is False
