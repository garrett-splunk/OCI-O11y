# OCI Metrics → Splunk O11y Workshop

**Primary path:** Connector Hub → OCI Function → `/v2/datapoint` → Metric Finder & dashboards  
**Optional:** Logs via Streaming + OTel Collector (requires Splunk Cloud/Enterprise for Log Observer)

**Splunk reference:** [oci-monitoring-metrics-to-splunk-observability-python](https://github.com/splunk/oracle-cloud-examples-splunk-observability/tree/master/samples/oci-monitoring-metrics-to-splunk-observability-python) (`splunk/oracle-cloud-examples-splunk-observability`)

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

**Splunk O11y filter (local lab):** `deployment.environment.name:oci-connector-lab`

**Splunk O11y filter (live OCI tenancy):** `deployment.environment.name:oci-workshop-live` (after step 6 in `lab/OCI_METRICS.md`)

## Connect a real OCI tenancy (step 6)

Local scripts mirror `func.py` on OCI Functions. To use live Monitoring data instead of fixtures:

1. Confirm metrics in OCI **Metrics Explorer** (`oci_computeagent`)
2. Deploy `lab/functions/oci-metrics-forwarder/` with Fn CLI
3. Create Connector Hub: **Monitoring → Function**
4. Verify in Splunk O11y with real instance OCIDs (stop local fill script to prove it is live)

See `lab/OCI_METRICS.md` for CLI commands and verification steps.

## Optional — logs path

Requires **Docker** and a Splunk O11y org with **Log Observer** linked to Splunk Cloud or Enterprise.

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
| `lab/scripts/metrics-lab.sh` | Metrics-only lab (no Docker) |
| `lab/scripts/fill-occ-dashboard.sh` | Populate OCC dashboard charts |
| `lab/functions/oci-metrics-forwarder/` | OCI Function for Monitoring metrics |
| `lab/lib/oci_metrics_transform.py` | Shared OCI → Splunk O11y gauge mapping |
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
