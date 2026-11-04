"""Train final per-station/horizon models and save reproducible model artifacts."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
import sys

import joblib
import pandas as pd
import sklearn
from sklearn.base import clone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from airsource.forecast import _model_candidates, feature_frame, future_targets

DATA_PATH = ROOT / "data" / "processed" / "delhi_multisite_hourly.csv"
BENCHMARK_JSON = ROOT / "reports" / "public_benchmark.json"
BENCHMARK_CSV = ROOT / "reports" / "public_benchmark.csv"
OUT = ROOT / "models"


def main() -> None:
    data = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    benchmark = json.loads(BENCHMARK_JSON.read_text(encoding="utf-8"))
    scores = pd.read_csv(BENCHMARK_CSV)
    candidate_map = dict(_model_candidates())
    manifest = {
        "project": "AirSource X",
        "dataset": "Delhi Multi-Site Air-Quality Data Set V1",
        "dataset_doi": "10.17632/bzhzr9b64v.1",
        "dataset_license": "CC BY 4.0",
        "dataset_sha256": hashlib.sha256(
            DATA_PATH.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
        "runtime_versions": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "training": "Per-station and per-horizon validation-selected model, refit on all rows with complete historical targets.",
        "features": "Issue-time and trailing-history features from airsource.forecast.feature_frame.",
        "warning": "Historical research artifacts trained on 2018-06 through 2019-10 data. Not current monitoring or a validated operational warning model.",
        "artifacts": [],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    stations = sorted(data["station"].dropna().unique())
    for station in stations:
        frame = data.loc[data["station"] == station].sort_values("timestamp").copy()
        print(f"Refitting selected models for {station} ({len(frame):,} rows)", flush=True)
        x = feature_frame(frame)
        x = x.loc[:, x.notna().any(axis=0)]
        targets = future_targets(frame)
        current = pd.to_numeric(frame.set_index("timestamp")["pm25"], errors="coerce")
        station_diagnostics = benchmark["station_diagnostics"][station]
        for horizon, selected_name in station_diagnostics["selected_models"].items():
            y = targets[horizon]
            usable = y.notna() & current.notna()
            model = clone(candidate_map[selected_name])
            model.fit(x.loc[usable], y.loc[usable])
            latest = x.loc[current.notna()].iloc[[-1]]
            prediction = float(max(0.0, model.predict(latest)[0]))
            radius = station_diagnostics["uncertainty"][horizon]["calibration_radius_ug_m3"]
            path = OUT / f"{station.lower()}_{horizon}.joblib"
            row = scores.loc[(scores["station"] == station)
                             & (scores["horizon"] == horizon)
                             & (scores["model"] == selected_name)].iloc[0]
            metrics = {key: (int(row[key]) if key == "samples" else float(row[key]))
                       for key in ("samples", "mae", "rmse", "bias")}
            bundle = {
                "model": model,
                "station": station,
                "horizon": horizon,
                "selected_model": selected_name,
                "feature_names": list(x.columns),
                "trained_through": latest.index[-1].isoformat(),
                "forecast_pm25_ug_m3": prediction,
                "forecast_interval_90": [max(0.0, prediction - radius), prediction + radius],
                "interval_caveat": "Radius calibrated on a separate historical block; coverage can shift over time.",
                "holdout_metrics": metrics,
                "selection_diagnostics": station_diagnostics["selection"][horizon],
            }
            joblib.dump(bundle, path, compress=3)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest["artifacts"].append({
                "file": path.name,
                "sha256": digest,
                "station": station,
                "horizon": horizon,
                "model": bundle["selected_model"],
                "holdout_mae_ug_m3": bundle["holdout_metrics"]["mae"],
                "rows": int(frame.shape[0]),
            })
            print(f"  saved {path.name} ({digest[:12]})", flush=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Saved {len(manifest['artifacts'])} station/horizon model artifacts in {OUT}")


if __name__ == "__main__":
    main()
