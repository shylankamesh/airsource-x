"""Evidence-first screening rules with explicit missingness and ablation."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _last_and_reference(frame: pd.DataFrame, station: str) -> tuple[pd.Series, pd.DataFrame]:
    own = frame.loc[frame["station"].astype(str) == station].sort_values("timestamp")
    own = own.dropna(subset=["pm25"])
    if len(own) < 2:
        raise ValueError("Choose a station with at least two PM2.5 observations.")
    return own.iloc[-1], own.iloc[:-1]


def _is_high(value: Any, reference: pd.Series, quantile: float = 0.9) -> bool | None:
    history = pd.to_numeric(reference, errors="coerce").dropna()
    if pd.isna(value) or len(history) < 24:
        return None
    return bool(float(value) >= float(history.quantile(quantile)))


def investigate(frame: pd.DataFrame, station: str, excluded_families: set[str] | None = None) -> dict[str, Any]:
    """Create inspectable screening cards; never output a proven emission source."""
    excluded = excluded_families or set()
    current, reference = _last_and_reference(frame, station)
    claims: list[dict[str, Any]] = []
    missing_sources: list[str] = []
    available = set(frame.columns)

    # Dust-like coarse particle pattern: three independent-looking signals,
    # presented as a heuristic and not a source attribution.
    family = "Coarse particle + wind"
    if family in excluded:
        claims.append({"hypothesis": "Dust-like coarse-particle conditions", "status": "Not assessed",
                       "family": family, "supports": [], "contradicts": [],
                       "reason": "This evidence family was removed in the counterfactual view."})
    elif "pm10" not in available or "wind_speed_kmh" not in available:
        if "pm10" not in available:
            missing_sources.append("PM10")
        if "wind_speed_kmh" not in available:
            missing_sources.append("Wind speed")
        claims.append({"hypothesis": "Dust-like coarse-particle conditions", "status": "Insufficient evidence",
                       "family": family, "supports": [], "contradicts": [],
                       "reason": "PM10 and wind context are both required for this screening rule."})
    else:
        ratio = pd.to_numeric(reference.get("pm10", pd.Series(dtype=float)), errors="coerce") / pd.to_numeric(reference.get("pm25", pd.Series(dtype=float)), errors="coerce").replace(0, np.nan)
        now_ratio = current.get("pm10", np.nan) / max(float(current.get("pm25", np.nan)), 1e-6)
        high_pm10 = _is_high(current.get("pm10", np.nan), reference["pm10"])
        high_wind = _is_high(current.get("wind_speed_kmh", np.nan), reference["wind_speed_kmh"], 0.75)
        high_ratio = bool(len(ratio.dropna()) >= 24 and now_ratio >= ratio.dropna().quantile(0.75)) if pd.notna(now_ratio) else None
        states = [high_pm10, high_wind, high_ratio]
        if high_pm10 is None:
            missing_sources.append("PM10 history / coverage")
        if high_wind is None:
            missing_sources.append("Wind speed history / coverage")
        if high_ratio is None:
            missing_sources.append("Paired PM10 and PM2.5 history for particle ratio")
        supports = [label for label, ok in zip(("PM10 elevated against this station's history", "wind speed elevated against this station's history", "coarse-to-fine particle ratio elevated against this station's history"), states) if ok]
        contradictions = ["PM10 is not elevated relative to this station's history"] if high_pm10 is False else []
        enough = all(x is not None for x in states)
        status = "Pattern present" if enough and all(states) else ("Mixed evidence" if enough and supports else "No strong pattern" if enough else "Insufficient evidence")
        claims.append({"hypothesis": "Dust-like coarse-particle conditions", "status": status, "family": family,
                       "supports": supports, "contradicts": contradictions,
                       "reason": "A relative, data-driven heuristic only. It cannot distinguish dust from other coarse-particle sources or establish causality."})

    family = "Combustion co-pollutants"
    if family in excluded:
        claims.append({"hypothesis": "Combustion-compatible co-pollutant pattern", "status": "Not assessed",
                       "family": family, "supports": [], "contradicts": [],
                       "reason": "This evidence family was removed in the counterfactual view."})
    else:
        candidate = [c for c in ("co", "no2") if c in available]
        if not candidate:
            missing_sources.extend(["CO", "NO2"])
            claims.append({"hypothesis": "Combustion-compatible co-pollutant pattern", "status": "Insufficient evidence",
                           "family": family, "supports": [], "contradicts": [],
                           "reason": "CO and NO2 are not present in the uploaded data."})
        else:
            signals = {c.upper(): _is_high(current.get(c, np.nan), reference[c]) for c in candidate}
            support = [f"{c} is elevated relative to this station's history" for c, high in signals.items() if high]
            missing_sources.extend([f"{c} history / coverage" for c, high in signals.items() if high is None])
            measured = [v for v in signals.values() if v is not None]
            status = ("Mixed evidence" if support and any(high is False for high in signals.values()) else
                      "Pattern present" if support else ("No strong pattern" if measured else "Insufficient evidence"))
            claims.append({"hypothesis": "Combustion-compatible co-pollutant pattern", "status": status,
                           "family": family, "supports": support,
                           "contradicts": [f"{c} is not elevated relative to this station's history" for c, high in signals.items() if high is False],
                           "reason": "CO/NO2 co-occurrence is non-specific: traffic, industry, biomass burning and other processes can overlap. No source is assigned."})

    family = "Concurrent station context"
    if family in excluded:
        claims.append({"hypothesis": "Regional versus localized episode context", "status": "Not assessed",
                       "family": family, "supports": [], "contradicts": [],
                       "reason": "Concurrent station context was removed in the counterfactual view."})
    else:
        latest = frame.dropna(subset=["pm25"]).sort_values("timestamp").groupby("station", as_index=False).tail(1)
        latest = latest.loc[latest["station"].astype(str) != station]
        if len(latest) < 2:
            claims.append({"hypothesis": "Regional versus localized episode context", "status": "Insufficient spatial coverage",
                           "family": family, "supports": [], "contradicts": [],
                           "reason": "At least two concurrent peer monitors are needed for a useful spatial comparison."})
            missing_sources.append("At least two nearby monitors with synchronized observations")
        else:
            cutoff = current["timestamp"] - pd.Timedelta(hours=3)
            peer = frame.loc[(frame["timestamp"] >= cutoff) & (frame["timestamp"] <= current["timestamp"]) & (frame["station"].astype(str) != station)].dropna(subset=["pm25"])
            peers = peer.groupby("station").tail(1)
            if len(peers) >= 2:
                peer_median = float(peers["pm25"].median())
                local = float(current["pm25"])
                regional = sum(_is_high(row.pm25, frame.loc[frame.station == row.station, "pm25"].iloc[:-1]) is True for row in peers.itertuples())
                status = "Shared elevation across monitors" if regional >= 2 else "Spatial context is mixed"
                reason = f"{regional} of {len(peers)} peers are above their own historical 90th percentile; peer median is {peer_median:.1f} µg/m³. Monitor siting and timing limit interpretation."
                claims.append({"hypothesis": "Regional versus localized episode context", "status": status,
                               "family": family, "supports": [f"Concurrent peer-station median: {peer_median:.1f} µg/m³"],
                               "contradicts": [f"Selected station: {local:.1f} µg/m³"], "reason": reason})
            else:
                claims.append({"hypothesis": "Regional versus localized episode context", "status": "Insufficient spatial coverage",
                               "family": family, "supports": [], "contradicts": [],
                               "reason": "Fewer than two peer monitors have readings within three hours of the selected station."})
                missing_sources.append("Synchronized, quality-screened measurements from nearby monitors")

    available_statuses = [c["status"] for c in claims if c["status"] not in {"Not assessed", "Insufficient evidence", "Insufficient spatial coverage"}]
    if not available_statuses:
        summary = "Evidence is too sparse to screen the current episode. The app abstains from a source conclusion."
    elif "Mixed evidence" in available_statuses or "Spatial context is mixed" in available_statuses:
        summary = "The indicators do not agree cleanly. Keep competing explanations open and collect more discriminating evidence."
    else:
        summary = "One or more screening patterns are present. These are observations to investigate, not confirmed source attributions."
    next_step = _next_measurement(missing_sources, claims)
    return {"station": station, "timestamp": current["timestamp"], "pm25": float(current["pm25"]),
            "summary": summary, "claims": claims, "missing": sorted(set(missing_sources)),
            "next_step": next_step, "excluded_families": sorted(excluded),
            "limitation": "Single-station correlations, weather, co-pollutants and nearby activity cannot prove an emission source."
            }


def _next_measurement(missing: list[str], claims: list[dict[str, Any]]) -> str:
    if any("nearby monitors" in x.lower() or "peer" in x.lower() or "synchronized" in x.lower() for x in missing):
        return "Add synchronized PM2.5 and PM10 observations from two nearby upwind/downwind monitors; this is the largest current gap in regional-versus-local context."
    if any("PM10" in x for x in missing):
        return "Measure PM10 alongside PM2.5 at the same station and timestamp to assess whether coarse particles are elevated."
    if any(x in missing for x in ("CO", "NO2")):
        return "Add quality-controlled CO and NO2 measurements at the same station; these remain non-specific indicators, not a source label."
    return "Preserve an additional day of synchronized pollutant and weather observations, then compare the same screening rules with the episode baseline."
