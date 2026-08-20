# Facilitator guide — OCI Connector Hub → O11y Cloud

~45 minutes hands-on. Local Redpanda simulates OCI Streaming for **logs**; Python simulator mirrors the OCI **metrics** Function.

## Summary

| Step | Artifact | Why |
|------|----------|-----|
| 1 | Prerequisites | Docker, Splunk ingest token |
| 2 | `docker compose up` | Redpanda + collector (logs) |
| 3 | `.env.splunk` | Realm + token + ingest URL |
| 4 | `otelcol-config.yaml` | kafka receiver → otlphttp O11y logs |
| 5 | `produce-oci-logs.sh` | Simulated log payloads |
| 6 | Log Observer | Verify logs filter |
| 7 | `produce-oci-metrics.sh` | Simulated Monitoring metrics |
| 8 | Metric Finder | Verify gauge metrics |
| 9 | `OCI_OPTIONAL.md` / `OCI_METRICS.md` | Real OCI deploy paths |
| 10 | Production gotchas | SASL, protocol 1.0, Function order |

## Script reference

| Script | When | What |
|--------|------|------|
| `scripts/start.sh` | Step 2 | `docker compose up -d`, wait for health |
| `scripts/verify-stack.sh` | After start | Kafka topic + collector :13133 |
| `scripts/produce-oci-logs.sh` | Step 5 | Publish OCI JSON to `oci-logs` |
| `scripts/verify-o11y-ingest.sh` | Step 6 | Log ingest verification |
| `scripts/produce-oci-metrics.sh` | Step 7 | POST gauge datapoints to `/v2/datapoint` |
| `scripts/verify-o11y-metrics.sh` | Step 8 | Metrics UI hints |
| `scripts/teardown-lab.sh` | End | `docker compose down -v` |

## Teaching notes

**Connector Hub vs Streaming vs collector**

- Connector Hub = managed fan-out inside OCI (Logging → Streaming, Monitoring → Object Storage, etc.)
- OCI Streaming = Kafka 1.0-compatible buffer — you do not install brokers
- Collector = standalone consumer (SOC4Kafka pattern) — runs anywhere with network access to the stream

**Metrics path (Monitoring → Function)**

- Connector Hub source = **Monitoring**, target = **Function** (not Streaming)
- Function maps OCI JSON to Splunk `gauge` arrays and POSTs `/v2/datapoint`
- Deploy Function **before** creating the Service Connector
- Local lab: `send-oci-metrics.py` uses the same transform as `functions/oci-metrics-forwarder/func.py`

**Why OTLP on Splunk side (logs only)**

OCI does not offer Connector Hub → third-party OTLP. The OpenTelemetry export happens in the collector (`otlphttp` → `/v3/event`).

**Contrast with other workshops**

- Oracle DB lab: `oracledb` receiver scrapes the database directly
- MQ-Rabbit-Kafka: `kafkametrics` scrapes broker metrics; not log fan-out from cloud control plane

## Timed run-of-show

### Part 1 — Start stack (5 min)

```bash
cd lab
cp .env.splunk.example .env.splunk   # facilitator token
./scripts/start.sh
./scripts/verify-stack.sh
```

Expected: collector health on `:13133`, topic `oci-logs` exists.

### Part 2 — Walk collector config (10 min)

Open `lab/collector/otelcol-config.yaml`. Four blocks:

1. `receivers.kafka` — topic `oci-logs`, `encoding: text`
2. `processors.resource/oci_lab` — environment + `cloud.provider=oci`
3. `exporters.otlphttp/o11y_logs` — `/v3/event` + `X-SF-Token`
4. `service.pipelines.logs` — single logs pipeline

Compare with `otelbin-examples/oci-production.yaml` for SASL + `protocol_version: "1.0.0"`.

### Part 3 — Produce + verify (10 min)

```bash
./scripts/produce-oci-logs.sh 10 0.3
./scripts/verify-o11y-ingest.sh
```

In O11y: **Log Observer** → Last 15 min → filter `deployment.environment.name:oci-connector-lab` → search `Connector Hub` or `compute`.

Debug exporter in collector logs should show `log records: N`. 401 errors mean bad token — fix `.env.splunk` and `docker compose restart otel-collector`.

### Part 4 — Metrics (10 min)

```bash
./scripts/produce-oci-metrics.sh 5
./scripts/verify-o11y-metrics.sh
```

Metric Finder: `VnicFromNetworkBytes`, filter `deployment.environment.name:oci-connector-lab`.

Walk `OCI_METRICS.md`: deploy order, namespace `oci_vcn`, dimension mapping.

### Part 5 — Optional OCI + gotchas (5 min)

Walk `OCI_OPTIONAL.md`: Connector Hub console flow, SASL username format, fresh consumer group, Lantern HEC vs this lab's O11y OTLP sink.

## One-liner cheat sheet

```bash
cd lab && cp .env.splunk.example .env.splunk && ./scripts/start.sh && ./scripts/produce-oci-logs.sh 10 && ./scripts/produce-oci-metrics.sh 5
```

Filter: `deployment.environment.name:oci-connector-lab`

## Common fixes

| Symptom | Fix |
|---------|-----|
| Collector won't start | Use collector **v0.155.0+** (kafka logs receiver); exporter is `otlphttp` not `otlp_http` |
| 401 on export | Valid ingest token in `.env.splunk`; restart collector |
| No logs in UI | Produce first; widen time range; remove filters; check debug exporter count |
| `mapfile` error on Mac | Fixed — script uses rpk via docker |
