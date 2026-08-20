"""Transform OCI Monitoring metric payloads to Splunk Observability /v2/datapoint format."""

from __future__ import annotations

import json
import os
import time
from typing import Any


DEFAULT_ENVIRONMENT = os.environ.get("DEPLOYMENT_ENVIRONMENT", "oci-connector-lab")


def oci_metric_to_splunk_gauges(
    oci_payload: dict[str, Any],
    *,
    environment: str | None = None,
) -> list[dict[str, Any]]:
    """Map one OCI metric event to Splunk gauge datapoints (one per OCI datapoint)."""
    env = environment or DEFAULT_ENVIRONMENT
    namespace = oci_payload.get("namespace", "unknown")
    compartment_id = oci_payload.get("compartmentId", "")
    resource_group = oci_payload.get("resourceGroup")
    metric_name = oci_payload.get("name", "unknown_metric")
    metadata = oci_payload.get("metadata") or {}
    oci_dimensions = oci_payload.get("dimensions") or {}

    gauges: list[dict[str, Any]] = []
    for dp in oci_payload.get("datapoints") or []:
        dimensions: dict[str, str] = {
            "oci_namespace": str(namespace),
            "oci_compartment_id": str(compartment_id),
            "oci_unit": str(metadata.get("unit", "")),
            "deployment.environment": env,
            "deployment.environment.name": env,
            "cloud.provider": "oci",
        }
        if resource_group:
            dimensions["oci_resource_group"] = str(resource_group)
        display_name = metadata.get("displayName")
        if display_name:
            dimensions["oci_display_name"] = str(display_name)
        for key, value in oci_dimensions.items():
            dimensions[f"oci_dim_{key}"] = str(value)

        point: dict[str, Any] = {
            "metric": metric_name,
            "value": dp.get("value", 0),
            "dimensions": dimensions,
        }
        if "timestamp" in dp:
            point["timestamp"] = int(dp["timestamp"])
        gauges.append(point)
    return gauges


def transform_payload(payload: dict[str, Any], *, environment: str | None = None) -> dict[str, list]:
    """Return Splunk datapoint body with gauge array."""
    if isinstance(payload, list):
        gauges: list[dict[str, Any]] = []
        for item in payload:
            gauges.extend(oci_metric_to_splunk_gauges(item, environment=environment))
        return {"gauge": gauges}

    return {"gauge": oci_metric_to_splunk_gauges(payload, environment=environment)}


def transform_jsonl(text: str, *, environment: str | None = None) -> dict[str, list]:
    gauges: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        gauges.extend(oci_metric_to_splunk_gauges(json.loads(line), environment=environment))
    return {"gauge": gauges}


def fresh_timestamps(body: dict[str, list]) -> dict[str, list]:
    """Re-stamp metrics for demo runs so charts show recent data."""
    now_ms = int(time.time() * 1000)
    for point in body.get("gauge", []):
        point["timestamp"] = now_ms
    return body
