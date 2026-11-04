import pandas as pd
import pytest
from airsource.decision_support import build_screening_brief


def test_brief_uses_latest_station_values_and_user_threshold():
    frame=pd.DataFrame({"timestamp":["2024-01-01T00:00:00Z","2024-01-01T01:00:00Z","2024-01-01T01:00:00Z"],
      "station":["A","A","B"],"pm25":[20,80,40]})
    out=build_screening_brief(frame,review_threshold_ug_m3=75)
    assert out["station_count"]==2
    assert out["stations_for_review"]==1
    assert out["threshold_type"].startswith("User-defined")


def test_brief_rejects_nonpositive_threshold():
    with pytest.raises(ValueError): build_screening_brief(pd.DataFrame(columns=["timestamp","station","pm25"]),review_threshold_ug_m3=0)
