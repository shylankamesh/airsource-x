"""Transparent public-impact screening briefs; never official AQI or health advice."""
from __future__ import annotations
import pandas as pd


def build_screening_brief(observations: pd.DataFrame, *, review_threshold_ug_m3: float = 75.0) -> dict:
    required = {"timestamp", "station", "pm25"}
    if not required.issubset(observations.columns):
        raise ValueError(f"Missing columns: {sorted(required - set(observations.columns))}")
    if review_threshold_ug_m3 <= 0:
        raise ValueError("Review threshold must be positive")
    data = observations.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce", utc=True)
    data["pm25"] = pd.to_numeric(data["pm25"], errors="coerce")
    data = data.dropna(subset=["timestamp", "station", "pm25"])
    data = data[data.pm25 >= 0].sort_values("timestamp")
    rows=[]
    for station, group in data.groupby("station", sort=True):
        latest=group.iloc[-1]
        value=float(latest.pm25)
        rows.append({"station":str(station),"observed_at":latest.timestamp,
          "pm25_ug_m3":value,"screening_status":"REVIEW" if value >= review_threshold_ug_m3 else "BELOW_USER_THRESHOLD",
          "recommended_process":"Verify monitor QA and compare nearby stations; communicate only with timestamp and source caveats." if value >= review_threshold_ug_m3 else "Continue routine monitoring and check data freshness."})
    result=pd.DataFrame(rows)
    return {"threshold_ug_m3":float(review_threshold_ug_m3),"threshold_type":"User-defined screening threshold; not an official AQI or health threshold",
      "station_count":len(result),"stations_for_review":int((result.screening_status=="REVIEW").sum()) if len(result) else 0,
      "latest_by_station":result,"limitations":["A latest reading is not a forecast or an exposure assessment.","Uploaded and provider data may have different measurement status; inspect provenance.","This brief does not identify sources, prescribe health actions, or replace official advisories."]}
