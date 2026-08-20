#!/usr/bin/env python3
"""
OCI Function: transform OCI Monitoring metrics and forward to Splunk Observability.

Deploy to OCI Functions; configure Service Connector Hub:
  Source: Monitoring (namespace e.g. oci_vcn)
  Target: This function

Environment variables:
  SPLUNK_O11Y_REALM       - e.g. us0
  SPLUNK_O11Y_TOKEN       - Splunk ingest token
  DEPLOYMENT_ENVIRONMENT  - default oci-connector-lab
  FORWARD_TO_SPLUNK       - true/false (default true)
  LOGGING_LEVEL           - INFO, DEBUG, etc.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

from oci_metrics_transform import fresh_timestamps, transform_payload

LOG = logging.getLogger(__name__)
LOG.setLevel(os.environ.get("LOGGING_LEVEL", "INFO"))


def _splunk_ingest_url() -> str:
    realm = os.environ.get("SPLUNK_O11Y_REALM", "us0")
    custom = os.environ.get("SPLUNK_INGEST_URL")
    if custom:
        return custom.rstrip("/")
    return f"https://ingest.{realm}.signalfx.com"


def _forward(body: dict) -> None:
    token = os.environ.get("SPLUNK_O11Y_TOKEN") or os.environ.get("SPLUNK_ACCESS_TOKEN")
    if not token:
        raise ValueError("SPLUNK_O11Y_TOKEN not configured")

    url = f"{_splunk_ingest_url()}/v2/datapoint"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "X-SF-Token": token},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        LOG.info("Forwarded %d gauge points -> HTTP %s", len(body.get("gauge", [])), resp.status)


def handler(ctx, data: bytes = b""):  # noqa: ARG001 — OCI Functions signature
    try:
        payload = json.loads(data.decode("utf-8") if data else "{}")
    except json.JSONDecodeError as exc:
        LOG.exception("Invalid JSON payload")
        return {"status": "error", "message": str(exc)}

    env = os.environ.get("DEPLOYMENT_ENVIRONMENT", "oci-connector-lab")
    body = transform_payload(payload, environment=env)
    count = len(body.get("gauge", []))
    LOG.info("Transformed OCI metric %s -> %d gauge point(s)", payload.get("name"), count)

    if os.environ.get("FORWARD_TO_SPLUNK", "true").lower() in ("1", "true", "yes"):
        _forward(body)

    return {"status": "ok", "gauge_points": count}
