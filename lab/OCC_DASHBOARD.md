# Oracle Cloud Compute (OCC) dashboards

This lab can populate the **Oracle Cloud Compute** dashboard group shipped in `dashboards/dashboard_group_OCC.json`.

## Quick start

```bash
cd lab
cp .env.splunk.example .env.splunk   # set SPLUNK_ACCESS_TOKEN + SPLUNK_INGEST_URL

# One-shot sample (5 metrics)
./scripts/produce-oci-metrics.sh 5

# Fill OCC dashboards (~10 minutes of data at default settings)
./scripts/fill-occ-dashboard.sh 20 30
```

Import the dashboard group in Observability Cloud: **Dashboards → Create dashboard group → Import JSON** and select `dashboards/dashboard_group_OCC.json`.

## How metrics reach Splunk (OCI integration)

### Production path

```
OCI Monitoring (oci_computeagent metrics on compute instances)
        ↓
OCI Connector Hub (Monitoring source → Function target)
        ↓
OCI Function (lab/functions/oci-metrics-forwarder/func.py)
  • maps OCI JSON → Splunk /v2/datapoint gauge body
  • adds oci_namespace, oci_dim_*, deployment.environment.name
        ↓
Splunk Observability Cloud ingest (/v2/datapoint)
        ↓
Signalflow charts in OCC dashboards (filter oci_namespace = oci_computeagent)
```

### Local lab path (same transform, no OCI tenancy)

```
fixtures/oci-occ-dashboard-metrics.jsonl
        ↓
scripts/send-oci-metrics.py (uses lab/lib/oci_metrics_transform.py)
        ↓
Splunk Observability Cloud /v2/datapoint
```

The Python transform is shared with the deployable OCI Function so local runs match production shape.

## Metric and dimension mapping

| OCI Monitoring | Splunk metric | Required dimensions for OCC charts |
|----------------|---------------|-----------------------------------|
| `namespace: oci_computeagent` | dimension `oci_namespace` | Always filter `oci_computeagent` |
| `name: CpuUtilization` | `CpuUtilization` | `oci_dim_resourceId`, `oci_dim_resourceDisplayName`, `oci_dim_imageId`, `oci_dim_shape`, `oci_dim_availabilityDomain`, `oci_dim_instancePoolId` |
| `name: MemoryUtilization` | `MemoryUtilization` | `oci_dim_resourceId`, `oci_dim_resourceDisplayName` |
| `name: MemoryAllocationStalls` | `MemoryAllocationStalls` | `oci_dim_resourceId` |
| `name: LoadAverage` | `LoadAverage` | `oci_dim_resourceId` |
| `name: DiskIopsRead` / `DiskIopsWritten` | same | Cumulative-style values; charts use `.delta()` |
| `name: DiskBytesRead` / `DiskBytesWritten` | same | Cumulative-style values; charts use `.delta()` |
| `name: NetworksBytesIn` / `NetworksBytesOut` | same | Cumulative-style values; charts use `.delta()` |

Lab transform also sets:

- `deployment.environment.name` — default `oci-connector-lab` (override with `DEPLOYMENT_ENVIRONMENT`)
- `cloud.provider: oci`
- `oci_compartment_id`, `oci_unit`, `oci_display_name` when present in OCI payload

## Why `fill-occ-dashboard.sh` loops

Many OCC charts call Signalflow `.delta()` on disk and network metrics. Those expect **monotonically increasing counter-like values** over time. The fill script:

1. Sends all fixture metrics in one batch per iteration (`--batch-all`)
2. Multiplies counter metric values by iteration number (`--increment-counters`)
3. Waits 30 seconds between iterations (configurable) so time-series charts have multiple points

Gauge metrics (CPU, memory) get a small sine-wave variation so percentile charts move without leaving valid ranges.

## Verify in O11y

```bash
./scripts/verify-o11y-metrics.sh
```

Metric Finder examples:

- `CpuUtilization` + filter `oci_namespace:oci_computeagent`
- `NetworksBytesIn` with `deployment.environment.name:oci-connector-lab`
- Group by `oci_dim_resourceDisplayName`

## Dashboard charts (Signalflow reference)

| Dashboard chart | Signalflow pattern |
|-----------------|-------------------|
| Top Instances by CPU % | `data('CpuUtilization', filter=filter('oci_namespace', 'oci_computeagent'))` |
| Active Hosts | count by `oci_dim_resourceId` |
| Disk Iops | `DiskIopsRead` / `DiskIopsWritten` with `.delta()` |
| Network Bytes In/Out | `NetworksBytesIn` / `NetworksBytesOut` with `.delta()` |
| Memory Used % | `MemoryUtilization` |
| CPU % Trend | raw `CpuUtilization` time series |

Full programs are embedded in `dashboards/dashboard_group_OCC.json`.
