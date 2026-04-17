import pytest
from pipewatch.anomaly import AnomalyDetector
from pipewatch.metrics import PipelineMetric, MetricStatus


def make_metric(name: str, value: float, pipeline: str = "pipe1") -> PipelineMetric:
    return PipelineMetric(name=name, value=value, pipeline=pipeline, status=MetricStatus.OK)


@pytest.fixture
def detector():
    return AnomalyDetector(threshold=2.0, min_samples=3)


def test_check_returns_none_before_min_samples(detector):
    m = make_metric("latency", 10.0)
    detector.record(m)
    detector.record(make_metric("latency", 11.0))
    result = detector.check(make_metric("latency", 50.0))
    assert result is None


def test_no_anomaly_on_normal_value(detector):
    for v in [10.0, 10.0, 10.0, 10.0]:
        detector.record(make_metric("latency", v))
    result = detector.check(make_metric("latency", 10.5))
    assert result is not None
    assert result.is_anomaly is False


def test_anomaly_detected_on_spike(detector):
    for v in [10.0, 10.0, 10.0, 10.0, 10.0]:
        detector.record(make_metric("latency", v))
    result = detector.check(make_metric("latency", 100.0))
    assert result is not None
    assert result.is_anomaly is True
    assert result.z_score > 2.0


def test_record_and_check_returns_result(detector):
    for v in [5.0, 5.0, 5.0]:
        detector.record(make_metric("errors", v))
    result = detector.record_and_check(make_metric("errors", 5.1))
    assert result is not None
    assert result.metric_name == "errors"


def test_to_dict_keys(detector):
    for v in [1.0, 1.0, 1.0, 1.0]:
        detector.record(make_metric("rows", v))
    result = detector.check(make_metric("rows", 1.0))
    d = result.to_dict()
    assert set(d.keys()) == {"metric_name", "pipeline", "value", "mean", "stddev", "z_score", "is_anomaly"}


def test_separate_pipelines_tracked_independently(detector):
    for v in [10.0, 10.0, 10.0]:
        detector.record(make_metric("latency", v, pipeline="pipe1"))
    result = detector.check(make_metric("latency", 10.0, pipeline="pipe2"))
    assert result is None
