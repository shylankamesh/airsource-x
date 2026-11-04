import pandas as pd
from airsource.ingestion import canonicalize_openaq, canonicalize_firms, validate_canonical
from airsource.store import ObservationStore


def test_openaq_canonicalization_preserves_units_and_class():
    frame=pd.DataFrame([{"location_id":12,"sensor_id":34,"parameter":"pm25","value":18.2,"unit":"µg/m³",
      "timestamp":"2026-11-04T08:00:00Z","latitude":28.6,"longitude":77.2}])
    out=canonicalize_openaq(frame,{"retrieved_at_utc":"2026-11-04T08:01:00Z"})
    assert out.iloc[0].data_class=="ground_sensor_measurement"
    assert out.iloc[0].unit=="µg/m³"
    assert pd.isna(out.iloc[0].available_at)
    assert validate_canonical(out)["rows"]==1


def test_firms_is_satellite_context_not_pm25():
    frame=pd.DataFrame([{"latitude":28.5,"longitude":77.2,"acq_date":"20261104","acq_time":800,"frp":4.2,"confidence":"nominal"}])
    out=canonicalize_firms(frame,{"retrieved_at_utc":"2026-11-04T08:10:00Z"})
    assert out.iloc[0].parameter=="fire_thermal_anomaly"
    assert out.iloc[0].data_class=="satellite_fire_detection"
    assert out.iloc[0].unit=="MW"
    assert pd.Timestamp(out.iloc[0].observed_at)==pd.Timestamp("2026-11-04T08:00:00Z")


def test_store_is_idempotent_and_keeps_ingestion_audit(tmp_path):
    frame=canonicalize_openaq(pd.DataFrame([{"location_id":12,"sensor_id":34,"parameter":"pm25","value":18.2,"unit":"µg/m³",
      "timestamp":"2026-11-04T08:00:00Z","latitude":28.6,"longitude":77.2}]),{"retrieved_at_utc":"2026-11-04T08:01:00Z"})
    store=ObservationStore(tmp_path/"obs.sqlite")
    first=store.ingest(frame,{"provider":"OpenAQ"})
    second=store.ingest(frame,{"provider":"OpenAQ"})
    assert first["rows_inserted"]==1
    assert second["rows_inserted"]==0 and second["rows_ignored"]==1
    assert len(store.observations())==1
    assert len(store.ingestion_history())==2
    assert store.source_health().iloc[0].rows_inserted==1
