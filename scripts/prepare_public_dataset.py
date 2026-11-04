"""Prepare the cited CC BY 4.0 Delhi multi-site dataset for AirSource X."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from airsource.data import prepare_observations

RAW_ROOT = ROOT / "data" / "raw" / "mendeley-bzhzr9b64v"
OUTPUT = ROOT / "data" / "processed" / "delhi_multisite_hourly.csv"


def main() -> None:
    files = sorted(RAW_ROOT.rglob("*_Hourly.csv"))
    if len(files) != 6:
        raise SystemExit(f"Expected six Mendeley station CSVs under {RAW_ROOT}; found {len(files)}")

    frames = []
    for path in files:
        source = pd.read_csv(path)
        required = {"year", "month", "day", "hour", "PM2.5"}
        if not required.issubset(source.columns):
            raise SystemExit(f"Missing expected columns in {path.name}: {sorted(required - set(source.columns))}")
        frame = pd.DataFrame({
            "timestamp": pd.to_datetime({
                "year": source["year"], "month": source["month"],
                "day": source["day"], "hour": source["hour"],
            }, errors="coerce"),
            "station": path.stem.removesuffix("_Hourly"),
            "pm25": source["PM2.5"],
            "pm10": source.get("PM10"),
            "no2": source.get("NO2"),
            "co": source.get("CO"),
            "so2": source.get("SO2"),
            "o3": source.get("Ozone"),
            "temperature_c": source.get("AT"),
            "humidity_pct": source.get("RH"),
            # Dataset weather metadata in the cited literature reports WS in m/s;
            # AirSource's canonical field is km/h.
            "wind_speed_kmh": pd.to_numeric(source.get("WS"), errors="coerce") * 3.6,
            "wind_direction_deg": source.get("WD"),
            "barometric_pressure_mmhg": source.get("BP"),
            "solar_radiation_w_m2": source.get("SR"),
        })
        frames.append(frame)

    raw = pd.concat(frames, ignore_index=True)
    hourly, quality = prepare_observations(raw)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    hourly.to_csv(OUTPUT, index=False, float_format="%.5f")
    summary = hourly.groupby("station").agg(
        first_seen=("timestamp", "min"), last_seen=("timestamp", "max"),
        hourly_rows=("timestamp", "size"), valid_pm25=("pm25", "count"),
    )
    print(f"Input records: {len(raw):,}; prepared hourly records: {len(hourly):,}")
    print(f"Discarded timestamps: {quality['discarded_invalid_timestamps']}; duplicates: {quality['duplicate_station_timestamps']}")
    print(summary.to_string())
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
