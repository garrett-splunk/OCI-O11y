#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$LAB_ROOT"

COUNT="${1:-10}"
INTERVAL="${2:-0.5}"
FIXTURES="$LAB_ROOT/fixtures/oci-log-samples.jsonl"

if [[ ! -f "$FIXTURES" ]]; then
  echo "ERROR: missing $FIXTURES" >&2
  exit 1
fi

produce_rpk() {
  local payload="$1"
  printf '%s\n' "$payload" | docker compose exec -T kafka \
    rpk topic produce oci-logs --brokers localhost:9092 -z none
}

fresh_payload() {
  python3 -c "
import json, uuid, sys
from datetime import datetime, timezone
obj = json.loads(open(sys.argv[1]).read().splitlines()[int(sys.argv[2]) % int(sys.argv[3])])
now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.') + f'{datetime.now(timezone.utc).microsecond // 1000:03d}Z'
obj['datetime'] = now
lc = obj.get('logContent') or {}
if isinstance(lc, dict):
    lc['id'] = 'ocid1.logcontent.oc1.iad.' + uuid.uuid4().hex[:12]
    lc['time'] = now
    obj['logContent'] = lc
print(json.dumps(obj, separators=(',', ':')))
" "$FIXTURES" "$1" "$(grep -cve '^[[:space:]]*$' "$FIXTURES")"
}

SAMPLE_COUNT="$(grep -cve '^[[:space:]]*$' "$FIXTURES")"

if command -v python3 >/dev/null 2>&1 && python3 -c "import kafka" 2>/dev/null; then
  python3 producer/produce_oci_logs.py \
    --bootstrap localhost:9092 \
    --topic oci-logs \
    --fixtures "$FIXTURES" \
    --count "$COUNT" \
    --interval "$INTERVAL"
  exit 0
fi

echo "Producing $COUNT message(s) via rpk (Redpanda CLI in kafka container)..."
i=0
while [[ "$i" -lt "$COUNT" ]]; do
  payload="$(fresh_payload "$i")"
  produce_rpk "$payload"
  i=$((i + 1))
  echo "  [$i/$COUNT] sent"
  if [[ "$i" -lt "$COUNT" ]] && awk "BEGIN {exit !($INTERVAL > 0)}"; then
    sleep "$INTERVAL"
  fi
done

echo "Done. Check collector: docker compose logs otel-collector --tail 20"
