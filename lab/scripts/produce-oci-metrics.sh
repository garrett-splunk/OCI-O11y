#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$LAB_ROOT"

COUNT="${1:-5}"
INTERVAL="${2:-0.5}"

python3 scripts/send-oci-metrics.py --count "$COUNT" --interval "$INTERVAL"
