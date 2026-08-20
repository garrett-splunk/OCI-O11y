# OCI → Splunk Observability Cloud Workshop

**Logs:** Connector Hub → OCI Streaming → SOC4Kafka → `otlphttp` → Log Observer  
**Metrics:** Connector Hub → OCI Function → `/v2/datapoint` → Metric Finder

**Workshop site:** [https://garrett-splunk.github.io/OCI-O11y/](https://garrett-splunk.github.io/OCI-O11y/)

## Quick start — logs

```bash
git clone https://github.com/garrett-splunk/OCI-O11y.git
cd OCI-O11y/lab
cp .env.splunk.example .env.splunk   # add your ingest token
./scripts/start.sh
./scripts/produce-oci-logs.sh 10
./scripts/verify-o11y-ingest.sh
```

## Quick start — metrics

```bash
cd lab
./scripts/produce-oci-metrics.sh 5
./scripts/verify-o11y-metrics.sh
```

## Oracle Cloud Compute dashboards

Import `dashboards/dashboard_group_OCC.json`, then populate charts:

```bash
cd lab
./scripts/fill-occ-dashboard.sh 20 30
```

See `lab/OCC_DASHBOARD.md` for OCI integration → Signalflow mapping.

**Splunk filter:** `deployment.environment.name:oci-connector-lab`

## Repo layout

| Path | Purpose |
|------|---------|
| `index.html` | GitHub Pages workshop guide |
| `lab/docker-compose.yml` | Redpanda + OTel Collector (logs path) |
| `lab/collector/otelcol-config.yaml` | kafka → otlphttp logs |
| `lab/functions/oci-metrics-forwarder/` | OCI Function for Monitoring metrics |
| `lab/lib/oci_metrics_transform.py` | Shared OCI → Splunk gauge mapping |
| `lab/OCI_OPTIONAL.md` | Real OCI logs (Streaming) setup |
| `lab/OCI_METRICS.md` | Real OCI metrics (Function) setup |
| `lab/OCC_DASHBOARD.md` | OCC dashboard metric mapping + fill script |
| `dashboards/dashboard_group_OCC.json` | Importable Oracle Cloud Compute dashboard group |
| `WORKSHOP_GUIDE.md` | Facilitator guide |

## Teardown

```bash
cd lab && ./scripts/teardown-lab.sh
```
