#!/usr/bin/env bash
# Metrics-only lab path — no Docker required.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$LAB_ROOT"

if [[ ! -f .env.splunk ]]; then
  echo "Create lab/.env.splunk first:" >&2
  echo "  cp .env.splunk.example .env.splunk" >&2
  exit 1
fi

echo "=== Metrics-only OCI → O11y lab ==="
./scripts/verify-o11y-metrics.sh
echo ""
echo "=== Fill Oracle Cloud Compute dashboards ==="
./scripts/fill-occ-dashboard.sh "${1:-20}" "${2:-30}"
