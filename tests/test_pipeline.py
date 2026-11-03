import numpy as np
import pandas as pd
import pytest
from airsource.pipeline import (TZ,load_station,build_issues,make_synthetic_fixture,
                                split_chronological,station_overlap,get_metrics)

def test_15minute_aggregation_and_missing(tmp_path):
    t=pd.date_range('2024-01-01',periods=12,freq='15min',tz=TZ)
    values=[10,20,30,40, 10,20,np.nan,np.nan, 20,30,40,np.nan]
    p=tmp_path/'sample.csv'
    pd.DataFrame({'Timestamp':t.tz_localize(None).astype(str),'PM2.5 (ug/m3)':values,'PM10 (ug/m3)':[40]*12}).to_csv(p,index=False)
    h,a=load_station(p)
    assert h.pm25.iloc[0]==25
    assert np.isnan(h.pm25.iloc[1])
    assert h.pm25.iloc[2]==30
    assert a['input_cadence']=='15-minute'

def test_negative_pm_invalid(tmp_path):
    t=pd.date_range('2024-01-01',periods=5,freq='h')
    p=tmp_path/'negative.csv'
    pd.DataFrame({'Timestamp':t.astype(str),'PM2.5':[10,-999,30,40,50]}).to_csv(p,index=False)
    h,a=load_station(p)
    assert pd.isna(h.pm25.iloc[1])

def test_issues_two_nonoverlapping_forward_windows():
    t=pd.date_range('2024-01-01',periods=10*24,freq='h',tz=TZ)
    h=pd.DataFrame({'pm25':np.arange(len(t),dtype=float),
                    'pm10':np.arange(len(t),dtype=float)+20,
                    'no2':20.0,'ws':2.0,'rh':40.0},index=t)
    issues=build_issues(h)
    a=issues.loc[issues.issue_ist==pd.Timestamp('2024-01-03',tz=TZ)].iloc[0]
    T=a.issue_ist
    assert a.target_0_24 == pytest.approx(h.loc[T+pd.Timedelta(hours=1):T+pd.Timedelta(hours=24),'pm25'].mean())
    assert a.target_24_48 == pytest.approx(h.loc[T+pd.Timedelta(hours=25):T+pd.Timedelta(hours=48),'pm25'].mean())
    assert a.pm_lag24_mean == pytest.approx(h.loc[T-pd.Timedelta(hours=24):T-pd.Timedelta(hours=1),'pm25'].mean())

def test_future_observation_cannot_change_issue_features():
    h=make_synthetic_fixture(14)
    original=build_issues(h).iloc[4]
    mutated=h.copy()
    mutated.loc[original.issue_ist+pd.Timedelta(hours=1):,'pm25']=99999
    second=build_issues(mutated).iloc[4]
    for c in ['pm_lag24_mean','pm_lag48_mean','pm_lag72_mean','pm_lag7d_mean','pm_last_valid']:
        assert np.isclose(original[c],second[c],equal_nan=True)
    assert original.target_0_24 != second.target_0_24

def test_target_availability_without_imputation():
    h=make_synthetic_fixture(15)
    T=pd.Timestamp('2024-01-07',tz=TZ)
    h.loc[T+pd.Timedelta(hours=1):T+pd.Timedelta(hours=11),'pm25']=np.nan
    r=build_issues(h).set_index('issue_ist').loc[T]
    assert r.target_0_24_count<18
    assert np.isnan(r.target_0_24)

def test_split_embargo_and_sizes():
    h=make_synthetic_fixture(260)
    issues=build_issues(h)
    tr,va,te=split_chronological(issues)
    assert len(tr)>100 and len(te)>15
    assert (va.issue_ist.min()-tr.issue_ist.max())>pd.Timedelta(days=2)
    assert (te.issue_ist.min()-va.issue_ist.max())>pd.Timedelta(days=2)

def test_persistence_metric():
    m=get_metrics([10,20],[11,19]);assert m['mae']==1

def test_spatial_comparison_uses_coincident_measurements():
    a=make_synthetic_fixture(4)
    b=a.copy();b['pm25']+=10
    b.loc[b.index[:8],'pm25']=np.nan
    c,ts=station_overlap({'one':a,'two':b})
    v=ts.dropna()
    assert c.iloc[0].common_hours==len(v)
    assert c.iloc[0].mean_difference_ugm3==pytest.approx(-10)
