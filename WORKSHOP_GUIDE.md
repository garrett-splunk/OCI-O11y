# Facilitator guide — OCI Metrics → O11y Cloud

~25 minutes hands-on. **Metrics-first** — Python simulator mirrors the OCI Function. Docker/Redpanda is optional (logs appendix only).

## Summary

| Step | Artifact | Why |
|------|----------|-----|
| 1 | Prerequisites | Python 3, Splunk ingest token (metrics scope) |
| 2 | `.env.splunk` | Realm + token + ingest URL (match US0/US1/etc.) |
| 3 | `produce-oci-metrics.sh` | Simulated Monitoring metrics |
| 4 | Metric Finder | Verify gauge metrics |
| 5 | `fill-occ-dashboard.sh` | Populate Oracle Cloud Compute dashboards |
| 6 | `OCI_METRICS.md` | Real OCI deploy path |
| 7 | Production gotchas | Function order, namespace filters |
| — | Logs appendix (optional) | Docker + collector; needs Splunk Cloud/Enterprise for Log Observer |

## Script reference

| Script | When | What |
|--------|------|------|
| `scripts/metrics-lab.sh` | Main lab | Verify + fill OCC dashboards (no Docker) |
| `scripts/produce-oci-metrics.sh` | Step 3 | POST gauge datapoints to `/v2/datapoint` |
| `scripts/verify-o11y-metrics.sh` | Step 4 | Send samples + UI hints |
| `scripts/fill-occ-dashboard.sh` | Step 5 | Loop OCC metrics for `.delta()` charts |
| `scripts/start.sh` | Logs appendix | `docker compose up -d` |
| `scripts/produce-oci-logs.sh` | Logs appendix | Publish OCI JSON to `oci-logs` |
| `scripts/teardown-lab.sh` | End (if Docker used) | `docker compose down -v` |

## Teaching notes

**Why metrics-first**

- Observability Cloud ingest tokens work for **metrics** (`/v2/datapoint`) on all orgs.
- **Log Observer** for OCI logs typically requires a linked Splunk Cloud or Enterprise instance — many workshop attendees only have O11y metrics.
- The metrics path matches production OCI Connector Hub (Monitoring → Function) without Docker.

**Metrics path (Monitoring → Function)**

- Connector Hub source = **Monitoring**, target = **Function** (not Streaming)
- Function maps OCI JSON to Splunk `gauge` arrays and POSTs `/v2/datapoint`
- Deploy Function **before** creating the Service Connector
- Local lab: `send-oci-metrics.py` uses the same transform as `functions/oci-metrics-forwarder/func.py`

**OCC dashboards**

- Charts filter `oci_namespace = oci_computeagent`
- Use `fill-occ-dashboard.sh` not basic samples — basic fixtures use mixed namespaces (`oci_vcn`, etc.)

**Logs appendix (optional)**

- OCI Logging → Connector Hub → Streaming → collector `kafka` receiver → `otlphttp` → `/v3/event`
- Skip if attendees cannot access Log Observer

## Timed run-of-show

### Part 1 — Credentials (5 min)

```bash
cd lab
cp .env.splunk.example .env.splunk
# facilitator token — confirm realm (e.g. us1)
```

### Part 2 — Metrics + mapping (10 min)

```bash
./scripts/produce-oci-metrics.sh 5
./scripts/verify-o11y-metrics.sh
```

Walk transform: OCI `namespace` → `oci_namespace`, `dimensions.*` → `oci_dim_*`.

Metric Finder: `CpuUtilization`, filter `oci_namespace:oci_computeagent`.

### Part 3 — OCC dashboards (10 min)

Import `dashboards/dashboard_group_OCC.json`.

```bash
./scripts/fill-occ-dashboard.sh 20 30
```

While running: **Oracle Cloud Compute** dashboards, Last 15 minutes. Explain `.delta()` on disk/network counters.

### Part 4 — Real OCI + optional logs (5 min)

Walk `OCI_METRICS.md` deploy order. Mention logs appendix only if org has Log Observer.

## One-liner cheat sheet

```bash
cd lab && cp .env.splunk.example .env.splunk && ./scripts/metrics-lab.sh 20 30
```

Filter: `deployment.environment.name:oci-connector-lab`

## Common fixes

| Symptom | Fix |
|---------|-----|
| HTTP 401 on metrics | Token + realm mismatch (US1 → `ingest.us1.signalfx.com`) |
| Metrics in Finder, dashboards empty | Run `fill-occ-dashboard.sh`; import OCC JSON; Last 15 min |
| No logs in Log Observer | Expected on O11y-only orgs — skip logs appendix |
| Collector won't start | Logs appendix only; collector v0.155.0+ |
