# OCI Monitoring metrics → Splunk O11y

Two paths: **local lab** (fixture simulator on your laptop) and **production** (same code running on **OCI Functions**, fed by real Monitoring data).

**Splunk reference:** [oci-monitoring-metrics-to-splunk-observability-python](https://github.com/splunk/oracle-cloud-examples-splunk-observability/tree/master/samples/oci-monitoring-metrics-to-splunk-observability-python)

## Local lab vs OCI production

Steps 3–5 of the workshop run scripts **on your laptop**. Step 6 moves the **same transform and forward logic** into your OCI tenancy so Connector Hub invokes it with live Monitoring payloads.

| Workshop step | Local lab (laptop) | Production (OCI tenancy) |
|---------------|-------------------|---------------------------|
| Transform OCI JSON → Splunk `gauge` | `lab/lib/oci_metrics_transform.py` | Same module in `functions/oci-metrics-forwarder/` |
| Forward to Splunk O11y | `scripts/send-oci-metrics.py` | `func.py` on **OCI Functions** |
| Metric source | `fixtures/*.jsonl` (demo data) | **OCI Monitoring** on real compute / VCN / LB |
| Trigger | You run `./scripts/fill-occ-dashboard.sh` | **Connector Hub** (Monitoring → Function) |
| Splunk auth | `lab/.env.splunk` | Function env `SPLUNK_O11Y_TOKEN` |
| Tell lab vs live apart | `deployment.environment.name:oci-connector-lab` | Set `DEPLOYMENT_ENVIRONMENT=oci-workshop-live` (or your prod tag) |
| Instance IDs | `ocid1.instance.oc1.iad.workshop-*` (fixtures) | Real OCIDs from **Compute → Instances** |

The local scripts are **not** a different integration — they exercise the same `/v2/datapoint` payload shape the Function sends in production.

## Production architecture

```
OCI Monitoring (oci_computeagent, oci_vcn, …)
        ↓
Connector Hub (Monitoring source → Function target)
        ↓
oci-metrics-forwarder (OCI Function — func.py)
        ↓ transform_payload() → gauge[]
        ↓
POST https://ingest.{realm}.signalfx.com/v2/datapoint
        ↓
Splunk O11y — Metric Finder & OCC dashboards
```

Connector Hub does **not** send Splunk O11y-native metrics directly. The Function maps OCI payloads to Splunk O11y `gauge` datapoints with dimensions (`oci_namespace`, `oci_dim_*`, etc.).

---

## Additional steps to connect a real OCI tenancy

Complete these **after** steps 1–5 (local lab) or instead of running `fill-occ-dashboard.sh` once the connector is active.

### 0. Prerequisites

| Requirement | Notes |
|-------------|--------|
| OCI tenancy | Admin or delegated access to create Functions, Connector Hub, policies |
| Compartment | Workshop resources (Function app, connector, compute) |
| VCN + subnet | Subnet must allow **egress HTTPS** to Splunk ingest (internet or NAT gateway) |
| Compute instance(s) | At least one VM with **Monitoring enabled** (`oci_computeagent` metrics) |
| Splunk O11y ingest token | Same token type as the lab (`/v2/datapoint` scope) |
| OCI CLI | `oci setup config` completed |
| Fn CLI | [Install Fn CLI](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsinstallfncli.htm) and `fn update context` pointed at your region |

### 1. Confirm OCI Monitoring is producing metrics

Before deploying the Function, prove the tenancy already has monitoring data.

**Console:** **Observability & Management → Monitoring → Metrics Explorer**

- Namespace: `oci_computeagent`
- Metric: `CpuUtilization` or `MemoryUtilization`
- Resource: pick a **real** compute instance OCID

**CLI:**

```bash
export COMPARTMENT_OCID="<your-compartment-ocid>"
export INSTANCE_OCID="<real-compute-instance-ocid>"

oci compute instance list --compartment-id "$COMPARTMENT_OCID" --output table

oci monitoring metric-data summarize-metrics-data \
  --compartment-id "$COMPARTMENT_OCID" \
  --namespace oci_computeagent \
  --query-text "CpuUtilization[1m]{resourceId = \"$INSTANCE_OCID\"}.mean()" \
  --start-time "$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

If Metrics Explorer shows data, OCI is the source of truth — Splunk should mirror it after the connector runs.

### 2. Deploy the OCI Function (same code as the lab)

The forwarder lives in `lab/functions/oci-metrics-forwarder/`. It shares `oci_metrics_transform.py` with `lab/lib/`.

```bash
cd lab/functions/oci-metrics-forwarder

# One-time: create Functions application in your compartment/subnet
fn create app oci-o11y-workshop \
  --annotation oracle.com/oci/subnetIds='["<subnet-ocid>"]'

# Deploy function code to OCI
fn deploy --app oci-o11y-workshop
```

### 3. Configure Function environment variables

Use a **distinct** environment tag so live metrics do not mix with lab fixtures:

```bash
fn config function oci-o11y-workshop oci-metrics-forwarder SPLUNK_O11Y_TOKEN "<ingest-token>"
fn config function oci-o11y-workshop oci-metrics-forwarder SPLUNK_O11Y_REALM "us1"
fn config function oci-o11y-workshop oci-metrics-forwarder DEPLOYMENT_ENVIRONMENT "oci-workshop-live"
fn config function oci-o11y-workshop oci-metrics-forwarder FORWARD_TO_SPLUNK "true"
fn config function oci-o11y-workshop oci-metrics-forwarder LOGGING_LEVEL "INFO"
```

Optional: `SPLUNK_INGEST_URL` if you need a full ingest host override (same as lab `SPLUNK_INGEST_URL`).

| Variable | Default | Purpose |
|----------|---------|---------|
| `SPLUNK_O11Y_REALM` | `us0` | Realm for ingest URL (`ingest.{realm}.signalfx.com`) |
| `SPLUNK_O11Y_TOKEN` | — | Splunk O11y ingest token (required) |
| `SPLUNK_INGEST_URL` | — | Optional full ingest base URL override |
| `DEPLOYMENT_ENVIRONMENT` | `oci-connector-lab` | Becomes `deployment.environment.name` — use **`oci-workshop-live`** for real tenancy |
| `FORWARD_TO_SPLUNK` | `true` | Set `false` for transform-only tests |
| `LOGGING_LEVEL` | `INFO` | Function logging |

### 4. Create Connector Hub (Monitoring → Function)

**Console:** **Observability & Management → Connector Hub → Create connector**

1. **Name:** e.g. `oci-metrics-to-splunk-o11y`
2. **Source:** **Monitoring**
   - Compartment: where your instances / metrics live
   - Namespace: start with **`oci_computeagent`** (OCC dashboards); add `oci_vcn` later if needed
3. **Target:** **Functions**
   - Application: `oci-o11y-workshop`
   - Function: `oci-metrics-forwarder`
4. **Policies:** allow Connector Hub to create IAM policies (metrics read + Function invoke), or attach equivalent policies manually.

**Deploy order:** Function **must** exist before the connector — same rule as the workshop teaches for production.

### 5. Verify the pipeline in OCI

| Check | Where | Healthy signal |
|-------|--------|----------------|
| Connector state | Connector Hub → your connector | **Active**, recent metric deliveries |
| Function invocations | **Functions → oci-metrics-forwarder** | Invoke count increasing |
| Function logs | Function → **Logs** | `Transformed OCI metric …` and `Forwarded N gauge points -> HTTP 200` |
| Source metrics | Metrics Explorer | Still showing data for your instance OCID |

### 6. Verify in Splunk O11y (prove it is not fixture data)

1. **Stop** any local `./scripts/fill-occ-dashboard.sh` on your laptop.
2. Open **Metric Finder**:
   - Metric: `CpuUtilization`
   - Filter: `deployment.environment.name:oci-workshop-live` and `oci_namespace:oci_computeagent`
   - Group by: `oci_dim_resourceId`
3. Confirm OCIDs match **Compute → Instances** in OCI Console (not `workshop-1` fixture IDs).
4. Compare a value at the same timestamp with **Metrics Explorer** in OCI.

Import `dashboards/dashboard_group_OCC.json` and on **OCC Instance** select a **real** `oci_dim_resourceId`. Data should continue after the local script is stopped.

### 7. Optional — run lab and live side by side

| Source | Filter in Splunk O11y |
|--------|------------------------|
| Local fixtures | `deployment.environment.name:oci-connector-lab` |
| OCI tenancy | `deployment.environment.name:oci-workshop-live` |

Use separate dashboard filters or variables so attendees see demo data and live tenancy data without confusion.

---

## OCI → Splunk O11y mapping

| OCI field | Splunk O11y field |
|-----------|--------------|
| `name` | `metric` |
| `datapoints[].value` | `value` |
| `datapoints[].timestamp` | `timestamp` (ms) |
| `namespace` | dimension `oci_namespace` |
| `compartmentId` | dimension `oci_compartment_id` |
| `metadata.unit` | dimension `oci_unit` |
| `dimensions.*` | dimension `oci_dim_<name>` |
| (Function env) | `deployment.environment.name` |

## Local lab (no OCI tenancy required)

Simulates the Function transform and POSTs to your Splunk O11y org:

```bash
cd lab
./scripts/produce-oci-metrics.sh 5
./scripts/verify-o11y-metrics.sh
./scripts/fill-occ-dashboard.sh 20 30
```

**Metric Finder:** `CpuUtilization`, filter `deployment.environment.name:oci-connector-lab`

## Contrast with logs path

| | Logs (Streaming lab) | Metrics (this doc) |
|--|----------------------|---------------------|
| Source | OCI Logging | OCI Monitoring |
| Connector target | Streaming | Function |
| Consumer | OTel `kafka` receiver | Function → REST API |
| Splunk O11y sink | `otlphttp` `/v3/event` | `/v2/datapoint` gauge |

Reference: [Splunk — oci-monitoring-metrics-to-splunk-observability-python](https://github.com/splunk/oracle-cloud-examples-splunk-observability/tree/master/samples/oci-monitoring-metrics-to-splunk-observability-python) (official sample; this lab’s Function and transform follow the same pattern).
