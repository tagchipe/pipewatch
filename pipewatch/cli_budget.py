"""CLI for pipeline violation budget tracking."""
import json
import click
from pipewatch.budget import BudgetTracker
from pipewatch.metrics import PipelineMetric, MetricStatus


def _demo_tracker() -> tuple[BudgetTracker, list[PipelineMetric]]:
    tracker = BudgetTracker(default_max=3, default_window=3600.0)
    tracker.register("ingest", max_violations=2, window_seconds=3600.0)
    metrics = [
        PipelineMetric(name="rows", pipeline="ingest", value=0, status=MetricStatus.CRITICAL),
        PipelineMetric(name="rows", pipeline="ingest", value=0, status=MetricStatus.WARNING),
        PipelineMetric(name="rows", pipeline="ingest", value=0, status=MetricStatus.CRITICAL),
        PipelineMetric(name="lag", pipeline="transform", value=5, status=MetricStatus.WARNING),
    ]
    return tracker, metrics


@click.group(name="budget")
def budget_cli() -> None:
    """Pipeline violation budget commands."""


@budget_cli.command(name="check")
@click.option("--pipeline", default=None, help="Filter to a single pipeline.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def check_cmd(pipeline: str | None, as_json: bool) -> None:
    """Check violation budgets for all (or one) pipeline."""
    tracker, metrics = _demo_tracker()
    for m in metrics:
        tracker.ingest(m)

    pipelines = [pipeline] if pipeline else ["ingest", "transform"]
    results = [tracker.check(p) for p in pipelines]

    if as_json:
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            status = "EXCEEDED" if r.exceeded else "OK"
            click.echo(
                f"{r.pipeline}: {r.violation_count}/{r.max_violations} violations [{status}]"
            )
