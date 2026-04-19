import time
import pytest
from unittest.mock import MagicMock
from pipewatch.alerts import Alert
from pipewatch.metrics import MetricStatus
from pipewatch.escalation import EscalationManager


def make_alert(pipeline="pipe_a", metric="row_count", status=MetricStatus.WARNING) -> Alert:
    return Alert(pipeline=pipeline, metric_name=metric, status=status, value=5.0, message="test alert")


@pytest.fixture
def manager() -> EscalationManager:
    return EscalationManager()


def test_first_check_not_escalated(manager):
    alert = make_alert()
    result = manager.check(alert)
    assert result.escalated is False
    assert result.level == 0


def test_escalates_after_threshold(manager):
    handler = MagicMock()
    manager.add_level(level=1, handler=handler, after_seconds=0.05)
    alert = make_alert()
    manager.check(alert)  # register
    time.sleep(0.07)
    result = manager.check(alert)
    assert result.escalated is True
    assert result.level == 1
    handler.assert_called_once_with(alert)


def test_does_not_re_escalate_same_level(manager):
    handler = MagicMock()
    manager.add_level(level=1, handler=handler, after_seconds=0.05)
    alert = make_alert()
    manager.check(alert)
    time.sleep(0.07)
    manager.check(alert)  # escalates
    result = manager.check(alert)  # should not re-escalate
    assert result.escalated is False
    assert handler.call_count == 1


def test_escalates_through_levels(manager):
    h1, h2 = MagicMock(), MagicMock()
    manager.add_level(level=1, handler=h1, after_seconds=0.03)
    manager.add_level(level=2, handler=h2, after_seconds=0.08)
    alert = make_alert()
    manager.check(alert)
    time.sleep(0.05)
    r1 = manager.check(alert)
    assert r1.level == 1 and r1.escalated is True
    time.sleep(0.06)
    r2 = manager.check(alert)
    assert r2.level == 2 and r2.escalated is True


def test_resolve_clears_state(manager):
    handler = MagicMock()
    manager.add_level(level=1, handler=handler, after_seconds=0.0)
    alert = make_alert()
    manager.check(alert)
    manager.resolve(alert)
    result = manager.check(alert)  # fresh start
    assert result.escalated is False
    assert result.level == 0


def test_result_to_dict(manager):
    alert = make_alert()
    result = manager.check(alert)
    d = result.to_dict()
    assert d["pipeline"] == "pipe_a"
    assert d["metric"] == "row_count"
    assert "escalated" in d
