"""Compact reliability summaries from benchmark and source-ingestion records."""
from __future__ import annotations
from typing import Any
import pandas as pd
from .monitoring import source_freshness


def benchmark_summary(report: dict[str, Any]) -> pd.DataFrame:
    """Read the repository benchmark's explicit holdout run records."""
    rows=[]
    for run in report.get("runs", []):
        rows.append({"station":run.get("station"),"horizon":run.get("horizon"),"model":run.get("model"),
          "mae_ug_m3":run.get("mae"),"rmse_ug_m3":run.get("rmse"),"bias_ug_m3":run.get("bias"),
          "samples":run.get("samples"),"interval_test_coverage":run.get("interval_test_coverage"),
          "mean_test_interval_width_ug_m3":run.get("mean_test_interval_width_ug_m3")})
    return pd.DataFrame(rows)


def ingestion_freshness(history: pd.DataFrame, *, expected_interval_hours: float=24.0, now=None) -> pd.DataFrame:
    if history.empty:
        return pd.DataFrame(columns=["source","status","age_hours","message"])
    rows=[]
    for source, group in history.groupby("source"):
        successful=group[group["status"]=="success"]
        last=successful["completed_at"].max() if not successful.empty else None
        rows.append(source_freshness(source=str(source),last_successful_retrieval=last,
          expected_interval_hours=expected_interval_hours,now=now))
    return pd.DataFrame(rows)
