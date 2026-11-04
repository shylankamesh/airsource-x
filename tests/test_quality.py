import pandas as pd
from airsource.quality import audit_observations


def test_quality_report_counts_duplicates_missing_and_gaps():
    frame = pd.DataFrame({
        "station": ["A", "A", "A"],
        "timestamp": ["2024-01-01T00:00:00Z", "2024-01-01T00:00:00Z", "2024-01-01T03:00:00Z"],
        "pm25": [10.0, None, 15.0], "humidity_pct": [50, 50, 150],
    })
    report = audit_observations(frame, now=pd.Timestamp("2024-01-01T04:00:00Z"))
    assert report["duplicate_station_timestamps"] == 1
    assert report["missing_by_column"]["pm25"] == 1
    assert report["range_violations"]["humidity_pct"] == 1
    assert report["gap_count_by_station"]["A"] == 1
    assert report["latest_data_age_hours"] == 1.0


def test_quality_report_does_not_modify_input():
    frame = pd.DataFrame({"station": ["A"], "timestamp": ["2024-01-01"], "pm25": [5]})
    original = frame.copy(deep=True)
    audit_observations(frame, now=pd.Timestamp("2024-01-02T00:00:00Z"))
    pd.testing.assert_frame_equal(frame, original)
