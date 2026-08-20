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

Import the dashboard group in Splunk O11y: **Dashboards → Create dashboard group → Import JSON** and select `dashboards/dashboard_group_OCC.json`.

**Splunk reference:** [oci-monitoring-metrics-to-splunk-observability-python](https://github.com/splunk/oracle-cloud-examples-splunk-observability/tree/master/samples/oci-monitoring-metrics-to-splunk-observability-python)

## How metrics reach Splunk O11y (OCI integration)

### Production path

```
OCI Monitoring (oci_computeagent metrics on compute instances)
        ↓
OCI Connector Hub (Monitoring source → Function target)
        ↓
OCI Function (lab/functions/oci-metrics-forwarder/func.py)
  • maps OCI JSON → Splunk O11y /v2/datapoint gauge body
  • adds oci_namespace, oci_dim_*, deployment.environment.name
        ↓
Splunk O11y ingest (/v2/datapoint)
        ↓
Signalflow charts in OCC dashboards (filter oci_namespace = oci_computeagent)
```

### Local lab path (same transform, no OCI tenancy)

```
fixtures/oci-occ-dashboard-metrics.jsonl
        ↓
scripts/send-oci-metrics.py (uses lab/lib/oci_metrics_transform.py)
        ↓
Splunk O11y /v2/datapoint
```

The Python transform is shared with the deployable OCI Function so local runs match production shape.

## Metric and dimension mapping

| OCI Monitoring | Splunk O11y metric | Required dimensions for OCC charts |
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
| Memory Used % | `MemoryUtilization` with `oci_namespace` filter |
| CPU % Trend | raw `CpuUtilization` time series |
| OCC Instance top tiles | `mean(over='5m')` on `CpuUtilization` / `MemoryUtilization` (single-value row) |

Full programs are embedded in `dashboards/dashboard_group_OCC.json`.

## Example dashboards

After `./scripts/fill-occ-dashboard.sh 20 30`, you should see data on both dashboards:

- **OCC Instances** — aggregate CPU %, Memory Used %, disk, and network charts
- **OCC Instance** — pick an instance from the `oci_dim_resourceId` variable; disk and network charts populate immediately; top-row CPU/Memory single-value tiles require the dashboard JSON from this repo

Screenshots are in `images/occ-instances-dashboard.png` and `images/occ-instance-dashboard.png` (also on the workshop site).

## Troubleshooting: OCC Instance single-value tiles

If **CPU Used %** or **Memory Used %** in the top row show no data while lower charts (Memory Used % time series, Disk Iops) work:

1. **Re-import** `dashboards/dashboard_group_OCC.json` — older exports used `.min()` without a namespace filter on memory and `maxDelay: 0`, which often leaves single-value tiles blank with sparse lab data.
2. **Select an instance** in the required `oci_dim_resourceId` dashboard variable (e.g. `ocid1.instance.oc1.iad.workshop-2`).
3. **Keep sending data** with `./scripts/fill-occ-dashboard.sh 20 30` and set the dashboard time picker to **Last 15 minutes**.
4. **Scroll to the top row** — the single-value tiles are easy to miss above the larger charts.
