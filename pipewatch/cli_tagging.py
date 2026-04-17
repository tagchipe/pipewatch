"""CLI commands for metric tagging."""
import click
from pipewatch.tagging import TagManager
from pipewatch.metrics import PipelineMetric, MetricStatus


def _demo_manager() -> TagManager:
    mgr = TagManager()
    metrics = [
        PipelineMetric(name="rows_loaded", pipeline="etl_main", value=5000, status=MetricStatus.OK),
        PipelineMetric(name="error_rate", pipeline="etl_main", value=0.02, status=MetricStatus.WARNING),
        PipelineMetric(name="latency_ms", pipeline="etl_fast", value=320, status=MetricStatus.OK),
    ]
    mgr.tag(metrics[0], ["volume", "etl"])
    mgr.tag(metrics[1], ["quality", "etl"])
    mgr.tag(metrics[2], ["perf", "etl"])
    return mgr


@click.group(name="tags")
def tagging_cli():
    """Manage and query metric tags."""


@tagging_cli.command(name="list")
def list_tags_cmd():
    """List all known tags."""
    mgr = _demo_manager()
    tags = sorted(mgr.all_tags())
    if not tags:
        click.echo("No tags registered.")
        return
    for tag in tags:
        metrics = mgr.by_tag(tag)
        names = ", ".join(m.name for m in metrics)
        click.echo(f"  [{tag}] -> {names}")


@tagging_cli.command(name="filter")
@click.argument("tag")
def filter_cmd(tag: str):
    """Show metrics matching TAG."""
    mgr = _demo_manager()
    metrics = mgr.by_tag(tag)
    if not metrics:
        click.echo(f"No metrics found for tag '{tag}'.")
        return
    for m in metrics:
        click.echo(f"  {m.name} ({m.pipeline}) — {m.status.value}")
