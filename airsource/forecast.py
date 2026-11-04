"""Leakage-aware two-horizon forecasting and chronological evaluation."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingRegressor, IsolationForest
from sklearn.metrics import mean_absolute_error, mean_squared_error

BASE_FEATURES = ["pm25", "pm10", "no2", "co", "so2", "o3", "temperature_c", "humidity_pct",
                 "wind_speed_kmh", "wind_direction_deg", "precipitation_mm",
                 "barometric_pressure_mmhg", "solar_radiation_w_m2"]


def feature_frame(station_frame: pd.DataFrame) -> pd.DataFrame:
    """Build issue-time-safe features; no future observations enter X."""
    data = station_frame.sort_values("timestamp").set_index("timestamp").copy()
    numeric = [c for c in BASE_FEATURES if c in data]
    if "pm25" not in numeric:
        raise ValueError("PM2.5 is required for forecasting.")
    x = pd.DataFrame(index=data.index)
    for col in numeric:
        x[f"{col}_now"] = pd.to_numeric(data[col], errors="coerce")
        if col in {"pm25", "pm10", "no2", "co"}:
            for lag in (1, 3, 6, 12, 24, 48, 168):
                x[f"{col}_lag_{lag}h"] = data[col].shift(lag)
            for window in (3, 6, 12, 24, 168):
                x[f"{col}_mean_{window}h"] = data[col].rolling(window, min_periods=window).mean()
            for window in (24, 168):
                x[f"{col}_std_{window}h"] = data[col].rolling(window, min_periods=window).std()
    if "wind_direction_deg" in data:
        radians = np.deg2rad(data["wind_direction_deg"])
        x["wind_sin"] = np.sin(radians)
        x["wind_cos"] = np.cos(radians)
    local = data.index
    for name, angle in (("hour", 2 * np.pi * local.hour / 24),
                        ("weekday", 2 * np.pi * local.dayofweek / 7),
                        ("year_day", 2 * np.pi * local.dayofyear / 365.25)):
        x[f"{name}_sin"] = np.sin(angle)
        x[f"{name}_cos"] = np.cos(angle)
    # Drop features with no information, but preserve sparse numeric features.
    return x.replace([np.inf, -np.inf], np.nan)


def future_targets(station_frame: pd.DataFrame) -> pd.DataFrame:
    """Use complete, consecutive hourly windows after each issue time."""
    data = station_frame.sort_values("timestamp").set_index("timestamp")
    s = pd.to_numeric(data["pm25"], errors="coerce")
    # With hourly rows, these windows represent [t+1,t+24] and [t+25,t+48].
    next_24 = s.shift(-1).rolling(24, min_periods=24).mean().shift(-23)
    next_24_48 = s.shift(-25).rolling(24, min_periods=24).mean().shift(-23)
    return pd.DataFrame({"target_0_24h": next_24, "target_24_48h": next_24_48}, index=data.index)


def _model_candidates() -> list[tuple[str, Any]]:
    try:
        from lightgbm import LGBMRegressor
        common = {"max_depth": -1, "subsample": 0.9, "colsample_bytree": 0.9,
                  "random_state": 42, "verbosity": -1, "n_jobs": 1}
        candidates = [
            ("LightGBM leaves=7", LGBMRegressor(**common, n_estimators=400, learning_rate=0.03,
                                                num_leaves=7, min_child_samples=20, reg_lambda=2.0)),
            ("LightGBM leaves=15", LGBMRegressor(**common, n_estimators=400, learning_rate=0.03,
                                                 num_leaves=15, min_child_samples=30, reg_lambda=2.0)),
            ("LightGBM leaves=31", LGBMRegressor(**common, n_estimators=500, learning_rate=0.025,
                                                 num_leaves=31, min_child_samples=40, reg_lambda=3.0)),
        ]
    except (ImportError, OSError):
        candidates = []
    candidates.append(("HistGradientBoosting", HistGradientBoostingRegressor(
        max_iter=250, learning_rate=0.055, max_leaf_nodes=15,
        l2_regularization=2.0, random_state=42)))
    return candidates


def _metrics(actual: pd.Series, predicted: np.ndarray) -> dict[str, float | int]:
    mask = actual.notna() & np.isfinite(predicted)
    y = actual.loc[mask].astype(float)
    p = predicted[mask]
    if not len(y):
        return {"samples": 0, "mae": math.nan, "rmse": math.nan, "bias": math.nan}
    return {"samples": int(len(y)), "mae": float(mean_absolute_error(y, p)),
            "rmse": float(mean_squared_error(y, p) ** 0.5), "bias": float(np.mean(p - y))}


def _seasonal_predictions(history_y: pd.Series, issue_times: pd.DatetimeIndex,
                         fallback_train_y: pd.Series | None = None) -> np.ndarray:
    history = history_y.dropna()
    train = (fallback_train_y.dropna() if fallback_train_y is not None else history)
    if train.empty or train.index.tz_localize(None).to_period("W").nunique() < 4:
        return np.full(len(issue_times), np.nan)
    keys = pd.Series(list(zip(train.index.dayofweek, train.index.hour)), index=train.index)
    means = train.groupby(keys).mean()
    # Same-horizon target from the prior week is observable by issue time and
    # follows seasonal changes better than a long-run hour-of-week average.
    return np.array([history.get(t - pd.Timedelta(days=7),
                               means.get((t.dayofweek, t.hour), train.mean()))
                     for t in issue_times], dtype=float)


def evaluate_and_forecast(station_frame: pd.DataFrame, min_samples: int = 180) -> dict[str, Any]:
    """Purged walk-forward model selection with a later temporal holdout."""
    data = station_frame.sort_values("timestamp").drop_duplicates("timestamp").set_index("timestamp")
    x = feature_frame(data.reset_index())
    targets = future_targets(data.reset_index())
    x = x.loc[targets.index]
    x = x.loc[:, x.notna().any(axis=0)]
    issues = x.index
    if len(issues) < min_samples:
        raise ValueError(f"Need at least {min_samples} hourly rows for a useful chronological evaluation; found {len(issues)}.")
    cut_idx = int(len(issues) * 0.8)
    test_start = issues[cut_idx]
    train_end = test_start - pd.Timedelta(hours=48)
    train_mask = issues < train_end
    test_mask = issues >= test_start
    if int(train_mask.sum()) < 100 or int(test_mask.sum()) < 25:
        raise ValueError("Not enough rows remain after the 48-hour leakage purge. Add a longer hourly history.")
    current = pd.to_numeric(data["pm25"], errors="coerce")
    future_row = x.loc[current.notna()].iloc[[-1]]
    if future_row.empty:
        raise ValueError("The latest timestamp has no usable current PM2.5 value.")
    results: dict[str, Any] = {"model_name": "Validation-selected per forecast horizon",
                               "features": list(x.columns), "test_start": test_start,
                               "train_end": train_end, "metrics": {}, "forecast": {},
                               "forecast_intervals": {}, "uncertainty": {}, "models": {},
                               "selection": {}, "selected_models": {}}
    for target_name in ("target_0_24h", "target_24_48h"):
        candidates = _model_candidates()
        y = targets[target_name]
        usable_train = train_mask & y.notna() & current.notna()
        usable_test = test_mask & y.notna() & current.notna()
        if int(usable_train.sum()) < 80 or int(usable_test.sum()) < 20:
            results["metrics"][target_name] = {"error": "Insufficient complete target windows after purging."}
            continue
        train_issues = issues[train_mask]
        calibration_start = train_issues[int(len(train_issues) * 0.8)]
        calibration_train = ((issues < calibration_start - pd.Timedelta(hours=48))
                             & train_mask & y.notna() & current.notna())
        calibration_valid = ((issues >= calibration_start) & train_mask & y.notna() & current.notna())
        if int(calibration_train.sum()) < 100 or int(calibration_valid.sum()) < 20:
            raise ValueError("Not enough historical rows for purged model selection and interval calibration.")
        fold_bounds = [(int(len(train_issues) * fraction),
                        int(len(train_issues) * (fraction + 0.1)))
                       for fraction in (0.4, 0.5, 0.6)]
        validation_scores = []
        for candidate_name, candidate in candidates:
            fold_scores = []
            for fold_number, (start_idx, end_idx) in enumerate(fold_bounds, start=1):
                validation_start = train_issues[start_idx]
                validation_end = train_issues[min(end_idx, len(train_issues) - 1)]
                fit_mask = ((issues < validation_start - pd.Timedelta(hours=48))
                            & train_mask & y.notna() & current.notna())
                valid_mask = ((issues >= validation_start) & (issues < validation_end)
                              & train_mask & y.notna() & current.notna())
                if int(fit_mask.sum()) < 100 or int(valid_mask.sum()) < 20:
                    continue
                selector = clone(candidate)
                selector.fit(x.loc[fit_mask], y.loc[fit_mask])
                validation_prediction = np.maximum(selector.predict(x.loc[valid_mask]), 0.0)
                fold_scores.append({"fold": fold_number,
                                    "mae": _metrics(y.loc[valid_mask], validation_prediction)["mae"],
                                    "samples": int(valid_mask.sum()),
                                    "train_end": (validation_start - pd.Timedelta(hours=48)).isoformat(),
                                    "validation_start": validation_start.isoformat(),
                                    "validation_end": validation_end.isoformat()})
            if len(fold_scores) < 2:
                raise ValueError("Not enough historical rows for at least two purged walk-forward validation folds.")
            validation_scores.append({"model": candidate_name,
                                      "mae": float(np.mean([row["mae"] for row in fold_scores])),
                                      "samples": int(sum(row["samples"] for row in fold_scores)),
                                      "folds": fold_scores})
        chosen = min(validation_scores, key=lambda row: row["mae"])
        selected_name = chosen["model"]
        template = next(item for name, item in candidates if name == selected_name)
        calibrator = clone(template)
        calibrator.fit(x.loc[calibration_train], y.loc[calibration_train])
        calibration_prediction = np.maximum(calibrator.predict(x.loc[calibration_valid]), 0.0)
        calibration_error = np.abs(y.loc[calibration_valid].to_numpy() - calibration_prediction)
        rank = min(int(np.ceil(0.90 * (len(calibration_error) + 1))), len(calibration_error))
        interval_radius = float(np.sort(calibration_error)[rank - 1])
        model = clone(template)
        model.fit(x.loc[usable_train], y.loc[usable_train])
        test_pred = np.maximum(model.predict(x.loc[usable_test]), 0.0)
        idx = x.index[usable_test]
        test_actual = y.loc[usable_test].to_numpy()
        test_lower = np.maximum(0.0, test_pred - interval_radius)
        test_upper = test_pred + interval_radius
        metric_set = {"model": _metrics(y.loc[usable_test], test_pred),
                      "persistence": _metrics(y.loc[usable_test], current.loc[usable_test].to_numpy()),
                      "seasonal": _metrics(y.loc[usable_test], _seasonal_predictions(y, idx, y.loc[usable_train]))}
        metric_set["selected_model"] = selected_name
        residual = y.loc[usable_test].to_numpy() - test_pred
        metric_set["residuals"] = residual
        results["selection"][target_name] = {"method": "mean MAE across purged expanding-window chronological folds",
                                             "validation_folds": len(chosen["folds"]),
                                             "calibration_start": calibration_start,
                                             "candidates": validation_scores,
                                             "selected": selected_name}
        results["uncertainty"][target_name] = {
            "method": "90% split-conformal absolute-residual interval; calibration block precedes test block",
            "calibration_samples": int(len(calibration_error)),
            "calibration_radius_ug_m3": interval_radius,
            "test_coverage": float(np.mean((test_actual >= test_lower) & (test_actual <= test_upper))),
            "mean_test_interval_width_ug_m3": float(np.mean(test_upper - test_lower)),
        }
        results.setdefault("explain_data", {})[target_name] = {
            "row": future_row.copy(),
            "background": x.loc[usable_train].sample(min(20, int(usable_train.sum())), random_state=42).copy(),
        }
        final_model = clone(template)
        final_model.fit(x.loc[y.notna() & current.notna()], y.loc[y.notna() & current.notna()])
        prediction = float(max(0.0, final_model.predict(future_row)[0]))
        results["metrics"][target_name] = metric_set
        results["forecast"][target_name] = prediction
        results["models"][target_name] = final_model
        results["selected_models"][target_name] = selected_name
        results["forecast_intervals"][target_name] = [max(0.0, prediction - interval_radius),
                                                      prediction + interval_radius]
    results["latest_timestamp"] = future_row.index[-1]
    results["latest_pm25"] = float(current.loc[future_row.index[-1]])
    return results


def shap_explanation(model: Any, row: pd.DataFrame, background: pd.DataFrame) -> pd.DataFrame:
    """Compute a local SHAP explanation; raise a readable error if unsupported."""
    import shap

    # Use model-agnostic permutation SHAP to keep the explanation available for
    # both LightGBM and the documented sklearn fallback.
    explainer = shap.Explainer(model.predict, background)
    explanation = explainer(row, max_evals=max(2 * len(row.columns) + 1, 101))
    return pd.DataFrame({"feature": row.columns, "value": row.iloc[0].to_numpy(),
                         "shap_value": np.asarray(explanation.values).reshape(-1),
                         "base_value": float(np.asarray(explanation.base_values).reshape(-1)[0])})


def detect_anomalies(station_frame: pd.DataFrame) -> pd.DataFrame:
    """Flag unusual multivariate rows; an anomaly is not a confirmed incident."""
    data = station_frame.sort_values("timestamp").copy()
    candidates = [c for c in ("pm25", "pm10", "no2", "co", "temperature_c", "humidity_pct", "wind_speed_kmh")
                  if c in data and pd.to_numeric(data[c], errors="coerce").notna().any()]
    matrix = data[candidates].apply(pd.to_numeric, errors="coerce")
    usable = matrix.notna().sum(axis=1) >= 2
    matrix = matrix.loc[usable]
    if len(matrix) < 40:
        raise ValueError("At least 40 rows with two or more pollutant/weather variables are required for anomaly screening.")
    matrix = matrix.fillna(matrix.median())
    detector = IsolationForest(n_estimators=200, contamination="auto", random_state=42)
    detector.fit(matrix)
    scored = data.loc[usable].copy()
    scored["anomaly_score"] = detector.decision_function(matrix)
    scored["is_unusual"] = detector.predict(matrix) == -1
    scored["features_used"] = ", ".join(candidates)
    return scored.sort_values("timestamp")
