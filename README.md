# pipewatch

A lightweight CLI for monitoring and alerting on ETL pipeline health metrics.

---

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/yourname/pipewatch.git && cd pipewatch && pip install -e .
```

---

## Usage

Monitor a pipeline by pointing pipewatch at your metrics endpoint or log source:

```bash
pipewatch monitor --source postgres://user:pass@host/db --pipeline my_etl_job
```

Set alert thresholds and receive notifications when metrics fall outside expected ranges:

```bash
pipewatch watch \
  --pipeline daily_ingest \
  --max-latency 300 \
  --min-rows 1000 \
  --alert-email ops@example.com
```

Check the status of all tracked pipelines at a glance:

```bash
pipewatch status
```

For a full list of commands and options:

```bash
pipewatch --help
```

---

## Features

- Real-time latency and row count monitoring
- Configurable alert thresholds with email and webhook notifications
- Simple YAML-based pipeline configuration
- Supports PostgreSQL, MySQL, and file-based sources

---

## License

This project is licensed under the [MIT License](LICENSE).