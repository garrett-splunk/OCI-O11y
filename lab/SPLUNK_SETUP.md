# Splunk OTel Collector — OCI Connector lab wiring

This lab runs the collector in Docker with **`collector/otelcol-config.yaml`**.

## Pipeline

1. **`receivers.kafka`** — consumes `oci-logs` topic (Redpanda locally; OCI Streaming in production)
2. **`processors.resource/oci_lab`** — tags `deployment.environment`, `cloud.provider=oci`
3. **`exporters.otlphttp/o11y_logs`** — logs to `${SPLUNK_INGEST_URL}/v3/event`

## Secrets

```bash
cp .env.splunk.example .env.splunk
# Edit SPLUNK_ACCESS_TOKEN, SPLUNK_REALM, SPLUNK_INGEST_URL
docker compose restart otel-collector
```

## Verify

```bash
curl -sf http://localhost:13133/
docker compose logs otel-collector --tail 30 | grep -iE 'kafka|export|error|401'
```

## Production OCI Streaming

See `collector/otelbin-examples/oci-production.yaml` for SASL_SSL/PLAIN, `protocol_version: "1.0.0"`, and stream pool bootstrap FQDN.

Reference: [Splunk Lantern — OCI Streaming + SOC4Kafka](https://lantern.splunk.com/Platform_Data_Management/Unlock_Insights/Forwarding_OCI_Streaming_to_Splunk_with_Splunk_OpenTelemetry_Collector_for_Kafka) (adapt sink from `splunk_hec` to `otlphttp`).
