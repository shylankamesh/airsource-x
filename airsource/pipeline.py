"""Leakage-aware AirSource X PM2.5 forecasting, data ingestion, and evaluation.

Research prototype; raw station data must be independently verified for real-world claims.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from lightgbm import LGBMRegressor

TZ = 'Asia/Kolkata'
FEATURES = ['pm_lag24_mean', 'pm_lag48_mean', 'pm_lag72_mean', 'pm_lag7d_mean',
            'pm_lag24_std', 'pm_last_valid', 'month_sin', 'month_cos', 'dayofyear_sin',
            'dayofyear_cos', 'weekday', 'pm10_lag24_mean', 'no2_lag24_mean',
            'ws_lag24_mean', 'rh_lag24_mean']
OPTIONAL = ['pm10', 'no2', 'ws', 'rh']


def _locate(df, aliases):
    keys={str(c).strip().lower().replace('_','').replace(' ',''): c for c in df.columns}
    for a in aliases:
        k=a.strip().lower().replace('_','').replace(' ','')
        if k in keys: return keys[k]
    return None


def load_station(path, station=None):
    """Parse OpenCity CPCB 15-minute/hourly CSV with explicit source timestamp assumption.

    CSV Timestamp is assumed IST unless timezone is embedded. VERIFY source semantics before
    calling this an operational as-of evaluation. No post-observation availability delay known.
    """
    p=Path(path)
    df=pd.read_csv(p, low_memory=False)
    time_col=_locate(df,['Timestamp','datetime','date_time','Date','Time'])
    pm_col=_locate(df,['PM2.5 (ug/m3)','PM2.5','PM25','pm2_5','PM2.5 (µg/m³)'])
    st_col=_locate(df,['Station Name','station','station_name'])
    if not time_col or not pm_col: raise ValueError(f'Missing Timestamp/PM2.5 columns: {list(df.columns)}')
    if station is not None and st_col:
        mask=df[st_col].astype(str).str.contains(station,case=False,regex=False)
        if not mask.any(): raise ValueError(f'No station name matching {station!r}')
        df=df.loc[mask].copy()
    raw_rows=len(df)
    time=pd.to_datetime(df[time_col],errors='coerce')
    if isinstance(time.dtype,pd.DatetimeTZDtype):
        time=time.dt.tz_convert(TZ)
    else:
        time=time.dt.tz_localize(TZ,ambiguous='NaT',nonexistent='NaT')
    data=pd.DataFrame(index=pd.DatetimeIndex(time))
    for dst, al in {'pm25':[pm_col], 'pm10':['PM10 (ug/m3)','PM10 (µg/m³)','PM10'],
                   'no2':['NO2 (ug/m3)','NO2 (µg/m³)','NO2'],'ws':['WS (m/s)','wind_speed','WS'],
                   'rh':['RH (%)','humidity','RH']}.items():
        col=_locate(df,al)
        data[dst]=pd.to_numeric(df[col],errors='coerce').to_numpy() if col else np.nan
        data.loc[data[dst]<0,dst]=np.nan
    bad_ts=int(data.index.isna().sum());data=data.loc[data.index.notna()].sort_index()
    dup=int(data.index.duplicated().sum())
    # Duplicate source timestamps are collapsed; never count same timestamp twice.
    data=data.groupby(level=0).mean(numeric_only=True)
    step=data.index.to_series().diff().dropna().median()
    is_quarter=step<=pd.Timedelta(minutes=20)
    if is_quarter:
        grouped=data.resample('h')
        h=grouped.mean()
        counts=grouped.count()
        for c in data.columns: h.loc[counts[c]<3,c]=np.nan
    else:
        h=data.resample('h').mean()
    h=h.asfreq('h')
    if len(h)==0: raise ValueError('No valid timestamps')
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    coverage=float(h.pm25.notna().mean())
    audit={'file':p.name,'sha256':sha,'source_rows':raw_rows,'bad_timestamps':bad_ts,
           'duplicate_timestamps':dup,'input_cadence':'15-minute' if is_quarter else 'hourly/other',
           'timestamp_assumption':'Timestamp is IST unless explicit offset',
           'first_hour_ist':str(h.index.min()),'last_hour_ist':str(h.index.max()),
           'total_hours':int(len(h)),'valid_pm25_hours':int(h.pm25.notna().sum()),
           'pm25_hour_coverage':round(coverage,5),
           'max_missing_streak_hours':int(h.pm25.isna().astype(int).groupby(h.pm25.notna().cumsum()).sum().max()),
           'optional_coverage':{c:round(float(h[c].notna().mean()),5) for c in OPTIONAL}}
    return h,audit


def make_synthetic_fixture(n_days=430, seed=42, station='SYNTHETIC_A'):
    """Deterministic simulation for software tests ONLY, not Delhi measurements."""
    rng=np.random.default_rng(seed)
    idx=pd.date_range('2024-01-01',periods=n_days*24,freq='h',tz=TZ)
    hour=idx.hour.to_numpy();day=np.arange(len(idx))/24
    season=34*np.cos(2*np.pi*day/365)
    daily=12*np.cos(2*np.pi*(hour-7)/24)
    event=np.zeros(len(idx))
    for center in np.arange(130, n_days-2, 27):
        distance=np.arange(len(idx))/24-center
        event+=90*np.exp(-0.5*(distance/1.7)**2)
    base=95+season+daily+event
    pm=np.clip(base+rng.normal(0,17,len(idx)),5,550)
    if station.endswith('B'):
        pm=np.clip(pm*.86+rng.normal(0,20,len(pm)),5,550)
    pm10=np.clip(pm*1.6+rng.normal(0,25,len(idx)),pm+2,None)
    no2=24+hour*0.6 + rng.normal(0,6,len(idx))
    ws=np.clip(2.5+1.1*np.sin(2*np.pi*hour/24)+rng.normal(0,.5,len(idx)),0,12)
    rh=np.clip(50+13*np.cos(2*np.pi*hour/24)+rng.normal(0,5,len(idx)),10,100)
    a=pd.DataFrame({'pm25':pm,'pm10':pm10,'no2':no2,'ws':ws,'rh':rh},index=idx)
    for c in a.columns:
        m=rng.random(len(a))<(0.025 if c=='pm25' else 0.075)
        a.loc[m,c]=np.nan
    return a


def _valid_mean(x, minimum=18):
    a=x.dropna()
    return float(a.mean()) if len(a)>=minimum else np.nan


def build_issues(hourly, station='Station'):
    """Issue times at midnight IST, past-only features and strictly forward targets.

    Observations at the issue timestamp T are deliberately excluded from inputs.
    For real operational replay, verify the monitor's publication lag independently.
    """
    if hourly.index.tz is None:raise ValueError('Expected timezone-aware hourly index')
    h=hourly.sort_index().asfreq('h')
    rows=[]
    for T in pd.date_range(h.index.min().ceil('D'),h.index.max().floor('D')-pd.Timedelta(days=2),freq='D',tz=TZ):
        past=h.loc[T-pd.Timedelta(hours=24):T-pd.Timedelta(hours=1)]
        if len(past)<24 or past.pm25.count()<18:continue
        hist48=h.loc[T-pd.Timedelta(hours=48):T-pd.Timedelta(hours=1)]
        hist72=h.loc[T-pd.Timedelta(hours=72):T-pd.Timedelta(hours=1)]
        hist7=h.loc[T-pd.Timedelta(days=7):T-pd.Timedelta(hours=1)]
        future1=h.loc[T+pd.Timedelta(hours=1):T+pd.Timedelta(hours=24),'pm25']
        future2=h.loc[T+pd.Timedelta(hours=25):T+pd.Timedelta(hours=48),'pm25']
        if len(future1)!=24 or len(future2)!=24: continue
        row={'issue_ist':T,'station':station,'target_0_24':_valid_mean(future1),
             'target_24_48':_valid_mean(future2),
             'target_0_24_count':int(future1.count()),'target_24_48_count':int(future2.count()),
             'pm_lag24_mean':float(past.pm25.mean()),
             'pm_lag48_mean':float(hist48.pm25.mean()) if len(hist48)>=48 and hist48.pm25.count()>=36 else np.nan,
             'pm_lag72_mean':float(hist72.pm25.mean()) if len(hist72)>=72 and hist72.pm25.count()>=54 else np.nan,
             'pm_lag7d_mean':float(hist7.pm25.mean()) if len(hist7)>=168 and hist7.pm25.count()>=126 else np.nan,
             'pm_lag24_std':float(past.pm25.std()),'pm_last_valid':float(past.pm25.dropna().iloc[-1]),
             'month_sin':float(np.sin(2*np.pi*T.month/12)), 'month_cos':float(np.cos(2*np.pi*T.month/12)),
             'dayofyear_sin':float(np.sin(2*np.pi*T.dayofyear/365.25)),
             'dayofyear_cos':float(np.cos(2*np.pi*T.dayofyear/365.25)), 'weekday':int(T.dayofweek)}
        for c in OPTIONAL:
            row[{'pm10':'pm10_lag24_mean','no2':'no2_lag24_mean','ws':'ws_lag24_mean','rh':'rh_lag24_mean'}[c]] = float(past[c].mean()) if c in past and past[c].count()>=18 else np.nan
        rows.append(row)
    out=pd.DataFrame(rows)
    if len(out):out=out.sort_values('issue_ist').reset_index(drop=True)
    return out


def split_chronological(issues,purge_days=2):
    """60/20/20 chronological split, two-day exclusions at split boundaries."""
    x=issues.sort_values('issue_ist').reset_index(drop=True)
    if len(x)<180:raise ValueError(f'Need >=180 issue times: got {len(x)}')
    a=int(len(x)*.60);b=int(len(x)*.80)
    train=x.iloc[:a].copy()
    valid=x.iloc[a:].loc[lambda y:y.issue_ist > train.issue_ist.max()+pd.Timedelta(days=purge_days)].iloc[:max(0,b-a-purge_days)].copy()
    test=x.iloc[b:].loc[lambda y:y.issue_ist > valid.issue_ist.max()+pd.Timedelta(days=purge_days)].copy()
    if min(map(len,[train,valid,test]))<15:raise ValueError('Insufficient split rows after embargo')
    return train,valid,test


def get_metrics(y,p):
    a=np.asarray(y,dtype=float);b=np.asarray(p,dtype=float)
    return {'n':int(len(a)),'mae':round(float(mean_absolute_error(a,b)),4),
            'rmse':round(float(np.sqrt(mean_squared_error(a,b))),4),
            'bias':round(float(np.mean(b-a)),4)}


def evaluate_forecasts(issues,outdir, data_label='UNVERIFIED',train_per_station=False):
    """Train and evaluate separate horizon LightGBM models vs persistence/seasonal.

    For multi-station projects this runs independently on each station (no spatial ML claim).
    Never mix data unless explicit spatial-holdout methodology is provided.
    """
    output=Path(outdir);output.mkdir(parents=True,exist_ok=True)
    scores=[];predictions=[];splits=[];event_results=[];interval_results=[]
    if train_per_station and 'station' in issues:
        groups=issues.groupby('station')
    else:groups=[(str(issues.station.iloc[0]),issues)]
    for name,g in groups:
        tr,va,te=split_chronological(g)
        splits.append({'station':name,'train_n':len(tr),'valid_n':len(va),'test_n':len(te),
                       'train_last':str(tr.issue_ist.max()),'validation_first':str(va.issue_ist.min()),
                       'validation_last':str(va.issue_ist.max()),'test_first':str(te.issue_ist.min())})
        for horizon in ['target_0_24','target_24_48']:
            # Train/validate/test same non-null target windows for all models.
            train=tr.dropna(subset=[horizon]);test=te.dropna(subset=[horizon]);val=va.dropna(subset=[horizon])
            if len(train)<40 or len(test)<15:raise ValueError('Not enough valid target labels')
            model=LGBMRegressor(n_estimators=160, learning_rate=.045,max_depth=5,num_leaves=15,
                                min_child_samples=15,random_state=14,verbosity=-1)
            model.fit(train[FEATURES],train[horizon])
            model_folder=output/'models'/str(name).replace('/','_')
            model_folder.mkdir(parents=True,exist_ok=True)
            joblib.dump(model,model_folder/f'{horizon}_lightgbm.joblib')
            (model_folder/f'{horizon}_metadata.json').write_text(json.dumps({'station':name,'horizon':horizon,'features':FEATURES,'train_last':str(train.issue_ist.max()),'test_first':str(test.issue_ist.min()),'data_label':data_label},indent=2),encoding='utf-8')
            model_pred=np.maximum(model.predict(test[FEATURES]),0)
            val_pred=np.maximum(model.predict(val[FEATURES]),0)
            # Simple split-conformal residual interval; dependent time series may
            # violate exchangeability assumptions, so empirical coverage is reported.
            abs_res=np.abs(val[horizon].to_numpy()-val_pred)
            rank_level=min(1.0,np.ceil((len(abs_res)+1)*.90)/len(abs_res)) if len(abs_res) else None
            q=float(np.quantile(abs_res,rank_level,method='higher')) if len(abs_res)>=15 else np.nan
            interval_lower=np.maximum(model_pred-q,0)
            interval_upper=model_pred+q
            empirical_coverage=float(np.mean((test[horizon].to_numpy()>=interval_lower)&
                                                (test[horizon].to_numpy()<=interval_upper))) if np.isfinite(q) else np.nan
            interval_results.append({'data_label':data_label,'station':name,'horizon':horizon,
                                     'nominal_coverage':0.90,'empirical_coverage':empirical_coverage,
                                     'mean_interval_width_ugm3':float(np.mean(interval_upper-interval_lower)) if np.isfinite(q) else np.nan,
                                     'calibration_rows':len(val),'test_rows':len(test),
                                     'calibration_limitation':'Temporal dependence: coverage is empirical, not guaranteed'})
            persistence=test.pm_lag24_mean.to_numpy()
            persistence_val=val.pm_lag24_mean.to_numpy()
            # Main-version comparator: last available hourly observation. Keep it
            # separate from the preceding-24-hour mean persistence baseline.
            last_observed=test.pm_last_valid.to_numpy()
            last_observed_val=val.pm_last_valid.to_numpy()
            # Calendar baseline fitted on train rows ONLY; month fallback global.
            monthly=train.groupby('month_cos')[horizon].mean() if False else train.groupby(train.issue_ist.dt.month)[horizon].mean()
            seasonal=test.issue_ist.dt.month.map(monthly).fillna(train[horizon].mean()).to_numpy()
            seasonal_val=val.issue_ist.dt.month.map(monthly).fillna(train[horizon].mean()).to_numpy()
            validation_candidates={'LightGBM':val_pred,'Last-observation':last_observed_val,
                                   'Persistence':persistence_val,'Seasonal':seasonal_val}
            chosen=min(validation_candidates,key=lambda k:mean_absolute_error(val[horizon],validation_candidates[k]))
            champion={'LightGBM':model_pred,'Last-observation':last_observed,
                      'Persistence':persistence,'Seasonal':seasonal}[chosen]
            (model_folder/f'{horizon}_selected.json').write_text(json.dumps({
                'method_chosen_by_validation':chosen,
                'validation_mae':{k:float(mean_absolute_error(val[horizon],v)) for k,v in validation_candidates.items()},
                'SELECTION_POLICY':'lowest validation MAE only; test data never consulted'},indent=2),encoding='utf-8')
            metrics={'LightGBM':get_metrics(test[horizon],model_pred),
                     'Last-observation':get_metrics(test[horizon],last_observed),
                     'Persistence':get_metrics(test[horizon],persistence),
                     'Seasonal':get_metrics(test[horizon],seasonal),
                     'Validation-selected':get_metrics(test[horizon],champion)}
            # Predeclared exploratory elevated-pollution threshold; NOT CPCB severe AQI.
            threshold=150.0
            truth=np.asarray(test[horizon],dtype=float)>=threshold
            for algorithm,yp in [('LightGBM',model_pred),('Last-observation',last_observed),
                                 ('Persistence',persistence),('Seasonal',seasonal),('Validation-selected',champion)]:
                alarm=np.asarray(yp,dtype=float)>=threshold
                hits=int((truth & alarm).sum());misses=int((truth & ~alarm).sum())
                false=int((~truth & alarm).sum());true_neg=int((~truth & ~alarm).sum())
                event_results.append({'data_label':data_label,'station':name,'horizon':horizon,
                                      'model':algorithm,'threshold_ugm3':threshold,
                                      'threshold_label':'EXPLORATORY high-PM event (not official AQI)',
                                      'actual_events':int(truth.sum()),'hits':hits,'misses':misses,
                                      'false_alarms':false,'true_negatives':true_neg,
                                      'precision':hits/(hits+false) if hits+false else np.nan,
                                      'recall':hits/(hits+misses) if hits+misses else np.nan})
            for algorithm,m in metrics.items():
                scores.append({'data_label':data_label,'station':name,'horizon':horizon,'model':algorithm,**m})
            for i,T in enumerate(test.issue_ist):
                predictions.append({'data_label':data_label,'station':name,'issue_ist':T.isoformat(),
                                    'horizon':horizon,'actual':float(test[horizon].iloc[i]),
                                    'LightGBM':float(model_pred[i]),'Last-observation':float(last_observed[i]),
                                    'Persistence':float(persistence[i]),
                                    'Seasonal':float(seasonal[i]),'Validation-selected':float(champion[i]),'selected_method':chosen,'interval_lower':float(interval_lower[i]),'interval_upper':float(interval_upper[i])})
            # 24h and 48h target forecast feature importance is diagnostic, not physical attribution.
            imp=pd.DataFrame({'feature':FEATURES,'importance_gain_or_splits':model.feature_importances_})
            imp.sort_values('importance_gain_or_splits',ascending=False).to_csv(output/f'{name}_{horizon}_feature_importance.csv',index=False)
    sc=pd.DataFrame(scores);pred=pd.DataFrame(predictions)
    sc.to_csv(output/'forecast_metrics.csv',index=False);pred.to_csv(output/'forecast_predictions.csv',index=False)
    pd.DataFrame(event_results).to_csv(output/'event_metrics.csv',index=False)
    pd.DataFrame(interval_results).to_csv(output/'interval_metrics.csv',index=False)
    (output/'forecast_splits.json').write_text(json.dumps(splits,indent=2),encoding='utf-8')
    return sc,pred,splits


def station_overlap(station_hourly):
    """Only report coincident readings, never interpolate a citywide surface."""
    table=pd.concat({k:v['pm25'] for k,v in station_hourly.items()},axis=1)
    records=[]
    names=list(table.columns)
    for i in range(len(names)):
        for j in range(i+1,len(names)):
            v=table[[names[i],names[j]]].dropna()
            records.append({'station_a':names[i],'station_b':names[j],'common_hours':len(v),
                            'correlation':float(v.corr().iloc[0,1]) if len(v)>=3 else np.nan,
                            'mean_difference_ugm3':float((v.iloc[:,0]-v.iloc[:,1]).mean()) if len(v) else np.nan})
    return pd.DataFrame(records),table

