"""Validation for sourced station metadata; coordinates are never guessed."""
from __future__ import annotations
import pandas as pd

REQUIRED_COLUMNS = ["station_id", "station_name", "latitude", "longitude", "site_type",
                    "valid_from", "metadata_source", "coordinate_quality"]


def validate_station_registry(frame: pd.DataFrame) -> dict:
    errors, warnings = [], []
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        return {"valid": False, "errors": [f"Missing required column: {c}" for c in missing], "warnings": []}
    data = frame.copy()
    ids = data["station_id"].astype("string").str.strip()
    if ids.isna().any() or ids.eq("").any(): errors.append("station_id contains blank values")
    if ids.duplicated().any(): errors.append("station_id values must be unique")
    for col, low, high in [("latitude", -90, 90), ("longitude", -180, 180)]:
        vals = pd.to_numeric(data[col], errors="coerce")
        invalid = vals.notna() & ~vals.between(low, high)
        if invalid.any(): errors.append(f"{col} contains values outside [{low}, {high}]")
        if vals.isna().any(): warnings.append(f"{col} is missing for {int(vals.isna().sum())} station(s); no map positioning should be inferred")
    start = pd.to_datetime(data["valid_from"], errors="coerce", utc=True)
    end = pd.to_datetime(data["valid_to"], errors="coerce", utc=True) if "valid_to" in data else pd.Series(pd.NaT, index=data.index, dtype="datetime64[ns, UTC]")
    if start.isna().any(): errors.append("valid_from must contain valid dates")
    comparable = end.notna() & start.notna()
    if (end[comparable] < start[comparable]).any(): errors.append("valid_to cannot precede valid_from")
    for col in ("metadata_source", "coordinate_quality"):
        if data[col].isna().any() or data[col].astype(str).str.strip().eq("").any():
            warnings.append(f"{col} is missing; metadata provenance is incomplete")
    return {"valid": not errors, "station_count": int(len(data)), "errors": errors, "warnings": warnings,
            "policy": "Only supplied, range-checked coordinates are accepted; missing coordinates remain unverified."}
