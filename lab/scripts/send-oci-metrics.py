#!/usr/bin/env python3
"""Local simulator: OCI Monitoring payloads → Splunk O11y /v2/datapoint."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB_ROOT / "lib"))

from oci_metrics_transform import fresh_timestamps, transform_jsonl, transform_payload  # noqa: E402


def load_splunk_config() -> tuple[str, str]:
    env_file = LAB_ROOT / ".env.splunk"
    values: dict[str, str] = {}
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            values[key.strip()] = val.strip()

    token = os.environ.get("SPLUNK_ACCESS_TOKEN") or values.get("SPLUNK_ACCESS_TOKEN", "")
    ingest = os.environ.get("SPLUNK_INGEST_URL") or values.get("SPLUNK_INGEST_URL", "")
    if not token or token == "your-ingest-token-here":
        raise SystemExit("ERROR: set SPLUNK_ACCESS_TOKEN in lab/.env.splunk")
    if not ingest:
        raise SystemExit("ERROR: set SPLUNK_INGEST_URL in lab/.env.splunk")
    return token, ingest.rstrip("/")


def post_datapoints(token: str, ingest_url: str, body: dict) -> None:
    url = f"{ingest_url}/v2/datapoint"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-SF-Token": token,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"POST {url} -> HTTP {resp.status} ({len(body.get('gauge', []))} gauge points)")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"ERROR: HTTP {exc.code} from Splunk ingest: {detail}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Send OCI-style metrics to Splunk O11y")
    parser.add_argument(
        "--fixtures",
        default=str(LAB_ROOT / "fixtures" / "oci-metric-samples.jsonl"),
    )
    parser.add_argument("--count", type=int, default=5, help="Metric events to send (cycles fixtures)")
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument(
        "--environment",
        default=os.environ.get("DEPLOYMENT_ENVIRONMENT", "oci-connector-lab"),
    )
    args = parser.parse_args()

    token, ingest = load_splunk_config()
    fixtures_path = Path(args.fixtures)
    lines = [ln.strip() for ln in fixtures_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        raise SystemExit(f"No fixtures in {fixtures_path}")

    print(f"Sending {args.count} OCI metric event(s) to {ingest}/v2/datapoint")
    for i in range(args.count):
        raw = json.loads(lines[i % len(lines)])
        body = fresh_timestamps(transform_payload(raw, environment=args.environment))
        post_datapoints(token, ingest, body)
        if args.interval > 0 and i < args.count - 1:
            time.sleep(args.interval)

    print("Done. In Metric Finder search: VnicFromNetworkBytes or CpuUtilization")
    print(f"Filter: deployment.environment.name:{args.environment}")


if __name__ == "__main__":
    main()
