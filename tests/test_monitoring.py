import pandas as pd
from airsource.monitoring import source_freshness


def test_source_freshness_states():
    now = pd.Timestamp("2024-01-01T12:00:00Z")
    assert source_freshness(source="x", last_successful_retrieval="2024-01-01T11:00:00Z", expected_interval_hours=2, now=now)["status"] == "FRESH"
    assert source_freshness(source="x", last_successful_retrieval="2024-01-01T09:00:00Z", expected_interval_hours=2, now=now)["status"] == "STALE"
    assert source_freshness(source="x", last_successful_retrieval=None, expected_interval_hours=2, now=now)["status"] == "UNAVAILABLE"
