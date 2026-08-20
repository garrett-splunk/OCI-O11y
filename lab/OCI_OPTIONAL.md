# OCI Connector Hub → Streaming (optional real OCI path)

The local lab uses **Redpanda** as a Kafka-compatible stand-in. Use these steps when moving to real **OCI Streaming** fed by **Connector Hub**.

## Architecture (production)

1. **OCI Logging** — service logs, audit logs, custom logs in a log group
2. **Connector Hub** — service connector: source = Logging, target = Streaming
3. **OCI Streaming** — Kafka 1.0-compatible stream pool + topic
4. **Splunk OTel Collector** — `kafka` receiver (SOC4Kafka pattern) → `otlphttp` → O11y `/v3/event`

Connector Hub does **not** export OTLP directly. OTLP is configured on the **Splunk collector** side.

## Console: Connector Hub (Logging → Streaming)

1. Open **Observability & Management → Logging** — note the log group OCID(s) to export.
2. Open **Analytics & AI → Messaging → Streaming** — create a **Stream Pool** and **Stream** (e.g. `oci-platform-logs`).
3. Open **Observability & Management → Connector Hub → Create connector**:
   - **Source:** Logging — select compartment + log group(s)
   - **Target:** Streaming — select stream OCID
   - Optional: **Log filter** task to reduce volume
4. Activate the connector; confirm records appear in the stream (Streaming → Stream → Load messages).

## OCI Streaming connection settings

From **Stream Pool → Kafka Connection Settings**:

| Value | Notes |
|-------|--------|
| Bootstrap servers | e.g. `cell-1.streaming.us-ashburn-1.oci.oraclecloud.com:9092` |
| SASL username | `tenancy/user/streampool-ocid` — **four-part** if using identity domain |
| SASL password | OCI **Auth Token** (Profile → User Settings → Auth Tokens) |
| Protocol | Kafka **1.0.0** only — set `protocol_version: "1.0.0"` in collector |

Use `lab/collector/otelbin-examples/oci-production.yaml` as the collector template.

## CLI example (service connector)

```bash
oci sch service-connector create \
  --compartment-id "$COMPARTMENT_OCID" \
  --display-name "oci-logs-to-streaming" \
  --source '{"kind":"logging","logSources":[...]}' \
  --target '{"kind":"streaming","streamId":"'"$STREAM_OCID"'"}'
```

See [OCI Connector Hub docs](https://docs.oracle.com/en-us/iaas/Content/connector-hub/overview.htm) for current JSON schema.

## Production gotchas

| Issue | Fix |
|-------|-----|
| `SASL authentication failed` | Use 4-part username if identity domain is enabled |
| Consumer loops `NOT_COORDINATOR` | Pick a **new** consumer group name |
| No messages consumed | Confirm stream pool network path (private endpoint vs public) |
| Works with HEC but not O11y | This lab uses `otlphttp` + ingest token — not HEC `:8088` |
| Special chars in auth token | Quote password in env files; YAML `#` prefix breaks MicroK8s secrets |

## Related references

- [Splunk Lantern — OCI Streaming + SOC4Kafka](https://lantern.splunk.com/Platform_Data_Management/Unlock_Insights/Forwarding_OCI_Streaming_to_Splunk_with_Splunk_OpenTelemetry_Collector_for_Kafka) (HEC sink; adapt to `otlphttp` for O11y)
- [adibirzu/oci-splunk](https://github.com/adibirzu/oci-splunk) — Terraform stack for OCI → Streaming → SOC4Kafka → Splunk Platform
