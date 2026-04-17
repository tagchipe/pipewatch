"""Scheduled metric collection runs for pipewatch."""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ScheduledJob:
    name: str
    interval_seconds: float
    fn: Callable[[], None]
    _thread: Optional[threading.Thread] = field(default=None, init=False, repr=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, init=False, repr=False)
    _last_run: Optional[float] = field(default=None, init=False, repr=False)

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name=f"pipewatch-{self.name}")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.interval_seconds + 1)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            self.fn()
            self._last_run = time.time()
            self._stop_event.wait(self.interval_seconds)

    @property
    def last_run(self) -> Optional[float]:
        return self._last_run


class Scheduler:
    def __init__(self) -> None:
        self._jobs: dict[str, ScheduledJob] = {}

    def register(self, name: str, interval_seconds: float, fn: Callable[[], None]) -> ScheduledJob:
        job = ScheduledJob(name=name, interval_seconds=interval_seconds, fn=fn)
        self._jobs[name] = job
        return job

    def start_all(self) -> None:
        for job in self._jobs.values():
            job.start()

    def stop_all(self) -> None:
        for job in self._jobs.values():
            job.stop()

    def job_names(self) -> list[str]:
        return list(self._jobs.keys())

    def get(self, name: str) -> Optional[ScheduledJob]:
        return self._jobs.get(name)
