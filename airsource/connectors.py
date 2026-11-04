"""External environmental data connectors with explicit provenance and data classes.

Connectors return provider-native observations and metadata. They do not silently
merge satellite/model products with regulatory ground-monitor observations.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests

OPENAQ_BASE = "https://api.openaq.org/v3"
OGD_BASE = "https://api.data.gov.in/resource"
FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


def _retrieved_at() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _get_json(url: str, *, params: dict | None = None, headers: dict | None = None,
              timeout: int = 30) -> dict[str, Any]:
    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Unexpected provider response: expected a JSON object.")
    return payload


def fetch_openaq_location_latest(location_id: int, *, api_key: str | None = None) -> tuple[pd.DataFrame, dict]:
    """Fetch latest sensor readings for one OpenAQ location (not a complete time series)."""
    key = api_key or os.getenv("OPENAQ_API_KEY")
    if not key:
        raise ValueError("OpenAQ API key required. Set OPENAQ_API_KEY; do not hard-code credentials.")
    if int(location_id) <= 0:
        raise ValueError("location_id must be positive.")
    url = f"{OPENAQ_BASE}/locations/{int(location_id)}/latest"
    payload = _get_json(url, headers={"X-API-Key": key, "Accept": "application/json"})
    rows = payload.get("results", [])
    records = []
    for row in rows:
        coords = row.get("coordinates") or {}
        dt = row.get("datetime") or {}
        records.append({
            "location_id": row.get("locationsId", location_id),
            "sensor_id": row.get("sensorsId"),
            "parameter": (row.get("parameter") or {}).get("name"),
            "value": row.get("value"),
            "unit": (row.get("parameter") or {}).get("units"),
            "timestamp": dt.get("utc"),
            "latitude": coords.get("latitude"),
            "longitude": coords.get("longitude"),
        })
    frame = pd.DataFrame(records)
    if not frame.empty:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    metadata = {
        "provider": "OpenAQ API v3", "endpoint": url, "retrieved_at_utc": _retrieved_at(),
        "data_class": "Sensor measurements aggregated by OpenAQ; not guaranteed to be complete or strictly ordered.",
        "resource_semantics": "Latest resource returns the latest value in each sensor series, not necessarily the most recently ingested record.",
        "record_count": len(frame), "location_id": int(location_id),
        "documentation": "https://docs.openaq.org/resources/latest",
    }
    return frame, metadata


def fetch_india_ogd_resource(resource_id: str, *, api_key: str | None = None,
                             limit: int = 1000, offset: int = 0) -> tuple[pd.DataFrame, dict]:
    """Fetch a configured data.gov.in resource; resource ID is never guessed."""
    key = api_key or os.getenv("DATA_GOV_IN_API_KEY")
    if not key:
        raise ValueError("data.gov.in API key required. Set DATA_GOV_IN_API_KEY.")
    if not resource_id or not str(resource_id).strip():
        raise ValueError("Provide the exact data.gov.in resource ID from its catalogue.")
    if not (1 <= int(limit) <= 10000) or int(offset) < 0:
        raise ValueError("limit must be 1..10000 and offset must be non-negative.")
    url = f"{OGD_BASE}/{resource_id}"
    payload = _get_json(url, params={"api-key": key, "format": "json",
                                    "limit": int(limit), "offset": int(offset)})
    rows = payload.get("records", [])
    frame = pd.DataFrame(rows)
    metadata = {
        "provider": "Open Government Data Platform India", "endpoint": url,
        "retrieved_at_utc": _retrieved_at(),
        "data_class": "Government-published resource; field meanings and measurement status depend on the selected catalogue resource.",
        "resource_id": str(resource_id), "record_count": len(frame),
        "catalogue": "https://www.data.gov.in/catalog/real-time-air-quality-index",
        "note": "Confirm the selected resource schema, units, station identifiers, update cadence and licence before mapping fields.",
    }
    return frame, metadata


def fetch_firms_area(west: float, south: float, east: float, north: float, *,
                     source: str = "VIIRS_SNPP_NRT", day_range: int = 1,
                     map_key: str | None = None) -> tuple[pd.DataFrame, dict]:
    """Fetch NASA FIRMS CSV for a bounding box; requires a user-provided MAP_KEY."""
    key = map_key or os.getenv("NASA_FIRMS_MAP_KEY")
    if not key:
        raise ValueError("NASA FIRMS MAP_KEY required. Set NASA_FIRMS_MAP_KEY.")
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("Invalid geographic bounding box.")
    if not 1 <= int(day_range) <= 5:
        raise ValueError("FIRMS Area API day_range must be between 1 and 5.")
    allowed = {"MODIS_NRT", "MODIS_SP", "VIIRS_SNPP_NRT", "VIIRS_SNPP_SP",
               "VIIRS_NOAA20_NRT", "VIIRS_NOAA20_SP", "VIIRS_NOAA21_NRT", "VIIRS_NOAA21_SP"}
    if source not in allowed:
        raise ValueError(f"Unsupported FIRMS source: {source}")
    area = f"{west},{south},{east},{north}"
    url = f"{FIRMS_BASE}/{key}/{source}/{area}/{int(day_range)}"
    response = requests.get(url, timeout=45, headers={"User-Agent": "AirSource-X/0.6 research"})
    response.raise_for_status()
    from io import StringIO
    frame = pd.read_csv(StringIO(response.text))
    metadata = {
        "provider": "NASA LANCE FIRMS", "endpoint": response.url,
        "retrieved_at_utc": _retrieved_at(),
        "data_class": "Satellite-detected thermal anomalies / active-fire detections; not direct measurements of PM2.5 or proof of a pollution source.",
        "source": source, "bbox_wsen": [west, south, east, north],
        "day_range": int(day_range), "record_count": len(frame),
        "documentation": "https://firms.modaps.eosdis.nasa.gov/api/area/",
        "interpretation": "A detection is a candidate fire/thermal anomaly. Assess confidence, acquisition time, cloud/overpass coverage and distance before contextual use.",
    }
    return frame, metadata


def external_source_catalogue() -> list[dict[str, str]]:
    """Machine-readable integration register, including products requiring separate auth/workflows."""
    return [
        {"source": "OpenAQ", "status": "connector_available", "data_class": "sensor measurements",
         "auth": "OPENAQ_API_KEY", "limitation": "Latest endpoint is not a complete chronological feed."},
        {"source": "India OGD/CPCB catalogue", "status": "configurable_connector_available",
         "data_class": "government-published resource", "auth": "DATA_GOV_IN_API_KEY + exact resource ID",
         "limitation": "Map fields only after schema and unit verification."},
        {"source": "NASA FIRMS", "status": "connector_available", "data_class": "satellite fire detections",
         "auth": "NASA_FIRMS_MAP_KEY", "limitation": "Thermal anomalies are not PM2.5 measurements or source proof."},
        {"source": "Sentinel-5P TROPOMI", "status": "catalogued_not_ingested",
         "data_class": "satellite column trace-gas products", "auth": "Earthdata / product-specific access",
         "limitation": "NO2 column is not surface NO2 or PM2.5."},
        {"source": "NASA MAIAC MCD19A2", "status": "catalogued_not_ingested",
         "data_class": "satellite aerosol optical depth", "auth": "NASA Earthdata",
         "limitation": "AOD is a column optical property, not surface PM2.5; retrieval gaps and vertical profile matter."},
        {"source": "Open-Meteo", "status": "existing_connector",
         "data_class": "weather and CAMS model estimates", "auth": "Keyless public endpoint subject to terms",
         "limitation": "Provider-modelled grid estimates, not ground station measurements."},
    ]
