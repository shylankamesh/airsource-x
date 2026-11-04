"""Canonicalise and quality-check hourly station observations."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

TZ = "Asia/Kolkata"
POLLUTANTS = ["pm25", "pm10", "no2", "co", "so2", "o3"]
WEATHER = ["temperature_c", "humidity_pct", "wind_speed_kmh", "wind_direction_deg", "precipitation_mm",
           "barometric_pressure_mmhg", "solar_radiation_w_m2"]
NUMERIC = POLLUTANTS + WEATHER + ["latitude", "longitude"]
ALIASES = {
    "timestamp": {"timestamp", "datetime", "date_time", "date", "time", "local_time", "datetime_local", "datetime_ist", "timestamp_ist"},
    "station": {"station", "station_id", "station_name", "site", "site_id", "location", "monitor", "monitor_name"},
    "pm25": {"pm25", "pm2_5", "pm2_5_ug_m3", "pm25_ug_m3", "pm2_5_concentration", "pm2_5_µg_m3"},
    "pm10": {"pm10", "pm10_ug_m3", "pm10_concentration"},
    "no2": {"no2", "nitrogen_dioxide", "nitrogen_dioxide_ug_m3"},
    "co": {"co", "carbon_monoxide", "carbon_monoxide_ug_m3"},
    "so2": {"so2", "sulphur_dioxide", "sulfur_dioxide"},
    "o3": {"o3", "ozone"},
    "temperature_c": {"temperature", "temperature_2m", "temp", "temp_c", "temperature_c", "at"},
    "humidity_pct": {"humidity", "relative_humidity", "relative_humidity_2m", "humidity_pct", "rh"},
    "wind_speed_kmh": {"wind_speed", "wind_speed_10m", "wind_speed_kmh", "windspeed", "ws"},
    "wind_direction_deg": {"wind_direction", "wind_direction_10m", "wind_direction_deg", "wind_dir", "wd"},
    "precipitation_mm": {"precipitation", "precipitation_mm", "rain"},
    "barometric_pressure_mmhg": {"barometric_pressure", "pressure", "pressure_mmhg", "bp"},
    "solar_radiation_w_m2": {"solar_radiation", "solar_radiation_w_m2", "sr"},
    "latitude": {"lat", "latitude"},
    "longitude": {"lon", "lng", "longitude"},
}


def _slug(value: Any) -> str:
    text = str(value).strip().lower().replace("µ", "u").replace("μ", "u").replace("³", "3").replace("²", "2")
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def canonicalise_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Rename common pollutant and weather headers to AirSource's schema."""
    reverse = {alias: canonical for canonical, aliases in ALIASES.items() for alias in aliases}
    rename = {}
    for col in frame.columns:
        key = _slug(col)
        if key in reverse:
            rename[col] = reverse[key]
    out = frame.rename(columns=rename).copy()
    # Keep the first column if a file contains two aliases for the same pollutant.
    out = out.loc[:, ~out.columns.duplicated()]
    return out


def prepare_observations(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return hourly, station-separated observations without filling data gaps.

    Naive timestamps are interpreted as Asia/Kolkata local time. Aware timestamps
    are converted to that timezone. No pollutant values are interpolated.
    """
    data = canonicalise_columns(frame)
    if "timestamp" not in data or "pm25" not in data:
        raise ValueError("CSV must include a timestamp column and PM2.5 (for example: timestamp, pm25).")
    original_rows = len(data)
    def parse_local(value):
        if pd.isna(value):
            return pd.NaT
        try:
            stamp = pd.Timestamp(value)
            if stamp.tzinfo is None:
                return stamp.tz_localize(TZ, ambiguous="NaT", nonexistent="shift_forward")
            return stamp.tz_convert(TZ)
        except (TypeError, ValueError, OverflowError):
            return pd.NaT

    parsed = pd.to_datetime(data["timestamp"].map(parse_local), errors="coerce", utc=True).dt.tz_convert(TZ)
    data["timestamp"] = parsed
    invalid_time = int(data["timestamp"].isna().sum())
    data = data.dropna(subset=["timestamp"]).copy()
    if "station" not in data:
        data["station"] = "Uploaded station"
    data["station"] = data["station"].fillna("Unknown station").astype(str).str.strip()
    if not data["station"].any():
        data["station"] = "Uploaded station"

    for col in NUMERIC:
        if col in data:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    negative_counts = {}
    for col in POLLUTANTS + ["precipitation_mm", "wind_speed_kmh"]:
        if col in data:
            negative_counts[col] = int((data[col] < 0).sum())
            data.loc[data[col] < 0, col] = np.nan
    duplicate_count = int(data.duplicated(["station", "timestamp"]).sum())
    data = data.sort_values("timestamp").drop_duplicates(["station", "timestamp"], keep="last")

    frames = []
    for station, group in data.groupby("station", sort=True):
        values = [col for col in NUMERIC if col in group.columns]
        hourly = (group.set_index("timestamp")[values]
                  .sort_index().resample("1h").mean())
        hourly["station"] = station
        hourly.index.name = "timestamp"
        frames.append(hourly.reset_index())
    if not frames:
        raise ValueError("No valid timestamped rows were found in this file.")
    hourly = pd.concat(frames, ignore_index=True)
    hourly = hourly.sort_values(["timestamp", "station"]).reset_index(drop=True)
    coverage = hourly.groupby("station").agg(
        first_seen=("timestamp", "min"), last_seen=("timestamp", "max"), hourly_rows=("timestamp", "size"),
        valid_pm25=("pm25", "count"),
    ).reset_index()
    report = {
        "input_rows": original_rows,
        "discarded_invalid_timestamps": invalid_time,
        "duplicate_station_timestamps": duplicate_count,
        "negative_values_set_missing": {k: v for k, v in negative_counts.items() if v},
        "stations": int(hourly["station"].nunique()),
        "hourly_rows": int(len(hourly)),
        "missing_pm25_rows": int(hourly["pm25"].isna().sum()),
        "coverage": coverage,
        "timestamp_policy": f"Naive timestamps interpreted as {TZ}; timezone-aware values converted to {TZ}.",
        "missing_policy": "Missing pollutant values remain missing; no interpolation or zero filling was applied.",
    }
    return hourly, report


def latest_by_station(frame: pd.DataFrame) -> pd.DataFrame:
    """Latest non-empty row for each station, preserving its source timestamp."""
    rows = []
    for station, group in frame.groupby("station", sort=True):
        available = group.dropna(subset=["pm25"])
        if not available.empty:
            rows.append(available.sort_values("timestamp").iloc[-1])
    return pd.DataFrame(rows).reset_index(drop=True) if rows else pd.DataFrame()
