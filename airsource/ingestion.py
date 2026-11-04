"""Canonical, provenance-preserving adapters for external observations."""
from __future__ import annotations
import hashlib, json
from typing import Any
import pandas as pd

CANONICAL_COLUMNS = ["observation_id", "source", "source_record_id", "location_id", "station_id",
 "parameter", "value", "unit", "observed_at", "available_at", "latitude", "longitude",
 "data_class", "quality_flag", "raw_payload_hash", "retrieved_at"]


def _hash_record(record: dict[str, Any]) -> str:
    raw = json.dumps(record, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def canonicalize_openaq(frame: pd.DataFrame, metadata: dict) -> pd.DataFrame:
    """Map the V6 OpenAQ latest response. No unit conversion or availability-time invention."""
    rows=[]
    for row in frame.to_dict("records"):
        source_id = row.get("sensor_id")
        stamp = row.get("timestamp")
        rec = {"source":"OpenAQ", "source_record_id":str(source_id) if source_id is not None else None,
          "location_id":str(row.get("location_id")) if row.get("location_id") is not None else None,
          "station_id":None, "parameter":str(row.get("parameter") or "unknown").strip().lower(),
          "value":pd.to_numeric(row.get("value"), errors="coerce"), "unit":row.get("unit"),
          "observed_at":pd.to_datetime(stamp, utc=True, errors="coerce"), "available_at":None,
          "latitude":row.get("latitude"), "longitude":row.get("longitude"),
          "data_class":"ground_sensor_measurement", "quality_flag":"unverified_provider_record",
          "retrieved_at":metadata.get("retrieved_at_utc")}
        rec["raw_payload_hash"]=_hash_record(row)
        rec["observation_id"]=_hash_record({k:rec.get(k) for k in ("source","source_record_id","parameter","observed_at","raw_payload_hash")})
        rows.append(rec)
    return pd.DataFrame(rows, columns=CANONICAL_COLUMNS)


def canonicalize_firms(frame: pd.DataFrame, metadata: dict) -> pd.DataFrame:
    """Map FIRMS detections as satellite context, never as pollutant measurements."""
    rows=[]
    for row in frame.to_dict("records"):
        stamp = row.get("acq_datetime")
        if pd.isna(stamp) and row.get("acq_date") and row.get("acq_time") is not None:
            try: stamp = pd.to_datetime(str(row["acq_date"])+str(int(row["acq_time"])).zfill(4), format="%Y%m%d%H%M", utc=True)
            except (ValueError, TypeError): stamp = None
        rec={"source":"NASA FIRMS", "source_record_id":None, "location_id":None, "station_id":None,
          "parameter":"fire_thermal_anomaly", "value":pd.to_numeric(row.get("frp"), errors="coerce"),
          "unit":"MW" if row.get("frp") is not None else None,
          "observed_at":pd.to_datetime(stamp, utc=True, errors="coerce"), "available_at":None,
          "latitude":row.get("latitude"), "longitude":row.get("longitude"),
          "data_class":"satellite_fire_detection", "quality_flag":str(row.get("confidence", "not_supplied")),
          "retrieved_at":metadata.get("retrieved_at_utc"), "raw_payload_hash":_hash_record(row)}
        rec["observation_id"]=_hash_record({k:rec.get(k) for k in ("source","raw_payload_hash")})
        rows.append(rec)
    return pd.DataFrame(rows, columns=CANONICAL_COLUMNS)


def validate_canonical(frame: pd.DataFrame) -> dict:
    missing=[c for c in CANONICAL_COLUMNS if c not in frame.columns]
    if missing: raise ValueError(f"Missing canonical columns: {missing}")
    return {"rows":len(frame), "missing_observation_ids":int(frame.observation_id.isna().sum()),
      "missing_observed_at":int(frame.observed_at.isna().sum()),
      "data_classes":sorted(frame.data_class.dropna().astype(str).unique().tolist()),
      "unknown_units_preserved":True}
