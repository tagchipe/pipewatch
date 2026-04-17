"""Tests for pipewatch.notifier."""

import time
from unittest.mock import MagicMock

import pytest

from pipewatch.alerts import Alert
from pipewatch.metrics import MetricStatus
from pipewatch.notifier import Notifier, NotifierConfig


def make_alert(pipeline="pipe", metric="rows", status=MetricStatus.WARNING, value=5.0):
    return Alert(pipeline=pipeline, metric_name=metric, status=status, value=value, threshold=10.0)


@pytest.fixture
def handler():
    return MagicMock()


@pytest.fixture
def notifier(handler):
    cfg = NotifierConfig(cooldown_seconds=1.0, max_per_minute=3)
    return Notifier(handler, cfg)


def test_first_send_allowed(notifier, handler):
    alert = make_alert()
    result = notifier.send(alert)
    assert result is True
    handler.assert_called_once_with(alert)


def test_duplicate_blocked_within_cooldown(notifier, handler):
    alert = make_alert()
    notifier.send(alert)
    result = notifier.send(alert)
    assert result is False
    assert handler.call_count == 1


def test_send_allowed_after_cooldown(notifier, handler):
    cfg = NotifierConfig(cooldown_seconds=0.05, max_per_minute=10)
    h = MagicMock()
    n = Notifier(h, cfg)
    alert = make_alert()
    n.send(alert)
    time.sleep(0.1)
    result = n.send(alert)
    assert result is True
    assert h.call_count == 2


def test_rate_limit_max_per_minute(handler):
    cfg = NotifierConfig(cooldown_seconds=0.0, max_per_minute=2)
    n = Notifier(handler, cfg)
    alerts = [make_alert(metric=f"m{i}") for i in range(3)]
    results = [n.send(a) for a in alerts]
    assert results == [True, True, False]


def test_different_keys_independent(notifier, handler):
    a1 = make_alert(metric="rows")
    a2 = make_alert(metric="latency")
    assert notifier.send(a1) is True
    assert notifier.send(a2) is True
    assert handler.call_count == 2


def test_reset_clears_state(notifier, handler):
    alert = make_alert()
    notifier.send(alert)
    notifier.reset()
    result = notifier.send(alert)
    assert result is True
    assert handler.call_count == 2
