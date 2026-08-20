#!/usr/bin/env python3
"""Publish OCI Logging-style JSON records to Kafka (simulates Connector Hub → Streaming)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from kafka import KafkaProducer
except ImportError:
    print("ERROR: install kafka-python (pip install kafka-python)", file=sys.stderr)
    sys.exit(1)


def load_samples(path: Path) -> list[str]:
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        raise SystemExit(f"No sample logs in {path}")
    return lines


def fresh_record(raw: str) -> str:
    """Re-stamp time/id so repeated runs produce distinct events in Log Observer."""
    obj = json.loads(raw)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    obj["datetime"] = now
    if "logContent" in obj and isinstance(obj["logContent"], dict):
        obj["logContent"]["id"] = f"ocid1.logcontent.oc1.iad.{uuid.uuid4().hex[:12]}"
        obj["logContent"]["time"] = now
    return json.dumps(obj, separators=(",", ":"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Produce OCI-style logs to Kafka")
    parser.add_argument("--bootstrap", default=os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092"))
    parser.add_argument("--topic", default=os.environ.get("KAFKA_TOPIC", "oci-logs"))
    parser.add_argument(
        "--fixtures",
        default=str(Path(__file__).resolve().parent.parent / "fixtures" / "oci-log-samples.jsonl"),
    )
    parser.add_argument("--count", type=int, default=10, help="Messages to send (cycles through fixtures)")
    parser.add_argument("--interval", type=float, default=0.5, help="Seconds between messages")
    args = parser.parse_args()

    samples = load_samples(Path(args.fixtures))
    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap,
        value_serializer=lambda v: v.encode("utf-8"),
        acks="all",
    )

    print(f"Producing {args.count} message(s) to {args.topic} @ {args.bootstrap}")
    for i in range(args.count):
        payload = fresh_record(samples[i % len(samples)])
        producer.send(args.topic, value=payload)
        print(f"  [{i + 1}/{args.count}] sent ({len(payload)} bytes)")
        if args.interval > 0 and i < args.count - 1:
            time.sleep(args.interval)

    producer.flush()
    producer.close()
    print("Done.")


if __name__ == "__main__":
    main()
