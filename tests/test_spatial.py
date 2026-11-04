import pandas as pd
import pytest
from airsource.spatial import haversine_km, attach_station_metadata, synchronized_station_snapshot, pairwise_spatial_statistics


def registry():
    return pd.DataFrame([
        {"station_id":"A","station_name":"Alpha","latitude":28.6,"longitude":77.2,"site_type":"unknown",
         "valid_from":"2020-01-01","valid_to":"","metadata_source":"published source","coordinate_quality":"rounded"},
        {"station_id":"B","station_name":"Beta","latitude":28.7,"longitude":77.3,"site_type":"unknown",
         "valid_from":"2020-01-01","valid_to":"","metadata_source":"published source","coordinate_quality":"rounded"},
    ])


def test_haversine_distance_is_symmetric_and_zero_at_same_point():
    assert haversine_km(28.6,77.2,28.6,77.2) == pytest.approx(0)
    assert haversine_km(28.6,77.2,28.7,77.3) == pytest.approx(haversine_km(28.7,77.3,28.6,77.2))


def test_metadata_join_and_common_timestamp_snapshot():
    obs = pd.DataFrame({"station":["A","B","A","B"],"timestamp":pd.to_datetime([
        "2025-01-01T00:00Z","2025-01-01T00:00Z","2025-01-01T01:00Z","2025-01-01T01:00Z"]),
        "pm25":[10,20,15,25]})
    joined = attach_station_metadata(obs,registry())
    assert len(joined) == 4
    snap = synchronized_station_snapshot(obs,registry())
    assert set(snap.station) == {"A","B"}
    assert snap.pm25.tolist() == [15,25]


def test_pairwise_correlation_respects_overlap_gate():
    times = list(pd.date_range("2025-01-01",periods=4,freq="h",tz="UTC"))
    obs = pd.DataFrame({"station":["A"]*4+["B"]*4,
        "timestamp":times+times,
        "pm25":[1,2,3,4,2,4,6,8]})
    stats = pairwise_spatial_statistics(obs,registry(),min_overlap=4)
    assert stats.iloc[0].overlap_hours == 4
    assert stats.iloc[0].pearson_r == pytest.approx(1.0)


def test_unknown_station_is_not_assigned_coordinates():
    obs = pd.DataFrame({"station":["C"],"timestamp":["2025-01-01T00:00Z"],"pm25":[10]})
    assert attach_station_metadata(obs,registry()).empty
