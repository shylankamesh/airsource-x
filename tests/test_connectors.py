import pandas as pd
import pytest
from airsource import connectors


class _Response:
    def __init__(self, payload=None, text=None, url="https://example.test/data"):
        self._payload = payload or {}
        self.text = text or ""
        self.url = url
    def raise_for_status(self):
        return None
    def json(self):
        return self._payload


def test_openaq_latest_normalises_sensor_measurements(monkeypatch):
    monkeypatch.setattr(connectors, "_get_json", lambda *a, **k: {
        "results": [{
            "locationsId": 10, "sensorsId": 20, "value": 12.5,
            "parameter": {"name": "pm25", "units": "µg/m³"},
            "datetime": {"utc": "2026-11-04T08:00:00Z"},
            "coordinates": {"latitude": 28.6, "longitude": 77.2},
        }]
    })
    frame, meta = connectors.fetch_openaq_location_latest(10, api_key="test")
    assert frame.iloc[0]["value"] == 12.5
    assert frame.iloc[0]["timestamp"] == pd.Timestamp("2026-11-04T08:00:00Z")
    assert meta["data_class"].startswith("Sensor measurements")


def test_openaq_requires_key(monkeypatch):
    monkeypatch.delenv("OPENAQ_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API key"):
        connectors.fetch_openaq_location_latest(10)


def test_ogd_resource_id_is_required(monkeypatch):
    monkeypatch.setenv("DATA_GOV_IN_API_KEY", "dummy")
    with pytest.raises(ValueError, match="resource ID"):
        connectors.fetch_india_ogd_resource("")


def test_ogd_fetch_uses_explicit_resource_and_metadata(monkeypatch):
    monkeypatch.setattr(connectors, "_get_json", lambda *a, **k: {"records": [{"station": "X"}]})
    frame, meta = connectors.fetch_india_ogd_resource("resource-123", api_key="dummy")
    assert len(frame) == 1
    assert meta["resource_id"] == "resource-123"


def test_firms_requires_key(monkeypatch):
    monkeypatch.delenv("NASA_FIRMS_MAP_KEY", raising=False)
    with pytest.raises(ValueError, match="MAP_KEY"):
        connectors.fetch_firms_area(76, 28, 78, 30)


def test_firms_validates_bbox_before_request(monkeypatch):
    with pytest.raises(ValueError, match="bounding box"):
        connectors.fetch_firms_area(78, 28, 76, 30, map_key="dummy")


def test_catalogue_marks_satellites_not_ingested():
    rows = connectors.external_source_catalogue()
    status = {r["source"]: r["status"] for r in rows}
    assert status["Sentinel-5P TROPOMI"] == "catalogued_not_ingested"
    assert status["NASA MAIAC MCD19A2"] == "catalogued_not_ingested"
