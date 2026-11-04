import pandas as pd
import pytest
import gzip
import hashlib
import json
from pathlib import Path

from airsource.station_context import (
    daily_station_means,
    load_station_history,
    coincident_elevation_hours,
    common_timestamp_matrix,
    common_timestamp_summary,
    same_hour_network_outliers,
    station_coverage,
)


def test_loader_converts_to_ist_and_rejects_duplicate_station_hours(tmp_path):
    path = tmp_path / "stations.csv"
    pd.DataFrame({
        "timestamp": ["2019-01-01T00:00:00Z", "2019-01-01T00:00:00Z"],
        "station": ["A", "A"],
        "pm25": [10, 12],
    }).to_csv(path, index=False)
    with pytest.raises(ValueError, match="duplicate"):
        load_station_history(path)


def test_coverage_and_daily_mean_keep_observed_support():
    frame = pd.DataFrame({
        "timestamp": pd.date_range("2019-01-01", periods=24, freq="h", tz="Asia/Kolkata"),
        "station": "A",
        "pm25": range(24),
    })
    coverage = station_coverage(frame).iloc[0]
    assert coverage["hourly_rows"] == 24
    assert coverage["valid_pm25"] == 24
    daily = daily_station_means(frame, minimum_hours=18)
    assert len(daily) == 1
    assert daily.iloc[0]["mean"] == pytest.approx(11.5)
    sparse = frame.copy()
    sparse.loc[sparse.index[:7], "pm25"] = float("nan")
    assert pd.isna(daily_station_means(sparse, minimum_hours=18).iloc[0]["mean"])


def test_station_alignment_preserves_missing_values_and_reports_overlap():
    t0 = pd.Timestamp("2019-01-01T00:00:00Z").tz_convert("Asia/Kolkata")
    t1 = t0 + pd.Timedelta(hours=1)
    frame = pd.DataFrame({
        "timestamp": [t0, t0, t0, t1, t1],
        "station": ["A", "B", "C", "A", "C"],
        "pm25": [10, 20, 30, 12, 32],
    })
    aligned = common_timestamp_matrix(frame)
    assert aligned.loc[t0, "B"] == 20
    assert pd.isna(aligned.loc[t1, "B"])
    assert common_timestamp_summary(frame) == {
        "timestamps": 2,
        "all_station_hours": 1,
        "at_least_four_station_hours": 0,
    }


def test_network_outlier_requires_multiple_stations_reporting():
    timestamp = pd.Timestamp("2019-01-01T00:00:00Z").tz_convert("Asia/Kolkata")
    frame = pd.DataFrame({
        "timestamp": [timestamp] * 6,
        "station": list("ABCDEF"),
        "pm25": [10, 11, 12, 13, 14, 100],
    })
    outliers = same_hour_network_outliers(frame)
    assert list(outliers["station"]) == ["F"]
    assert outliers.iloc[0]["stations_reporting"] == 6
    assert outliers.iloc[0]["pm25"] == 100
    flat_peers = frame.copy()
    flat_peers["pm25"] = [10, 10, 10, 10, 10, 20]
    assert list(same_hour_network_outliers(flat_peers)["station"]) == ["F"]


def test_coincident_elevations_require_a_majority_of_reporting_stations():
    timestamps = pd.date_range("2019-01-01", periods=10, freq="h", tz="Asia/Kolkata")
    rows = [{"timestamp": t, "station": station, "pm25": 1.0}
            for t in timestamps for station in list("ABCDEF")]
    rows[-1]["pm25"] = 10.0  # One station is relatively elevated; not a shared episode.
    assert coincident_elevation_hours(pd.DataFrame(rows)).empty
    for row in rows[-6:]:
        row["pm25"] = 10.0
    shared = coincident_elevation_hours(pd.DataFrame(rows))
    assert len(shared) == 1
    assert shared.iloc[0]["stations_above_own_p90"] == 6


def test_bundled_benchmark_has_six_labeled_historical_stations():
    from pathlib import Path

    dataset = Path(__file__).resolve().parents[1] / "data" / "benchmarks" / "delhi_multisite_hourly.csv.gz"
    history = load_station_history(dataset)
    assert set(history["station"].unique()) == {
        "AshokVihar", "DCStadium", "DwarkaSec8", "Najafgarh", "NehruNagar", "Okhla"
    }
    assert history["timestamp"].min().year == 2018
    assert history["timestamp"].max().year == 2019


def test_bundled_benchmark_matches_its_integrity_manifest():
    root = Path(__file__).resolve().parents[1]
    dataset = root / "data" / "benchmarks" / "delhi_multisite_hourly.csv.gz"
    manifest = json.loads((dataset.parent / "manifest.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(dataset.read_bytes()).hexdigest() == manifest["compressed_file_sha256"]
    with gzip.open(dataset, "rb") as source:
        original = source.read()
    assert hashlib.sha256(original).hexdigest() == manifest["prepared_csv_sha256"]
