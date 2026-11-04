"""Conservative space-time matching for contextual detections; not causal attribution."""
from __future__ import annotations
import math
import pandas as pd


def haversine_km(lat1, lon1, lat2, lon2):
    vals=[lat1,lon1,lat2,lon2]
    if any(pd.isna(v) for v in vals): return float("nan")
    if not (-90<=float(lat1)<=90 and -90<=float(lat2)<=90 and -180<=float(lon1)<=180 and -180<=float(lon2)<=180):
        raise ValueError("Coordinates out of range")
    p1,p2=math.radians(float(lat1)),math.radians(float(lat2))
    dp=math.radians(float(lat2)-float(lat1)); dl=math.radians(float(lon2)-float(lon1))
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 6371*2*math.asin(math.sqrt(a))


def match_fire_context(events: pd.DataFrame, detections: pd.DataFrame, *, radius_km: float=25, window_hours: float=6) -> pd.DataFrame:
    """Return candidate nearby/time-overlapping detections; no causal/source claim."""
    if radius_km<=0 or window_hours<0: raise ValueError("radius_km must be >0 and window_hours >=0")
    required_e={"event_id","timestamp","latitude","longitude"}; required_d={"observed_at","latitude","longitude"}
    if not required_e.issubset(events.columns) or not required_d.issubset(detections.columns):
        raise ValueError("Events/detections lack required time and coordinate fields")
    out=[]
    for e in events.to_dict("records"):
        et=pd.to_datetime(e["timestamp"],utc=True,errors="coerce")
        if pd.isna(et): continue
        for d in detections.to_dict("records"):
            dt=pd.to_datetime(d["observed_at"],utc=True,errors="coerce")
            if pd.isna(dt): continue
            delta=abs((dt-et).total_seconds())/3600
            if delta>window_hours: continue
            dist=haversine_km(e["latitude"],e["longitude"],d["latitude"],d["longitude"])
            if pd.notna(dist) and dist<=radius_km:
                out.append({"event_id":e["event_id"],"detection_time":dt,"time_delta_hours":round(delta,3),
                  "distance_km":round(dist,3),"context_source":d.get("source","NASA FIRMS"),
                  "data_class":d.get("data_class","satellite_fire_detection"),
                  "interpretation":"Candidate spatiotemporal context only; not evidence of causation or source attribution."})
    return pd.DataFrame(out,columns=["event_id","detection_time","time_delta_hours","distance_km","context_source","data_class","interpretation"])
