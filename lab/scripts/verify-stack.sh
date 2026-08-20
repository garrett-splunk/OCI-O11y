#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$LAB_ROOT"

FAIL=0

ok() {
  echo "OK  $1"
}

fail() {
  echo "FAIL $1" >&2
  FAIL=1
}

if docker compose ps kafka 2>/dev/null | grep -qE 'running|Up'; then ok "kafka container"; else fail "kafka container"; fi
if docker compose ps otel-collector 2>/dev/null | grep -qE 'running|Up'; then ok "otel-collector container"; else fail "otel-collector container"; fi
if curl -sf http://localhost:13133/ >/dev/null 2>&1; then ok "collector :13133 health"; else fail "collector :13133 health"; fi

TOPICS="$(docker compose exec -T kafka rpk topic list --brokers localhost:9092 2>/dev/null || true)"
if echo "$TOPICS" | grep -qE '(^|[[:space:]])oci-logs([[:space:]]|$)'; then ok "topic oci-logs"; else fail "topic oci-logs"; fi

if [[ -f .env.splunk ]]; then
  if grep -q 'your-ingest-token-here' .env.splunk 2>/dev/null; then
    echo "WARN: placeholder token still in .env.splunk" >&2
  fi
  ok ".env.splunk present"
else
  fail ".env.splunk missing (cp .env.splunk.example .env.splunk)"
fi

if [[ "$FAIL" -eq 0 ]]; then
  echo "Stack verification passed."
else
  echo "Stack verification failed." >&2
  exit 1
fi
