"""CLI command to display per-pipeline health status."""
import json
import click
from pipewatch.pipeline_status import PipelineStatusBoard
from pipewatch.cli import _build_demo_collector
from pipewatch.metrics import MetricStatus

STATUS_COLOR = {
    MetricStatus.OK: "green",
    MetricStatus.WARNING: "yellow",
    MetricStatus.CRITICAL: "red",
}


def _build_board() -> PipelineStatusBoard:
    collector = _build_demo_collector()
    metrics = collector.all_metrics()
    board = PipelineStatusBoard()
    board.ingest(metrics)
    return board


@click.group(name="pipeline-status")
def pipeline_status_cli():
    """Per-pipeline health status commands."""


@pipeline_status_cli.command(name="list")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--critical-only", is_flag=True, default=False)
def list_cmd(fmt: str, critical_only: bool):
    """List all pipeline statuses."""
    board = _build_board()
    pipelines = board.critical_pipelines() if critical_only else board.all()

    if fmt == "json":
        click.echo(json.dumps([p.to_dict() for p in pipelines], indent=2))
        return

    if not pipelines:
        click.echo("No pipelines found.")
        return

    for ps in pipelines:
        color = STATUS_COLOR.get(ps.overall_status, "white")
        label = ps.overall_status.value.upper()
        click.echo(f"[{click.style(label, fg=color)}] {ps.pipeline} ({len(ps.metrics)} metrics)")
        for m in ps.metrics:
            mc = STATUS_COLOR.get(m.status, "white")
            click.echo(f"    {m.name}: {m.value} [{click.style(m.status.value, fg=mc)}]")
