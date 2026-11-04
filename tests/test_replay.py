import pandas as pd
import pytest
from airsource.replay import as_of_replay


def test_as_of_replay_excludes_late_and_impossible_records():
    frame = pd.DataFrame({
        "observed_at":["2025-01-01T00:00:00Z","2025-01-01T02:00:00Z","2025-01-01T03:00:00Z"],
        "available_at":["2025-01-01T00:10:00Z","2025-01-01T01:00:00Z","2025-01-01T04:00:00Z"],
        "value":[1,2,3]})
    result = as_of_replay(frame, "2025-01-01T03:00:00Z")
    assert result["value"].tolist() == [1]


def test_replay_requires_availability_timestamp():
    with pytest.raises(ValueError):
        as_of_replay(pd.DataFrame({"observed_at":["2025-01-01"]}), "2025-01-02")
