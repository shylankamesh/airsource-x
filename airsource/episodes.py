"""Transparent, non-causal detection of persistent multi-station PM2.5 episodes."""
from __future__ import annotations

import numpy as np
import pandas as pd


def detect_station_episodes(
    observations: pd.DataFrame,
    *,
    baseline_hours: int = 24,
    min_baseline_points: int = 12,
    min_excess_ug_m3: float = 25.0,
    robust_sigma_multiplier: float = 2.5,
    min_pm25_ug_m3: float = 75.0,
    min_duration_hours: int = 2,
    max_gap_hours: int = 1,
) -> pd.DataFrame:
    """Detect persistent station-level rises against a strictly prior rolling baseline.

    This is an anomaly-screening rule, not an official AQI threshold or source detector.
    Baseline and MAD use only earlier observations; short gaps are bridged only up to
    max_gap_hours when assembling an event, not by imputing concentration values.
    """
    required = {"timestamp", "station", "pm25"}
    missing = required - set(observations.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if baseline_hours < 4 or min_baseline_points < 3 or min_duration_hours < 1:
        raise ValueError("Baseline and duration parameters are too small.")
    data = observations[list(required)].copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce", utc=True)
    data["pm25"] = pd.to_numeric(data["pm25"], errors="coerce")
    data = data.dropna(subset=["timestamp", "station", "pm25"])
    data = data[np.isfinite(data["pm25"]) & (data["pm25"] >= 0)]
    data = data.sort_values(["station", "timestamp"]).drop_duplicates(["station", "timestamp"])
    events = []
    for station, group in data.groupby("station", sort=True):
        group = group.sort_values("timestamp").set_index("timestamp")
        # The data are expected hourly. Rolling time windows tolerate occasional gaps.
        prior = group["pm25"].rolling(f"{baseline_hours}h", closed="left",
                                      min_periods=min_baseline_points)
        baseline = prior.median()
        mad = prior.apply(lambda x: np.median(np.abs(x - np.median(x))), raw=True)
        robust_sigma = 1.4826 * mad
        excess_threshold = np.maximum(min_excess_ug_m3, robust_sigma_multiplier * robust_sigma)
        candidate = (group["pm25"] >= min_pm25_ug_m3) & (group["pm25"] - baseline >= excess_threshold)
        candidate = candidate.fillna(False)
        idx = np.flatnonzero(candidate.to_numpy())
        if len(idx) == 0:
            continue
        # Split runs when timestamps are separated by more than the permitted gap.
        runs = []
        start = previous = idx[0]
        times = group.index
        for current in idx[1:]:
            gap = (times[current] - times[previous]).total_seconds() / 3600
            if gap > max_gap_hours + 1e-9:
                runs.append((start, previous))
                start = current
            previous = current
        runs.append((start, previous))
        for start_i, end_i in runs:
            start_time, end_time = times[start_i], times[end_i]
            duration = int(round((end_time - start_time).total_seconds() / 3600)) + 1
            if duration < min_duration_hours:
                continue
            segment = group.iloc[start_i:end_i + 1]
            peak_time = segment["pm25"].idxmax()
            peak = float(segment["pm25"].max())
            base_value = float(baseline.loc[start_time]) if pd.notna(baseline.loc[start_time]) else np.nan
            events.append({
                "station": str(station), "onset": start_time, "end": end_time,
                "peak_time": peak_time, "peak_pm25_ug_m3": peak,
                "onset_pm25_ug_m3": float(group.loc[start_time, "pm25"]),
                "baseline_pm25_ug_m3": base_value,
                "excess_at_onset_ug_m3": float(group.loc[start_time, "pm25"] - base_value) if np.isfinite(base_value) else np.nan,
                "duration_hours": duration, "candidate_hours": len(segment),
            })
    columns = ["station", "onset", "end", "peak_time", "peak_pm25_ug_m3",
               "onset_pm25_ug_m3", "baseline_pm25_ug_m3", "excess_at_onset_ug_m3",
               "duration_hours", "candidate_hours"]
    return pd.DataFrame(events, columns=columns).sort_values("onset").reset_index(drop=True)


def group_network_episodes(
    station_events: pd.DataFrame, *, onset_link_hours: int = 3, min_stations: int = 2
) -> pd.DataFrame:
    """Group nearby-in-time station episodes; timing does not imply transport or causality."""
    if station_events.empty:
        return pd.DataFrame(columns=[
            "episode_id", "first_onset", "last_onset", "stations_affected",
            "station_count", "lead_station", "last_station", "onset_span_hours",
            "network_peak_pm25_ug_m3", "network_peak_time", "interpretation"
        ])
    required = {"station", "onset", "end", "peak_time", "peak_pm25_ug_m3"}
    if not required.issubset(station_events.columns):
        raise ValueError(f"Station event table missing: {sorted(required - set(station_events.columns))}")
    events = station_events.copy()
    for col in ("onset", "end", "peak_time"):
        events[col] = pd.to_datetime(events[col], utc=True)
    events = events.sort_values("onset").reset_index(drop=True)
    clusters, current = [], [0]
    cluster_first = events.loc[0, "onset"]
    for i in range(1, len(events)):
        if (events.loc[i, "onset"] - cluster_first).total_seconds() <= onset_link_hours * 3600:
            current.append(i)
        else:
            clusters.append(current)
            current = [i]
            cluster_first = events.loc[i, "onset"]
    clusters.append(current)
    rows = []
    for indices in clusters:
        part = events.iloc[indices].copy()
        # A station contributes once per network episode: retain its earliest onset.
        part = part.sort_values("onset").drop_duplicates("station", keep="first")
        if len(part) < min_stations:
            continue
        first = part["onset"].min()
        last = part["onset"].max()
        peak_row = part.loc[part["peak_pm25_ug_m3"].idxmax()]
        ordered = part.sort_values("onset")
        rows.append({
            "episode_id": f"EP-{first.strftime('%Y%m%dT%H%M')}",
            "first_onset": first, "last_onset": last,
            "stations_affected": ", ".join(ordered["station"].astype(str)),
            "station_count": int(part["station"].nunique()),
            "lead_station": str(ordered.iloc[0]["station"]),
            "last_station": str(ordered.iloc[-1]["station"]),
            "onset_span_hours": round((last - first).total_seconds() / 3600, 2),
            "network_peak_pm25_ug_m3": float(peak_row["peak_pm25_ug_m3"]),
            "network_peak_time": peak_row["peak_time"],
            "interpretation": "Temporally associated station anomalies; not source attribution or proof of plume movement.",
        })
    return pd.DataFrame(rows)


def wind_quality_summary(observations: pd.DataFrame, *, max_plausible_speed_kmh: float = 60.0) -> dict:
    """Summarise wind plausibility before any exploratory use; does not repair values."""
    required = {"wind_speed_kmh", "wind_direction_deg"}
    if not required.issubset(observations.columns):
        return {"available": False, "usable_for_context": False, "reason": "Wind speed/direction columns are absent."}
    speed = pd.to_numeric(observations["wind_speed_kmh"], errors="coerce")
    direction = pd.to_numeric(observations["wind_direction_deg"], errors="coerce")
    valid = speed.between(0, max_plausible_speed_kmh) & direction.between(0, 360)
    total = len(observations)
    fraction = float(valid.mean()) if total else 0.0
    return {
        "available": True, "usable_for_context": bool(total and fraction >= 0.9),
        "rows": int(total), "plausible_rows": int(valid.sum()),
        "plausible_fraction": fraction, "max_plausible_speed_kmh": max_plausible_speed_kmh,
        "observed_max_speed_kmh": float(speed.max()) if speed.notna().any() else None,
        "reason": ("At least 90% of rows pass the screening bounds; still verify units, sensor QA and provenance."
                   if fraction >= 0.9 else
                   "Wind data fail the preliminary plausibility screen; do not use them for transport interpretation."),
    }
