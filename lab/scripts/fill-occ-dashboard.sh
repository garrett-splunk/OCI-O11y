#!/usr/bin/env bash
# Send OCI Compute (OCC) dashboard metrics with monotonic counters for .delta() charts.
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$LAB_ROOT"

LOOPS="${1:-20}"
INTERVAL="${2:-30}"

echo "Filling Oracle Cloud Compute dashboards (${LOOPS} iterations, ${INTERVAL}s apart)..."
python3 scripts/send-oci-metrics.py \
  --fixtures fixtures/oci-occ-dashboard-metrics.jsonl \
  --batch-all \
  --increment-counters \
  --loop "$LOOPS" \
  --interval "$INTERVAL"

echo ""
echo "Import dashboards/dashboard_group_OCC.json in Splunk O11y (Dashboards → Import)."
echo "Set time range to Last 15 minutes and filter deployment.environment.name:oci-connector-lab if needed."
