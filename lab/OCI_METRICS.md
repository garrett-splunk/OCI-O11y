# OCI Monitoring metrics → Splunk Observability Cloud

Two paths: **production** (Connector Hub → OCI Function) and **local lab** (fixture simulator).

## Production architecture

```
OCI Monitoring (oci_vcn, oci_computeagent, …)
        ↓
Connector Hub (Monitoring source → Function target)
        ↓
oci-metrics-forwarder (OCI Function)
        ↓ transform to gauge[]
        ↓
POST https://ingest.{realm}.signalfx.com/v2/datapoint
        ↓
Splunk Observability Cloud — Metric Finder
```

Connector Hub does **not** send Splunk-native metrics directly. The Function maps OCI payloads to Splunk `gauge` datapoints with dimensions (`oci_namespace`, `oci_dim_*`, etc.).

## Deployment order

1. Deploy the Function (`lab/functions/oci-metrics-forwarder/`)
2. Set Function config: `SPLUNK_O11Y_REALM`, `SPLUNK_O11Y_TOKEN`, `DEPLOYMENT_ENVIRONMENT`
3. Create Service Connector: **Monitoring** source → **Function** target
4. Start with namespace `oci_vcn`; expand namespaces once charts appear

## Function environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SPLUNK_O11Y_REALM` | `us0` | Realm for ingest URL |
| `SPLUNK_O11Y_TOKEN` | — | Splunk ingest token (required) |
| `SPLUNK_INGEST_URL` | — | Optional override (e.g. custom ingest host) |
| `DEPLOYMENT_ENVIRONMENT` | `oci-connector-lab` | `deployment.environment.name` dimension |
| `FORWARD_TO_SPLUNK` | `true` | Set `false` to transform-only test |
| `LOGGING_LEVEL` | `INFO` | Function logging |

## Deploy function (OCI CLI sketch)

```bash
cd lab/functions/oci-metrics-forwarder
fn create app oci-o11y-workshop --annotation oracle.com/oci/subnetIds='["<subnet-ocid>"]'
fn deploy --app oci-o11y-workshop
fn config function oci-o11y-workshop oci-metrics-forwarder SPLUNK_O11Y_TOKEN <token>
fn config function oci-o11y-workshop oci-metrics-forwarder SPLUNK_O11Y_REALM us0
fn config function oci-o11y-workshop oci-metrics-forwarder DEPLOYMENT_ENVIRONMENT oci-connector-lab
```

## Service Connector (Monitoring → Function)

Console: **Connector Hub → Create connector**

- **Source:** Monitoring — compartment + namespace (e.g. `oci_vcn`)
- **Target:** Functions — your app + `oci-metrics-forwarder`
- Allow auto-created IAM policies for metrics read + function invoke

## OCI → Splunk mapping

| OCI field | Splunk field |
|-----------|--------------|
| `name` | `metric` |
| `datapoints[].value` | `value` |
| `datapoints[].timestamp` | `timestamp` (ms) |
| `namespace` | dimension `oci_namespace` |
| `compartmentId` | dimension `oci_compartment_id` |
| `metadata.unit` | dimension `oci_unit` |
| `dimensions.*` | dimension `oci_dim_<name>` |
| (lab tag) | `deployment.environment.name` |

## Local lab (no OCI tenancy required)

Simulates the Function transform and POSTs to your Splunk org:

```bash
cd lab
./scripts/produce-oci-metrics.sh 5
./scripts/verify-o11y-metrics.sh
```

**Metric Finder:** `VnicFromNetworkBytes`, filter `deployment.environment.name:oci-connector-lab`

## Contrast with logs path

| | Logs (Streaming lab) | Metrics (this doc) |
|--|----------------------|---------------------|
| Source | OCI Logging | OCI Monitoring |
| Connector target | Streaming | Function |
| Consumer | OTel `kafka` receiver | Function → REST API |
| Splunk sink | `otlphttp` `/v3/event` | `/v2/datapoint` gauge |

Reference: [Oracle — Exporting OCI Monitoring Metrics to Splunk Observability](https://github.com/oracle-samples) (workshop pattern).
