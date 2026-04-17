import json
import click
from pipewatch.anomaly import AnomalyDetector
from pipewatch.metrics import PipelineMetric, MetricStatus


def _demo_detector() -> tuple[AnomalyDetector, list[PipelineMetric]]:
    detector = AnomalyDetector(threshold=2.0, min_samples=3)
    baseline = [
        PipelineMetric(name="latency", value=v, pipeline="etl_main", status=MetricStatus.OK)
        for v in [100.0, 102.0, 98.0, 101.0, 99.0]
    ]
    for m in baseline:
        detector.record(m)
    probes = [
        PipelineMetric(name="latency", value=101.0, pipeline="etl_main", status=MetricStatus.OK),
        PipelineMetric(name="latency", value=300.0, pipeline="etl_main", status=MetricStatus.CRITICAL),
    ]
    return detector, probes


@click.group()
def anomaly_cli():
    """Anomaly detection commands."""


@anomaly_cli.command("check")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
@click.option("--only-anomalies", is_flag=True, default=False, help="Show only anomalous metrics.")
def check_cmd(fmt: str, only_anomalies: bool):
    """Run anomaly detection on demo metrics."""
    detector, probes = _demo_detector()
    results = []
    for metric in probes:
        result = detector.check(metric)
        if result is None:
            continue
        if only_anomalies and not result.is_anomaly:
            continue
        results.append(result)

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            flag = "ANOMALY" if r.is_anomaly else "OK"
            click.echo(
                f"[{flag}] {r.pipeline}/{r.metric_name} "
                f"value={r.value} mean={r.mean:.2f} z={r.z_score:.2f}"
            )
    if any(r.is_anomaly for r in results):
        raise SystemExit(1)
