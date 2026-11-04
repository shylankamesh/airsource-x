import pandas as pd
from airsource.reliability import ingestion_freshness, benchmark_summary


def test_empty_ingestion_history_returns_empty_frame():
    assert ingestion_freshness(pd.DataFrame()).empty


def test_failed_only_source_is_unavailable():
    frame=pd.DataFrame({"source":["A"],"status":["failed"],"completed_at":["2024-01-01T00:00:00Z"]})
    out=ingestion_freshness(frame,now=pd.Timestamp("2024-01-02T00:00:00Z"))
    assert out.iloc[0]["status"]=="UNAVAILABLE"


def test_benchmark_summary_reads_holdout_runs():
    report={"runs":[{"station":"A","horizon":"h1","model":"M","mae":1.2,"rmse":2.0,"bias":0.1,"samples":50}]}
    out=benchmark_summary(report)
    assert len(out)==1 and out.iloc[0]["mae_ug_m3"]==1.2
