"""Tests for pipewatch.scheduler."""

import time
import pytest
from pipewatch.scheduler import Scheduler, ScheduledJob


@pytest.fixture
def scheduler():
    s = Scheduler()
    yield s
    s.stop_all()


def test_register_returns_job(scheduler):
    job = scheduler.register("test", 60, lambda: None)
    assert isinstance(job, ScheduledJob)
    assert job.name == "test"
    assert job.interval_seconds == 60


def test_job_names(scheduler):
    scheduler.register("alpha", 10, lambda: None)
    scheduler.register("beta", 20, lambda: None)
    assert set(scheduler.job_names()) == {"alpha", "beta"}


def test_get_existing_job(scheduler):
    scheduler.register("myjob", 5, lambda: None)
    job = scheduler.get("myjob")
    assert job is not None
    assert job.name == "myjob"


def test_get_missing_job(scheduler):
    assert scheduler.get("nope") is None


def test_job_runs_fn(scheduler):
    counter = {"n": 0}

    def increment():
        counter["n"] += 1

    job = scheduler.register("counter", 0.05, increment)
    job.start()
    time.sleep(0.2)
    job.stop()
    assert counter["n"] >= 2


def test_last_run_updated(scheduler):
    job = scheduler.register("ts", 0.05, lambda: None)
    assert job.last_run is None
    job.start()
    time.sleep(0.15)
    job.stop()
    assert job.last_run is not None


def test_start_all_stop_all(scheduler):
    results = []
    scheduler.register("a", 0.05, lambda: results.append("a"))
    scheduler.register("b", 0.05, lambda: results.append("b"))
    scheduler.start_all()
    time.sleep(0.2)
    scheduler.stop_all()
    assert "a" in results
    assert "b" in results
