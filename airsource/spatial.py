"""Spatial context for multi-station observations.

Distance is computed from sourced station coordinates. Concentration comparisons use
exactly aligned timestamps; this module never interpolates missing station values.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    vals = np.asarray([lat1, lon1, lat2, lon2], dtype=float)
    if not np.isfinite(vals).all():
        raise ValueError("All coordinates must be finite")
    if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90 and -180 <= lon1 <= 180 and -180 <= lon2 <= 180):
        raise ValueError("Coordinates are outside valid latitude/longitude ranges")
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi, dlambda = np.radians(lat2-lat1), np.radians(lon2-lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return float(2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1))))


def attach_station_metadata(observations: pd.DataFrame, registry: pd.DataFrame) -> pd.DataFrame:
    required_obs = {"station", "timestamp", "pm25"}
    missing = required_obs - set(observations.columns)
    if missing:
        raise ValueError(f"Observations missing columns: {', '.join(sorted(missing))}")
    from airsource.station_registry import validate_station_registry
    audit = validate_station_registry(registry)
    if not audit["valid"]:
        raise ValueError("Invalid station registry: " + "; ".join(audit["errors"]))
    coords = registry[["station_id", "latitude", "longitude", "station_name", "metadata_source", "coordinate_quality"]].copy()
    coords["latitude"] = pd.to_numeric(coords["latitude"], errors="coerce")
    coords["longitude"] = pd.to_numeric(coords["longitude"], errors="coerce")
    if coords[["latitude", "longitude"]].isna().any().any():
        raise ValueError("Spatial analysis requires verified coordinates for every registered station")
    data = observations.copy()
    data["station"] = data["station"].astype(str)
    coords["station_id"] = coords["station_id"].astype(str)
    data = data.merge(coords, left_on="station", right_on="station_id", how="inner", validate="many_to_one")
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce", utc=True)
    data["pm25"] = pd.to_numeric(data["pm25"], errors="coerce")
    return data.dropna(subset=["timestamp", "pm25", "latitude", "longitude"])


def station_distance_matrix(registry: pd.DataFrame) -> pd.DataFrame:
    records = registry.dropna(subset=["latitude", "longitude"]).to_dict("records")
    rows = []
    for a in records:
        row = {"station_id": a["station_id"]}
        for b in records:
            row[str(b["station_id"])] = haversine_km(float(a["latitude"]), float(a["longitude"]),
                                                       float(b["latitude"]), float(b["longitude"]))
        rows.append(row)
    return pd.DataFrame(rows).set_index("station_id") if rows else pd.DataFrame()


def synchronized_station_snapshot(observations: pd.DataFrame, registry: pd.DataFrame,
                                  *, max_age_minutes: int = 0) -> pd.DataFrame:
    """Latest common timestamp with at least two stations; exact-hour alignment by default."""
    data = attach_station_metadata(observations, registry)
    wide = data.pivot_table(index="timestamp", columns="station", values="pm25", aggfunc="mean")
    if max_age_minutes > 0:
        # Optional as-of snapshot: each station's latest value must be within the stated age.
        latest = data.sort_values("timestamp").groupby("station").tail(1)
        cutoff = latest["timestamp"].max()
        latest = latest.loc[latest["timestamp"] >= cutoff - pd.Timedelta(minutes=max_age_minutes)]
        return latest[["station", "timestamp", "pm25", "latitude", "longitude", "station_name"]].sort_values("station")
    complete = wide.dropna(thresh=2)
    if complete.empty:
        return pd.DataFrame(columns=["timestamp", "station", "pm25", "latitude", "longitude", "station_name"])
    timestamp = complete.index.max()
    selected = data.loc[data["timestamp"].eq(timestamp),
                        ["station", "timestamp", "pm25", "latitude", "longitude", "station_name"]]
    return selected.sort_values("station").reset_index(drop=True)


def pairwise_spatial_statistics(observations: pd.DataFrame, registry: pd.DataFrame,
                                *, min_overlap: int = 48) -> pd.DataFrame:
    data = attach_station_metadata(observations, registry)
    wide = data.pivot_table(index="timestamp", columns="station", values="pm25", aggfunc="mean")
    distances = station_distance_matrix(registry)
    rows = []
    for i, a in enumerate(wide.columns):
        for b in wide.columns[i+1:]:
            pair = wide[[a, b]].dropna()
            corr = pair[a].corr(pair[b]) if len(pair) >= min_overlap else np.nan
            rows.append({"station_a": a, "station_b": b,
                         "distance_km": float(distances.loc[a, b]) if a in distances.index and b in distances.columns else np.nan,
                         "overlap_hours": int(len(pair)),
                         "pearson_r": float(corr) if pd.notna(corr) else np.nan,
                         "correlation_status": "computed" if pd.notna(corr) else f"needs {min_overlap} overlapping hourly rows"})
    return pd.DataFrame(rows)


def spatial_coverage_summary(observations: pd.DataFrame, registry: pd.DataFrame) -> dict:
    data = attach_station_metadata(observations, registry)
    counts = data.groupby("station")["timestamp"].agg(["count", "min", "max"]).reset_index()
    return {"registered_stations": int(registry["station_id"].nunique()),
            "stations_with_observations": int(counts["station"].nunique()),
            "observation_rows_with_coordinates": int(len(data)),
            "time_basis": "UTC-normalized timestamps; source local timezone is preserved as instant",
            "interpolation": "none", "station_coverage": counts.to_dict("records")}
