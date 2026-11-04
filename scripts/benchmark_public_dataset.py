"""Run AirSource's leakage-aware holdout benchmark on each bundled station."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from airsource.forecast import evaluate_and_forecast

DATA_PATH = ROOT / "data" / "processed" / "delhi_multisite_hourly.csv"
JSON_PATH = ROOT / "reports" / "public_benchmark.json"
CSV_PATH = ROOT / "reports" / "public_benchmark.csv"


def clean(value):
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items() if key != "residuals"}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, float) and (pd.isna(value) or value in (float("inf"), float("-inf"))):
        return None
    return value


def main() -> None:
    data = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    records = []
    diagnostics = {}
    stations = sorted(data["station"].dropna().unique())
    for station in stations:
        station_data = data.loc[data["station"] == station].copy()
        print(f"Training and evaluating {station} ({len(station_data):,} rows)...", flush=True)
        result = evaluate_and_forecast(station_data)
        for horizon, metrics in result["metrics"].items():
            if "error" in metrics:
                records.append({"station": station, "horizon": horizon, "error": metrics["error"]})
                continue
            for model_name in ("model", "persistence", "seasonal"):
                score = metrics[model_name]
                row = {"station": station, "horizon": horizon,
                       "model": metrics["selected_model"] if model_name == "model" else
                                "Weekly same-horizon naive" if model_name == "seasonal" else model_name,
                       **score}
                if model_name == "model":
                    interval = result["uncertainty"][horizon]
                    row.update({"interval_calibration_samples": interval["calibration_samples"],
                                "interval_nominal_level": 0.90,
                                "interval_test_coverage": interval["test_coverage"],
                                "mean_test_interval_width_ug_m3": interval["mean_test_interval_width_ug_m3"]})
                records.append(row)
        diagnostics[station] = {"selected_models": result["selected_models"],
                                "selection": result["selection"],
                                "uncertainty": result["uncertainty"],
                                "train_end": result["train_end"],
                                "test_start": result["test_start"]}
        print(f"Finished {station}; selected={result['selected_models']}", flush=True)

    frame = pd.DataFrame(records)
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset": {
            "citation": "Sonawani, S.; Patil, K. (2021), Delhi Multi-Site Air-Quality Data Set, V1, Mendeley Data, doi:10.17632/bzhzr9b64v.1",
            "license": "CC BY 4.0",
            "observations": int(len(data)),
            "stations": stations,
            "first_timestamp": data["timestamp"].min().isoformat(),
            "last_timestamp": data["timestamp"].max().isoformat(),
            "warning": "Curated historical dataset (2018-06 to 2019-10); not a live feed. Results are temporal holdout results for these six stations and this period, not evidence of present-day or geographic transfer.",
        },
        "protocol": {
            "split": "Per-station chronological 80/20 holdout; candidate selection averages three expanding-window validation folds, each with 48-hour label purges; separate calibration block; 48-hour purge before test boundary.",
            "features": "Issue-time observations and trailing history only.",
            "targets": "Mean PM2.5 at t+1..t+24h and t+25..t+48h; complete hourly windows required.",
            "metrics": "MAE, RMSE, and prediction-minus-observation bias on identical valid test issue times; 90% split-conformal intervals include calibration and test coverage/width.",
        },
        "station_diagnostics": diagnostics,
        "runs": records,
    }
    JSON_PATH.write_text(json.dumps(clean(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    frame.to_csv(CSV_PATH, index=False)
    print(frame.to_string(index=False))
    print(f"Wrote {JSON_PATH.relative_to(ROOT)} and {CSV_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
