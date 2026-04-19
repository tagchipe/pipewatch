import time
import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.throttle import Throttler, ThrottleResult


def make_metric(pipeline="pipe", name="rows", value=1.0):
    return PipelineMetric(pipeline=pipeline, name=name, value=value, status=MetricStatus.OK)


@pytest.fixture
def throttler():
    from pipewatch.throttle import Throttler
    return Throttler(default_interval_seconds=1.0)


def test_first_check_always_allowed(throttler):
    m = make_metric()
    result = throttler.check(m)
    assert isinstance(result, ThrottleResult)
    assert result.allowed is True


def test_second_check_blocked_within_interval(throttler):
    m = make_metric()
    throttler.check(m)
    result = throttler.check(m)
    assert result.allowed is False


def test_check_allowed_after_interval_passes(throttler):
    throttler2 = Throttler(default_interval_seconds=0.05)
    m = make_metric()
    throttler2.check(m)
    time.sleep(0.1)
    result = throttler2.check(m)
    assert result.allowed is True


def test_to_dict_contains_expected_keys(throttler):
    m = make_metric()
    result = throttler.check(m)
    d = result.to_dict()
    assert "allowed" in d
    assert "key" in d
    assert "next_allowed_at" in d


def test_custom_interval_per_pipeline(throttler):
    throttler.register("pipe", interval_seconds=0.05)
    m = make_metric(pipeline="pipe")
    throttler.check(m)
    time.sleep(0.1)
    result = throttler.check(m)
    assert result.allowed is True


def test_different_pipelines_independent(throttler):
    m1 = make_metric(pipeline="a")
    m2 = make_metric(pipeline="b")
    throttler.check(m1)
    result = throttler.check(m2)
    assert result.allowed is True
