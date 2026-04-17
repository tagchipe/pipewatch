"""CLI commands for baseline deviation checking."""
import json
import click
from pipewatch.baseline import BaselineChecker, BaselineEntry
from pipewatch.metrics import PipelineMetric, MetricStatus
import datetime


def _demo_checker() -> tuple[BaselineChecker, list[PipelineMetric]]:
    checker = BaselineChecker()
    checker.register(BaselineEntry("orders", "row_count", expected=1000.0, tolerance=0.05))
    checker.register(BaselineEntry("orders", "null_rate", expected=0.02, tolerance=0.5))
    checker.register(BaselineEntry("payments", "amount_total", expected=50000.0, tolerance=0.1))

    now = datetime.datetime.utcnow()
    metrics = [
        PipelineMetric("orders", "row_count", 980.0, MetricStatus.OK, now),
        PipelineMetric("orders", "null_rate", 0.08, MetricStatus.WARNING, now),
        PipelineMetric("payments", "amount_total", 48000.0, MetricStatus.OK, now),
    ]
    return checker, metrics


@click.group()
def baseline_cli():
    """Baseline deviation commands."""


@baseline_cli.command("check")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--only-violations", is_flag=True, default=False)
def check_cmd(fmt: str, only_violations: bool):
    """Check metrics against registered baselines."""
    checker, metrics = _demo_checker()
    results = checker.check_all(metrics)

    if only_violations:
        results = [r for r in results if not r.within_baseline]

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return

    if not results:
        click.echo("No baseline results.")
        return

    for r in results:
        status = "OK" if r.within_baseline else "VIOLATION"
        click.echo(
            f"[{status}] {r.metric.pipeline}/{r.metric.name} "
            f"value={r.metric.value} expected={r.expected} "
            f"deviation={r.deviation:.2%} tolerance={r.tolerance:.2%}"
        )
