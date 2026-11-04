import pandas as pd
import pytest

from airsource.station_context import (
    daily_station_means,
    load_station_history,
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


def test_bundled_benchmark_has_six_labeled_historical_stations():
    from pathlib import Path

    dataset = Path(__file__).resolve().parents[1] / "data" / "benchmarks" / "delhi_multisite_hourly.csv.gz"
    history = load_station_history(dataset)
    assert set(history["station"].unique()) == {
        "AshokVihar", "DCStadium", "DwarkaSec8", "Najafgarh", "NehruNagar", "Okhla"
    }
    assert history["timestamp"].min().year == 2018
    assert history["timestamp"].max().year == 2019
