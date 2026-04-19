"""CLI for demonstrating alert routing."""
import json
import click
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.alerts import Alert
from pipewatch.routing import AlertRouter


def _demo_router() -> AlertRouter:
    router = AlertRouter()
    router.add_route(
        lambda a: None,
        pipeline="ingest",
        statuses=[MetricStatus.CRITICAL],
        name="ingest-critical",
    )
    router.add_route(
        lambda a: None,
        statuses=[MetricStatus.WARNING, MetricStatus.CRITICAL],
        name="all-warn-crit",
    )
    router.add_route(lambda a: None, name="catch-all")
    return router


def _demo_alerts():
    def _a(pipeline, status):
        m = PipelineMetric(name="row_count", pipeline=pipeline, value=1.0, status=status)
        return Alert(metric=m, message=f"{pipeline} {status.value}")

    return [
        _a("ingest", MetricStatus.CRITICAL),
        _a("ingest", MetricStatus.WARNING),
        _a("transform", MetricStatus.WARNING),
        _a("transform", MetricStatus.OK),
    ]


@click.group(name="routing")
def routing_cli():
    """Alert routing commands."""


@routing_cli.command(name="demo")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def demo_cmd(fmt: str):
    """Run demo alert routing and show dispatch results."""
    router = _demo_router()
    results = [router.dispatch(a) for a in _demo_alerts()]
    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            click.echo(
                f"alert={r.alert.metric.pipeline}/{r.alert.metric.status.value} "
                f"dispatched={r.dispatched} routes={r.matched_routes}"
            )
