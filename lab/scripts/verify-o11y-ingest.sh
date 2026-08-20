#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$LAB_ROOT"

echo "=== Collector health ==="
curl -sf http://localhost:13133/ && echo

echo ""
echo "=== Recent collector logs (kafka / export / error) ==="
docker compose logs otel-collector 2>&1 | grep -iE 'kafka|otlp|export|error|401|403' | tail -25 || docker compose logs otel-collector --tail 25

echo ""
echo "=== Splunk credentials check ==="
if [[ ! -f .env.splunk ]]; then
  echo "FAIL: .env.splunk missing" >&2
  exit 1
fi
# shellcheck disable=SC1091
set -a
source .env.splunk
set +a

if [[ "${SPLUNK_ACCESS_TOKEN:-}" == "your-ingest-token-here" || -z "${SPLUNK_ACCESS_TOKEN:-}" ]]; then
  echo "FAIL: set SPLUNK_ACCESS_TOKEN in .env.splunk" >&2
  exit 1
fi
echo "OK  SPLUNK_REALM=${SPLUNK_REALM:-unset}"
echo "OK  SPLUNK_INGEST_URL=${SPLUNK_INGEST_URL:-unset}"

echo ""
echo "=== O11y UI verification ==="
echo "1. Open Splunk Observability Cloud → Log Observer (or Logs)"
echo "2. Time range: Last 15 minutes"
echo "3. Filter: deployment.environment.name:oci-connector-lab"
echo "4. Search for: Connector Hub OR compute OR apigateway"
echo ""
echo "If no logs appear after produce-oci-logs.sh:"
echo "  docker compose restart otel-collector"
echo "  docker compose logs otel-collector --tail 50 | grep -iE '401|403|error|kafka'"
