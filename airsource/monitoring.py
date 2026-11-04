"""Source freshness and availability status helpers."""
from __future__ import annotations
import pandas as pd


def source_freshness(*, source: str, last_successful_retrieval: str | None,
                     expected_interval_hours: float, now: pd.Timestamp | None = None) -> dict:
    """Classify freshness from retrieval time, without treating missing as zero."""
    if expected_interval_hours <= 0:
        raise ValueError("expected_interval_hours must be positive")
    if not last_successful_retrieval:
        return {"source": source, "status": "UNAVAILABLE", "age_hours": None,
                "message": "No successful retrieval timestamp is recorded."}
    stamp = pd.Timestamp(last_successful_retrieval)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize("UTC")
    else:
        stamp = stamp.tz_convert("UTC")
    current = pd.Timestamp.now(tz="UTC") if now is None else pd.Timestamp(now)
    if current.tzinfo is None:
        current = current.tz_localize("UTC")
    else:
        current = current.tz_convert("UTC")
    age = max(0.0, (current - stamp).total_seconds() / 3600)
    if age <= expected_interval_hours:
        status = "FRESH"
    elif age <= expected_interval_hours * 2:
        status = "STALE"
    else:
        status = "OUTDATED"
    return {"source": source, "status": status, "age_hours": round(age, 2),
            "message": f"Last successful retrieval was {age:.1f} hours ago."}
