"""Tests for AlertDeduplicator."""
import time
import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.alerts import Alert
from pipewatch.deduplicator import AlertDeduplicator


def make_alert(name="row_count", pipeline="etl", status=MetricStatus.WARNING) -> Alert:
    metric = PipelineMetric(name=name, value=5.0, pipeline=pipeline, status=status)
    return Alert(metric=metric, message="test alert")


@pytest.fixture
def dedup() -> AlertDeduplicator:
    return AlertDeduplicator(window_seconds=1.0)


def test_first_alert_not_duplicate(dedup):
    alert = make_alert()
    assert dedup.is_duplicate(alert) is False


def test_second_alert_is_duplicate(dedup):
    alert = make_alert()
    dedup.is_duplicate(alert)
    assert dedup.is_duplicate(alert) is True


def test_duplicate_increments_count(dedup):
    alert = make_alert()
    dedup.is_duplicate(alert)
    dedup.is_duplicate(alert)
    entry = dedup.entry(alert)
    assert entry is not None
    assert entry.count == 2


def test_different_status_not_duplicate(dedup):
    a1 = make_alert(status=MetricStatus.WARNING)
    a2 = make_alert(status=MetricStatus.CRITICAL)
    dedup.is_duplicate(a1)
    assert dedup.is_duplicate(a2) is False


def test_expired_entry_not_duplicate():
    dedup = AlertDeduplicator(window_seconds=0.05)
    alert = make_alert()
    dedup.is_duplicate(alert)
    time.sleep(0.1)
    assert dedup.is_duplicate(alert) is False


def test_reset_clears_entry(dedup):
    alert = make_alert()
    dedup.is_duplicate(alert)
    dedup.reset(alert)
    assert dedup.is_duplicate(alert) is False


def test_clear_removes_all(dedup):
    dedup.is_duplicate(make_alert(name="a"))
    dedup.is_duplicate(make_alert(name="b"))
    dedup.clear()
    assert dedup.is_duplicate(make_alert(name="a")) is False
