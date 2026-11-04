import pandas as pd
from airsource.context_matching import haversine_km, match_fire_context


def test_distance_and_space_time_match_is_context_only():
    assert 110 < haversine_km(0,0,0,1) < 112
    events=pd.DataFrame([{"event_id":"E1","timestamp":"2026-11-04T08:00:00Z","latitude":28.6,"longitude":77.2}])
    detections=pd.DataFrame([{"observed_at":"2026-11-04T09:00:00Z","latitude":28.61,"longitude":77.2,"source":"NASA FIRMS","data_class":"satellite_fire_detection"}])
    out=match_fire_context(events,detections,radius_km=5,window_hours=3)
    assert len(out)==1
    assert "not evidence of causation" in out.iloc[0].interpretation


def test_match_excludes_outside_time_window():
    events=pd.DataFrame([{"event_id":"E1","timestamp":"2026-11-04T08:00:00Z","latitude":28.6,"longitude":77.2}])
    detections=pd.DataFrame([{"observed_at":"2026-11-05T08:00:00Z","latitude":28.6,"longitude":77.2}])
    assert match_fire_context(events,detections,window_hours=6).empty
