"""As-of replay filtering to prevent use of information unavailable at issue time."""
from __future__ import annotations
import pandas as pd


def as_of_replay(frame: pd.DataFrame, as_of, *, available_at_col: str = "available_at",
                 observed_at_col: str = "observed_at") -> pd.DataFrame:
    """Return records observable by `as_of`; never infer availability from observation time.

    Both timestamps must be present and timezone-aware or parseable as UTC.
    Records with missing/invalid timestamps are excluded and reported separately
    by callers through their source-quality audit.
    """
    required = {available_at_col, observed_at_col}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Replay requires explicit timestamp columns: {', '.join(sorted(missing))}")
    cutoff = pd.Timestamp(as_of)
    cutoff = cutoff.tz_localize("UTC") if cutoff.tzinfo is None else cutoff.tz_convert("UTC")
    data = frame.copy()
    available = pd.to_datetime(data[available_at_col], errors="coerce", utc=True)
    observed = pd.to_datetime(data[observed_at_col], errors="coerce", utc=True)
    # Also exclude impossible records that claim availability before observation.
    mask = available.notna() & observed.notna() & (available <= cutoff) & (observed <= available)
    result = data.loc[mask].copy()
    result[available_at_col] = available.loc[mask]
    result[observed_at_col] = observed.loc[mask]
    return result.sort_values(available_at_col).reset_index(drop=True)
