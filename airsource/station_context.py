"""Descriptive multi-station context for the separate 2018–2019 benchmark.

This module does not forecast, interpolate geographic surfaces, or infer emission
sources. Its outlier score compares same-hour station observations only.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {"timestamp", "station", "pm25"}


def load_station_history(path: str | Path) -> pd.DataFrame:
    """Read the attributed hourly benchmark and validate its station-time keys."""
    frame = pd.read_csv(path, compression="infer")
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Multi-station CSV is missing required columns: {sorted(missing)}")
    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    frame = frame.dropna(subset=["timestamp", "station"])
    frame["timestamp"] = frame["timestamp"].dt.tz_convert("Asia/Kolkata")
    frame["station"] = frame["station"].astype(str).str.strip()
    frame["pm25"] = pd.to_numeric(frame["pm25"], errors="coerce")
    frame.loc[frame["pm25"] < 0, "pm25"] = np.nan
    frame = frame.loc[frame["station"] != ""].sort_values(["timestamp", "station"])
    if frame.duplicated(["timestamp", "station"]).any():
        raise ValueError("Multi-station data contains duplicate station/timestamp rows")
    if frame.empty:
        raise ValueError("Multi-station dataset has no valid timestamped rows")
    return frame.reset_index(drop=True)


def station_coverage(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize observed rows and valid PM2.5 coverage per station."""
    summary = frame.groupby("station", sort=True).agg(
        first_seen=("timestamp", "min"),
        last_seen=("timestamp", "max"),
        hourly_rows=("timestamp", "size"),
        valid_pm25=("pm25", "count"),
    ).reset_index()
    summary["pm25_coverage_pct"] = (100 * summary["valid_pm25"] / summary["hourly_rows"]).round(1)
    return summary


def daily_station_means(frame: pd.DataFrame, minimum_hours: int = 18) -> pd.DataFrame:
    """Return daily observed means; omit days without the configured hourly support."""
    chunks = []
    for station, group in frame.groupby("station", sort=True):
        daily = group.set_index("timestamp")["pm25"].resample("1D").agg(["mean", "count"])
        daily.loc[daily["count"] < minimum_hours, "mean"] = np.nan
        daily["station"] = station
        chunks.append(daily.rename_axis("date").reset_index())
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(
        columns=["date", "mean", "count", "station"]
    )


def same_hour_network_outliers(frame: pd.DataFrame, threshold: float = 3.5,
                               minimum_stations: int = 4) -> pd.DataFrame:
    """Screen unusual same-hour station values using a robust network-relative score.

    A flagged value is only unusual relative to other stations in that hour. This
    is not a validated incident detector and does not identify a pollution source.
    """
    values = frame.pivot(index="timestamp", columns="station", values="pm25")
    count = values.count(axis=1)
    median = values.median(axis=1, skipna=True)
    deviations = values.sub(median, axis=0).abs()
    mad = deviations.median(axis=1, skipna=True)
    denominator = mad.replace(0, np.nan)
    robust_score = values.sub(median, axis=0).div(denominator, axis=0) * 0.6745
    flagged = robust_score.where(count.ge(minimum_stations), axis=0).where(
        robust_score.abs().ge(threshold)
    )
    out = flagged.stack().rename("robust_score").reset_index().dropna(subset=["robust_score"])
    if out.empty:
        return pd.DataFrame(columns=["timestamp", "station", "pm25", "network_median",
                                    "robust_score", "stations_reporting"])
    out = out.rename(columns={"level_1": "station"})
    out["pm25"] = [values.loc[t, s] for t, s in zip(out["timestamp"], out["station"])]
    out["network_median"] = [median.loc[t] for t in out["timestamp"]]
    out["stations_reporting"] = [int(count.loc[t]) for t in out["timestamp"]]
    out["robust_score"] = out["robust_score"].round(2)
    return out.assign(_magnitude=out["robust_score"].abs()).sort_values(
        "_magnitude", ascending=False
    ).drop(columns="_magnitude").head(100).reset_index(drop=True)
