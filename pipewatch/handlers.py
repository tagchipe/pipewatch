"""Built-in alert handlers for pipewatch."""

import sys
import json
from typing import TextIO

from pipewatch.alerts import Alert


def console_handler(alert: Alert, stream: TextIO = sys.stderr) -> None:
    """Print alert as a formatted string to stderr (or given stream)."""
    stream.write(
        f"{alert.triggered_at.isoformat()} | {alert.status.value.upper():8s} | "
        f"{alert.pipeline}/{alert.metric_name} = {alert.value}\n"
    )
    stream.flush()


def json_handler(alert: Alert, stream: TextIO = sys.stdout) -> None:
    """Print alert as a JSON line to stdout (or given stream)."""
    stream.write(json.dumps(alert.to_dict()) + "\n")
    stream.flush()


class FileHandler:
    """Append alerts as JSON lines to a file."""

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    def __call__(self, alert: Alert) -> None:
        with open(self.filepath, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(alert.to_dict()) + "\n")


class ThresholdFilter:
    """Wrap a handler so it only fires for specific statuses."""

    def __init__(self, handler, statuses) -> None:
        self._handler = handler
        self._statuses = set(statuses)

    def __call__(self, alert: Alert) -> None:
        if alert.status in self._statuses:
            self._handler(alert)
