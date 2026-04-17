"""CLI commands for managing scheduled metric collection."""

from __future__ import annotations

import time
import signal
import click

from pipewatch.scheduler import Scheduler
from pipewatch.cli import _build_demo_collector
from pipewatch.reporter import Reporter


def _make_scheduler(interval: float, output_format: str) -> Scheduler:
    scheduler = Scheduler()
    collector = _build_demo_collector()
    reporter = Reporter(collector)

    def run_report():
        report = reporter.build()
        if output_format == "json":
            click.echo(report.to_json())
        else:
            for name, status in report.statuses.items():
                click.echo(f"{name}: {status}")

    scheduler.register("report", interval, run_report)
    return scheduler


@click.group()
def scheduler_cli():
    """Scheduler commands for pipewatch."""


@scheduler_cli.command("run")
@click.option("--interval", default=10.0, show_default=True, help="Seconds between collection runs.")
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]), show_default=True)
@click.option("--duration", default=0.0, help="Run for N seconds then exit (0 = run until Ctrl-C).")
def run_cmd(interval: float, output_format: str, duration: float):
    """Start scheduled metric collection."""
    scheduler = _make_scheduler(interval, output_format)
    scheduler.start_all()
    click.echo(f"Scheduler started (interval={interval}s). Press Ctrl-C to stop.")

    stop = [False]

    def _handler(sig, frame):
        stop[0] = True

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)

    start = time.time()
    while not stop[0]:
        if duration > 0 and (time.time() - start) >= duration:
            break
        time.sleep(0.1)

    scheduler.stop_all()
    click.echo("Scheduler stopped.")
