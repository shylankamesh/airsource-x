import pandas as pd
from airsource.station_registry import validate_station_registry


def test_blank_coordinates_warn_but_are_not_fabricated():
    frame = pd.DataFrame([{"station_id":"A","station_name":"A","latitude":None,"longitude":None,
        "site_type":"unknown","valid_from":"2020-01-01","valid_to":None,
        "metadata_source":"pending","coordinate_quality":"unverified"}])
    result = validate_station_registry(frame)
    assert result["valid"] is True
    assert any("latitude is missing" in w for w in result["warnings"])


def test_invalid_coordinate_fails():
    frame = pd.DataFrame([{"station_id":"A","station_name":"A","latitude":120,"longitude":0,
        "site_type":"unknown","valid_from":"2020-01-01","metadata_source":"x","coordinate_quality":"x"}])
    assert validate_station_registry(frame)["valid"] is False
