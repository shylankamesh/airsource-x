"""Transparent forecast evaluation metrics for held-out predictions.

Event metrics require an explicit concentration threshold; they are not AQI labels.
"""
from __future__ import annotations
from typing import Any
import numpy as np
import pandas as pd


def evaluate_predictions(actual, predicted, *, severe_threshold: float | None = None) -> dict[str, Any]:
    y = pd.to_numeric(pd.Series(actual), errors="coerce").to_numpy(dtype=float)
    p = pd.to_numeric(pd.Series(predicted), errors="coerce").to_numpy(dtype=float)
    if len(y) != len(p):
        raise ValueError("actual and predicted must have the same length")
    mask = np.isfinite(y) & np.isfinite(p)
    y, p = y[mask], p[mask]
    if not len(y):
        return {"samples": 0, "mae": None, "rmse": None, "bias": None,
                "severe_event": None if severe_threshold is None else {"threshold": float(severe_threshold), "tp": 0, "fp": 0, "fn": 0, "precision": None, "recall": None}}
    error = p - y
    result = {"samples": int(len(y)), "mae": float(np.mean(np.abs(error))),
              "rmse": float(np.sqrt(np.mean(error ** 2))), "bias": float(np.mean(error)),
              "peak_absolute_error": float(abs(np.max(p) - np.max(y)))}
    if severe_threshold is not None:
        if not np.isfinite(severe_threshold):
            raise ValueError("severe_threshold must be finite")
        observed, forecast = y >= severe_threshold, p >= severe_threshold
        tp = int(np.sum(observed & forecast)); fp = int(np.sum(~observed & forecast)); fn = int(np.sum(observed & ~forecast))
        result["severe_event"] = {"threshold": float(severe_threshold), "definition": "actual or predicted concentration >= supplied threshold",
            "tp": tp, "fp": fp, "fn": fn,
            "precision": float(tp/(tp+fp)) if tp+fp else None,
            "recall": float(tp/(tp+fn)) if tp+fn else None}
    return result


def evaluate_by_horizon(frame: pd.DataFrame, *, actual_col: str = "actual",
                        predicted_col: str = "predicted", horizon_col: str = "horizon",
                        severe_threshold: float | None = None) -> dict[str, Any]:
    required = {actual_col, predicted_col, horizon_col}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    return {str(horizon): evaluate_predictions(group[actual_col], group[predicted_col], severe_threshold=severe_threshold)
            for horizon, group in frame.groupby(horizon_col, dropna=False, sort=True)}
