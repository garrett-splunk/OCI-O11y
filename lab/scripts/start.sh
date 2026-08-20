#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$LAB_ROOT"

if [[ ! -f .env.splunk ]]; then
  echo "WARNING: lab/.env.splunk missing — copy from .env.splunk.example and add your ingest token." >&2
  echo "  cp .env.splunk.example .env.splunk" >&2
fi

docker compose up -d --build

echo "Waiting for Kafka..."
for _ in $(seq 1 60); do
  if docker compose exec -T kafka rpk topic list --brokers localhost:9092 2>/dev/null | grep -qE '(^|[[:space:]])oci-logs([[:space:]]|$)'; then
    break
  fi
  sleep 2
done

echo "Waiting for collector health..."
for _ in $(seq 1 30); do
  if curl -sf http://localhost:13133/ >/dev/null 2>&1; then
    echo "Lab stack is up."
    echo "  Collector health: http://localhost:13133"
    echo "  Next: ./scripts/verify-stack.sh && ./scripts/produce-oci-logs.sh"
    exit 0
  fi
  sleep 2
done

echo "ERROR: collector health check did not pass on :13133" >&2
docker compose logs otel-collector --tail 30
exit 1
