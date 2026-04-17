"""Tests for pipewatch.silencer."""

from datetime import datetime, timedelta

import pytest

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.alerts import Alert
from pipewatch.silencer import Silencer, SilenceRule


def make_alert(name="rows_loaded", pipeline="etl", status=MetricStatus.WARNING):
    metric = PipelineMetric(name=name, value=5.0, pipeline=pipeline, status=status)
    return Alert(metric=metric, message="test alert")


@pytest.fixture
def silencer():
    return Silencer()


def test_not_silenced_by_default(silencer):
    assert silencer.is_silenced("rows_loaded") is False


def test_silence_blocks_key(silencer):
    silencer.silence("rows_loaded", duration_seconds=60)
    assert silencer.is_silenced("rows_loaded") is True


def test_expired_rule_not_silenced(silencer):
    past = datetime.utcnow() - timedelta(seconds=1)
    rule = SilenceRule(key="rows_loaded", expires_at=past)
    silencer._rules["rows_loaded"] = rule
    assert silencer.is_silenced("rows_loaded") is False


def test_allow_passes_unsilenced_alert(silencer):
    alert = make_alert()
    assert silencer.allow(alert) is True


def test_allow_blocks_silenced_metric(silencer):
    silencer.silence("rows_loaded", 120)
    alert = make_alert(name="rows_loaded")
    assert silencer.allow(alert) is False


def test_allow_blocks_silenced_pipeline(silencer):
    silencer.silence("etl", 120)
    alert = make_alert(pipeline="etl")
    assert silencer.allow(alert) is False


def test_active_rules_returns_only_active(silencer):
    silencer.silence("a", 120, reason="planned maintenance")
    past = datetime.utcnow() - timedelta(seconds=1)
    silencer._rules["b"] = SilenceRule(key="b", expires_at=past)
    active = silencer.active_rules()
    assert len(active) == 1
    assert active[0].key == "a"


def test_clear_removes_rule(silencer):
    silencer.silence("rows_loaded", 60)
    removed = silencer.clear("rows_loaded")
    assert removed is True
    assert silencer.is_silenced("rows_loaded") is False


def test_clear_missing_returns_false(silencer):
    assert silencer.clear("nonexistent") is False
