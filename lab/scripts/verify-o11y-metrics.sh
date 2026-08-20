#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$LAB_ROOT"

echo "=== Splunk O11y credentials ==="
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
echo "OK  SPLUNK_INGEST_URL=${SPLUNK_INGEST_URL:-unset}"

echo ""
echo "=== Send sample OCI metrics ==="
python3 scripts/send-oci-metrics.py --count 3 --interval 0.2

echo ""
echo "=== O11y UI verification ==="
echo "1. Open Splunk O11y → Metric Finder"
echo "2. Time range: Last 15 minutes"
echo "3. Search metrics: VnicFromNetworkBytes, CpuUtilization, HttpRequests"
echo "4. Filter: deployment.environment.name:oci-connector-lab"
echo "5. Dimensions: oci_namespace, oci_dim_resourceId, oci_unit"
