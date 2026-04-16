"""Tests for AlertManager and built-in handlers."""

import io
import pytest
from datetime import datetime

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.alerts import Alert, AlertManager
from pipewatch.handlers import console_handler, json_handler, ThresholdFilter


def make_metric(value: float, name: str = "row_count", pipeline: str = "etl") -> PipelineMetric:
    return PipelineMetric(pipeline=pipeline, name=name, value=value, collected_at=datetime.utcnow())


@pytest.fixture
def manager() -> AlertManager:
    return AlertManager()


def test_no_alert_on_ok(manager):
    metric = make_metric(100)
    result = manager.evaluate_and_alert(metric, MetricStatus.OK)
    assert result is None
    assert manager.history == []


def test_alert_on_warning(manager):
    received = []
    manager.register_handler(received.append)
    metric = make_metric(50)
    alert = manager.evaluate_and_alert(metric, MetricStatus.WARNING)
    assert alert is not None
    assert alert.status == MetricStatus.WARNING
    assert len(received) == 1
    assert received[0] is alert


def test_alert_on_critical(manager):
    metric = make_metric(5)
    alert = manager.evaluate_and_alert(metric, MetricStatus.CRITICAL)
    assert alert.status == MetricStatus.CRITICAL
    assert len(manager.history) == 1


def test_history_accumulates(manager):
    for val, status in [(50, MetricStatus.WARNING), (5, MetricStatus.CRITICAL)]:
        manager.evaluate_and_alert(make_metric(val), status)
    assert len(manager.history) == 2


def test_clear_history(manager):
    manager.evaluate_and_alert(make_metric(5), MetricStatus.CRITICAL)
    manager.clear_history()
    assert manager.history == []


def test_console_handler_writes(manager):
    buf = io.StringIO()
    manager.register_handler(lambda a: console_handler(a, stream=buf))
    manager.evaluate_and_alert(make_metric(10), MetricStatus.WARNING)
    output = buf.getvalue()
    assert "WARNING" in output
    assert "etl/row_count" in output


def test_threshold_filter_blocks(manager):
    received = []
    filtered = ThresholdFilter(received.append, [MetricStatus.CRITICAL])
    manager.register_handler(filtered)
    manager.evaluate_and_alert(make_metric(50), MetricStatus.WARNING)
    assert received == []
    manager.evaluate_and_alert(make_metric(5), MetricStatus.CRITICAL)
    assert len(received) == 1
