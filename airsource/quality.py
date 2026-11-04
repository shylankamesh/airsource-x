"""Data-quality diagnostics for station observations.

These checks describe data fitness; they do not silently repair or impute values.
"""
from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd

from .data import POLLUTANTS, WEATHER

PHYSICAL_RANGES = {
    "pm25": (0.0, 2000.0), "pm10": (0.0, 3000.0), "no2": (0.0, 2000.0),
    "co": (0.0, 100000.0), "so2": (0.0, 2000.0), "o3": (0.0, 2000.0),
    "humidity_pct": (0.0, 100.0), "wind_speed_kmh": (0.0, 300.0),
    "wind_direction_deg": (0.0, 360.0), "precipitation_mm": (0.0, 1000.0),
}


def audit_observations(frame: pd.DataFrame, *, expected_frequency: str = "1h",
                       now: pd.Timestamp | None = None) -> dict[str, Any]:
    """Return a JSON-friendly quality summary without changing the input frame."""
    required = {"station", "timestamp", "pm25"}
    missing_columns = sorted(required - set(frame.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce", utc=True)
    invalid_timestamps = int(data["timestamp"].isna().sum())
    valid = data.dropna(subset=["timestamp"])
    duplicate_keys = int(valid.duplicated(["station", "timestamp"]).sum())
    missing_by_column = {c: int(data[c].isna().sum()) for c in data.columns if c not in {"station", "timestamp"}}
    range_violations: dict[str, int] = {}
    for column, (low, high) in PHYSICAL_RANGES.items():
        if column in data:
            values = pd.to_numeric(data[column], errors="coerce")
            count = int(((values < low) | (values > high)).sum())
            if count:
                range_violations[column] = count
    gaps = {}
    for station, group in valid.groupby("station"):
        stamps = group["timestamp"].drop_duplicates().sort_values()
        if len(stamps) > 1:
            deltas = stamps.diff().dropna()
            expected = pd.Timedelta(expected_frequency)
            gaps[str(station)] = int((deltas > expected).sum())
        else:
            gaps[str(station)] = 0
    latest = valid["timestamp"].max() if not valid.empty else pd.NaT
    current = pd.Timestamp.now(tz="UTC") if now is None else pd.Timestamp(now)
    if current.tzinfo is None:
        current = current.tz_localize("UTC")
    else:
        current = current.tz_convert("UTC")
    age_hours = None if pd.isna(latest) else round((current - latest).total_seconds() / 3600, 2)
    station_summary = []
    for station, group in valid.groupby("station", sort=True):
        station_summary.append({
            "station": str(station), "rows": int(len(group)),
            "first_timestamp_utc": group["timestamp"].min().isoformat(),
            "last_timestamp_utc": group["timestamp"].max().isoformat(),
            "valid_pm25": int(group["pm25"].notna().sum()),
            "pm25_missing_fraction": round(float(group["pm25"].isna().mean()), 4),
            "gap_count": gaps[str(station)],
        })
    return {
        "row_count": int(len(data)), "station_count": int(valid["station"].nunique()),
        "invalid_timestamps": invalid_timestamps, "duplicate_station_timestamps": duplicate_keys,
        "missing_by_column": missing_by_column, "range_violations": range_violations,
        "gap_count_by_station": gaps, "latest_timestamp_utc": None if pd.isna(latest) else latest.isoformat(),
        "latest_data_age_hours": age_hours, "stations": station_summary,
        "policy": "Diagnostics only: no interpolation, zero filling, clipping, or silent row deletion.",
    }
