"""Tests for pipewatch.throttle."""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.throttle import MetricThrottler


def make_metric(pipeline="pipe", name="rows", value=1.0):
    return PipelineMetric(pipeline=pipeline, name=name, value=value, status=MetricStatus.OK)


@pytest.fixture
def throttler():
    return MetricThrottler(default_interval_seconds=60.0)


def test_first_check_always_allowed(throttler):
    result = throttler.check(make_metric())
    assert result.allowed is True
    assert result.next_allowed_at is None


def test_second_check_blocked_within_interval(throttler):
    throttler.check(make_metric())
    result = throttler.check(make_metric())
    assert result.allowed is False
    assert result.next_allowed_at is not None


def test_check_allowed_after_interval_passes(throttler):
    past = datetime.utcnow() - timedelta(seconds=120)
    with patch("pipewatch.throttle.datetime") as mock_dt:
        mock_dt.utcnow.return_value = past
        throttler.check(make_metric())
    result = throttler.check(make_metric())
    assert result.allowed is True


def test_custom_interval_respected():
    throttler = MetricThrottler(default_interval_seconds=10.0)
    throttler.register("pipe", "rows", interval_seconds=5.0)
    throttler.check(make_metric())
    result = throttler.check(make_metric())
    assert result.allowed is False


def test_different_keys_independent(throttler):
    throttler.check(make_metric(pipeline="a"))
    result = throttler.check(make_metric(pipeline="b"))
    assert result.allowed is True


def test_to_dict_shape(throttler):
    result = throttler.check(make_metric())
    d = result.to_dict()
    assert "key" in d
    assert "allowed" in d
    assert "next_allowed_at" in d


def test_blocked_result_next_allowed_is_isoformat(throttler):
    throttler.check(make_metric())
    result = throttler.check(make_metric())
    d = result.to_dict()
    assert d["allowed"] is False
    assert isinstance(d["next_allowed_at"], str)
