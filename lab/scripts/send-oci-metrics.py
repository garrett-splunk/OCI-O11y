#!/usr/bin/env python3
"""Local simulator: OCI Monitoring payloads → Splunk O11y /v2/datapoint."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB_ROOT / "lib"))

from oci_metrics_transform import fresh_timestamps, transform_payload  # noqa: E402

COUNTER_METRICS = {
    "DiskIopsRead",
    "DiskIopsWritten",
    "DiskBytesRead",
    "DiskBytesWritten",
    "NetworksBytesIn",
    "NetworksBytesOut",
}

GAUGE_METRICS = {
    "CpuUtilization",
    "MemoryUtilization",
    "MemoryAllocationStalls",
    "LoadAverage",
}


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


def load_fixtures(path: Path) -> list[dict]:
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        raise SystemExit(f"No fixtures in {path}")
    return [json.loads(line) for line in lines]


def adjust_payload_for_iteration(raw: dict, iteration: int, *, increment_counters: bool) -> dict:
    """Bump counter metrics so Signalflow .delta() charts show non-zero rates."""
    payload = json.loads(json.dumps(raw))
    metric_name = payload.get("name", "")
    for dp in payload.get("datapoints") or []:
        base = float(dp.get("value", 0))
        if increment_counters and metric_name in COUNTER_METRICS:
            dp["value"] = base * (iteration + 1)
        elif metric_name in GAUGE_METRICS:
            # Small oscillation keeps CPU/memory charts interesting without leaving 0–100 range.
            wave = math.sin(iteration / 3.0) * 5.0
            dp["value"] = max(0.0, min(100.0, base + wave)) if metric_name != "LoadAverage" else max(0.1, base + wave / 10.0)
    return payload


def build_body(
    fixtures: list[dict],
    *,
    iteration: int,
    environment: str,
    increment_counters: bool,
    batch_all: bool,
    count: int,
) -> dict:
    gauges: list[dict] = []
    if batch_all:
        for raw in fixtures:
            adjusted = adjust_payload_for_iteration(raw, iteration, increment_counters=increment_counters)
            gauges.extend(transform_payload(adjusted, environment=environment).get("gauge", []))
    else:
        for i in range(count):
            raw = fixtures[i % len(fixtures)]
            adjusted = adjust_payload_for_iteration(raw, iteration + i, increment_counters=increment_counters)
            gauges.extend(transform_payload(adjusted, environment=environment).get("gauge", []))
    return fresh_timestamps({"gauge": gauges})


def main() -> None:
    parser = argparse.ArgumentParser(description="Send OCI-style metrics to Splunk O11y")
    parser.add_argument(
        "--fixtures",
        default=str(LAB_ROOT / "fixtures" / "oci-metric-samples.jsonl"),
    )
    parser.add_argument("--count", type=int, default=5, help="Metric events per iteration (ignored with --batch-all)")
    parser.add_argument("--interval", type=float, default=0.5, help="Seconds between iterations")
    parser.add_argument("--loop", type=int, default=1, help="Iterations (0 = run until Ctrl+C)")
    parser.add_argument("--batch-all", action="store_true", help="Send every fixture line in one POST per iteration")
    parser.add_argument(
        "--increment-counters",
        action="store_true",
        help="Increase counter metrics each iteration for .delta() dashboard charts",
    )
    parser.add_argument(
        "--environment",
        default=os.environ.get("DEPLOYMENT_ENVIRONMENT", "oci-connector-lab"),
    )
    args = parser.parse_args()

    token, ingest = load_splunk_config()
    fixtures = load_fixtures(Path(args.fixtures))
    total_iterations = args.loop if args.loop > 0 else None

    print(f"Sending OCI metrics to {ingest}/v2/datapoint")
    print(f"  fixtures: {args.fixtures}")
    print(f"  batch-all: {args.batch_all}  increment-counters: {args.increment_counters}")
    if total_iterations:
        print(f"  iterations: {total_iterations}  interval: {args.interval}s")
    else:
        print(f"  iterations: until Ctrl+C  interval: {args.interval}s")

    iteration = 0
    while total_iterations is None or iteration < total_iterations:
        body = build_body(
            fixtures,
            iteration=iteration,
            environment=args.environment,
            increment_counters=args.increment_counters,
            batch_all=args.batch_all,
            count=args.count,
        )
        post_datapoints(token, ingest, body)
        iteration += 1
        if total_iterations is not None and iteration >= total_iterations:
            break
        if args.interval > 0:
            time.sleep(args.interval)

    print("Done.")
    print("Metric Finder: CpuUtilization, NetworksBytesIn, DiskIopsRead")
    print(f"Filter: deployment.environment.name:{args.environment} and oci_namespace:oci_computeagent")


if __name__ == "__main__":
    main()
