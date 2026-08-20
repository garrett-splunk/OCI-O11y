# OCI Metrics → Splunk Observability Cloud Workshop

**Primary path:** Connector Hub → OCI Function → `/v2/datapoint` → Metric Finder & dashboards  
**Optional:** Logs via Streaming + OTel Collector (requires Splunk Cloud/Enterprise for Log Observer)

**Workshop site:** [https://garrett-splunk.github.io/OCI-O11y/](https://garrett-splunk.github.io/OCI-O11y/)

## Quick start — metrics only (no Docker)

```bash
git clone https://github.com/garrett-splunk/OCI-O11y.git
cd OCI-O11y/lab
cp .env.splunk.example .env.splunk   # US1: ingest.us1.signalfx.com + ingest token
./scripts/metrics-lab.sh 20 30
```

Or step by step:

```bash
./scripts/produce-oci-metrics.sh 5
./scripts/verify-o11y-metrics.sh
./scripts/fill-occ-dashboard.sh 20 30
```

## Oracle Cloud Compute dashboards

Import `dashboards/dashboard_group_OCC.json`, then run `./scripts/fill-occ-dashboard.sh 20 30`.

See `lab/OCC_DASHBOARD.md` for OCI integration → Signalflow mapping.

**Splunk filter:** `deployment.environment.name:oci-connector-lab`

## Optional — logs path

Requires **Docker** and a Splunk org with **Log Observer** linked to Splunk Cloud or Enterprise.

```bash
cd lab
./scripts/start.sh
./scripts/produce-oci-logs.sh 10
./scripts/verify-o11y-ingest.sh
```

See `lab/OCI_OPTIONAL.md`.

## Repo layout

| Path | Purpose |
|------|---------|
| `index.html` | GitHub Pages workshop guide (metrics-first) |
| `lab/scripts/metrics-lab.sh` | Metrics-only lab (no Docker) |
| `lab/scripts/fill-occ-dashboard.sh` | Populate OCC dashboard charts |
| `lab/functions/oci-metrics-forwarder/` | OCI Function for Monitoring metrics |
| `lab/lib/oci_metrics_transform.py` | Shared OCI → Splunk gauge mapping |
| `lab/OCI_METRICS.md` | Real OCI metrics (Function) setup |
| `lab/OCC_DASHBOARD.md` | OCC dashboard metric mapping |
| `dashboards/dashboard_group_OCC.json` | Importable Oracle Cloud Compute dashboard group |
| `lab/docker-compose.yml` | Optional: Redpanda + OTel Collector (logs appendix) |
| `lab/OCI_OPTIONAL.md` | Optional logs (Streaming) setup |
| `WORKSHOP_GUIDE.md` | Facilitator guide |

## Teardown

Metrics-only: stop `fill-occ-dashboard.sh` with Ctrl+C.

If you ran the logs appendix:

```bash
cd lab && ./scripts/teardown-lab.sh
```
