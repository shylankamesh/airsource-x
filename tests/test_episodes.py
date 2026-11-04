import pandas as pd
from airsource.episodes import detect_station_episodes, group_network_episodes, wind_quality_summary


def _series(station, values, start="2024-01-01 00:00"):
    ts = pd.date_range(start, periods=len(values), freq="h", tz="UTC")
    return pd.DataFrame({"timestamp": ts, "station": station, "pm25": values})


def test_detects_persistent_rise_using_prior_baseline():
    base = [20.0] * 30
    values = base + [70.0, 85.0, 90.0, 80.0] + [25.0] * 4
    events = detect_station_episodes(pd.concat([_series("A", values)]))
    assert len(events) == 1
    assert events.iloc[0]["station"] == "A"
    assert events.iloc[0]["peak_pm25_ug_m3"] == 90.0
    assert events.iloc[0]["duration_hours"] >= 3


def test_single_spike_is_not_an_episode():
    values = [20.0] * 30 + [150.0] + [20.0] * 4
    events = detect_station_episodes(_series("A", values))
    assert events.empty


def test_network_grouping_reports_onset_order_without_causal_claim():
    a = _series("A", [20.0] * 30 + [80.0, 90.0, 85.0])
    b = _series("B", [20.0] * 31 + [85.0, 95.0, 88.0])
    events = detect_station_episodes(pd.concat([a, b]), min_duration_hours=2)
    network = group_network_episodes(events, onset_link_hours=3)
    assert len(network) == 1
    assert network.iloc[0]["lead_station"] == "A"
    assert network.iloc[0]["last_station"] == "B"
    assert "not source attribution" in network.iloc[0]["interpretation"]


def test_missing_wind_columns_are_not_usable():
    result = wind_quality_summary(pd.DataFrame({"pm25": [20, 30]}))
    assert not result["available"]
    assert not result["usable_for_context"]


def test_implausible_wind_is_blocked_not_repaired():
    frame = pd.DataFrame({
        "wind_speed_kmh": [3, 4, 5, 120, 170],
        "wind_direction_deg": [0, 90, 180, 270, 360],
    })
    result = wind_quality_summary(frame)
    assert result["available"]
    assert not result["usable_for_context"]
    assert result["plausible_rows"] == 3


def test_empty_or_invalid_input_is_handled():
    events = detect_station_episodes(pd.DataFrame(columns=["timestamp", "station", "pm25"]))
    assert events.empty
