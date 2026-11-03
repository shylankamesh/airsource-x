"""Run the AirSource X research prototype, strictly labelling real/synthetic outputs.

Usage:
 python -m scripts.run --synthetic
 python -m scripts.run --csv data/raw/del-anand-vihar-dpcc-2024-25.csv --name 'Anand Vihar'
 python -m scripts.run --csv path1.csv --csv path2.csv --name 'Anand Vihar' --name 'R K Puram'
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd
from airsource.pipeline import (load_station,make_synthetic_fixture,build_issues,evaluate_forecasts,station_overlap)
from airsource.evidence import (EvidenceInput,investigate,remove_evidence,run_policy_experiment,policy_fixtures,next_best_measurement)

ROOT=Path(__file__).resolve().parents[1]

def run(synthetic=False,files=None,names=None,outdir=None):
    files=files or [];names=names or []
    if not synthetic and not files:raise ValueError('Provide --csv station data or explicitly --synthetic')
    out=Path(outdir) if outdir else ROOT/'results';out.mkdir(parents=True,exist_ok=True)
    raw={};audits=[];issues=[];data_label='SYNTHETIC / NOT DELHI MEASUREMENTS' if synthetic else 'OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED'
    if synthetic:
        for station,seed in [('SYNTHETIC_A',42),('SYNTHETIC_B',313)]:
            h=make_synthetic_fixture(seed=seed,station=station)
            raw[station]=h
            audit={'station':station,'source':'DETERMINISTIC SYNTHETIC GENERATOR',
                   'first_hour_ist':str(h.index.min()),'last_hour_ist':str(h.index.max()),
                   'total_hours':len(h),'valid_pm25_hours':int(h.pm25.notna().sum()),
                   'pm25_hour_coverage':round(float(h.pm25.notna().mean()),5),
                   'WARNING':'Not empirical Delhi data'}
            audits.append(audit)
            issues.append(build_issues(h,station=station))
    else:
        for i,p in enumerate(files):
            name=names[i] if i<len(names) else Path(p).stem
            h,a=load_station(p)
            audit={'station':name,**a}
            audits.append(audit)
            if a['pm25_hour_coverage']<.7:raise ValueError(f'{name}: <70% valid PM2.5; see audit')
            raw[name]=h;issues.append(build_issues(h,station=name))
    (out/'data_audit.json').write_text(json.dumps(audits,indent=2,default=str))
    pd.DataFrame(audits).to_csv(out/'station_coverage_report.csv',index=False)
    allissues=pd.concat(issues,ignore_index=True)
    allissues.to_csv(out/'forecast_issue_table.csv',index=False)
    scores,preds,splits=evaluate_forecasts(allissues,out,data_label=data_label,train_per_station=True)
    policy,detail=run_policy_experiment(out)
    if len(raw)>1:
        overlap,aligned=station_overlap(raw)
        overlap.to_csv(out/'station_overlap.csv',index=False)
    else:overlap=pd.DataFrame()
    # Live, measured inputs from most recent complete historical day, without claiming any fire data.
    investigations=[]
    for station,h in raw.items():
        last=h.iloc[-24:]
        inputs=EvidenceInput(pm25=float(last.pm25.mean()),
                             pm10=float(last.pm10.mean()) if last.pm10.notna().any() else None,
                             wind_speed=float(last.ws.mean()) if last.ws.notna().any() else None,
                             humidity=float(last.rh.mean()) if last.rh.notna().any() else None,
                             fire_count_upwind=None,fires_checked=False,wind_supports_transport=None,
                             observed_at=str(last.index.max()),
                             source_refs={'monitor':station,'fire':'UNAVAILABLE','transport':'UNAVAILABLE'})
        investigations.append({'station':station,'source_mode':data_label,'input':vars(inputs),
                               'assessments':investigate(inputs),'next_measurement':next_best_measurement(inputs),
                               'remove_wind':remove_evidence(inputs,['WIND'])['diffs']})
    (out/'historical_investigations.json').write_text(json.dumps(investigations,indent=2))
    _write_markdown(out,data_label,audits,scores,policy,overlap,splits)
    _write_html(out,data_label,scores,preds,policy,overlap,investigations)
    print((out/'EXPERIMENT_RESULTS.md').read_text()[:2000]);print('OUTPUT:',str(out))
    return {'audit':audits,'scores':scores,'policy':policy,'overlap':overlap}

def _write_markdown(out,data_label,audits,scores,policy,overlap,splits):
    txt=['# AirSource X — Experiment execution report','',f'**DATA STATUS: {data_label}**','',
         '> Forecast metrics are retrospective observations from one station. They do not establish live/as-issued performance or physical source-apportionment accuracy.','',
         '## Input coverage','',pd.DataFrame(audits).to_markdown(index=False),'',
         '## Forecast benchmark (0–24h and 24–48h)','',scores.to_markdown(index=False),'',
         '## Locked evaluation partition metadata','', '```json',json.dumps(splits,indent=2),'```','',
         '## Exploratory elevated-pollution event metrics (150 µg/m³; not official AQI)' , '',
         pd.read_csv(out/'event_metrics.csv').to_markdown(index=False), '',
         '## Exploratory split-residual 90% interval coverage (temporal dependence caveat)' , '',
         pd.read_csv(out/'interval_metrics.csv').to_markdown(index=False), '',
         '## B0 / B1 / X evidence policy test — SYNTHETIC LOGIC FIXTURES ONLY','',policy.to_markdown(index=False),'',
         'These cases test rule-policy consistency, NOT ground-truth source fractions or source-classification accuracy.','',
         '## Multi-station overlap','',overlap.to_markdown(index=False) if len(overlap) else 'Not enough stations.','',
         '## Data and model limitations','',
         '- No real Delhi training metrics unless a sourced monitoring CSV was imported and its timestamps/coverage verified.','- Forecast models are lag-only and historic observed weather is used only in past-looking features; no future weather leakage.','- Real monitor publication delays have not been validated; operational as-issued replay requires ingestion availability timestamps.','- Original model uses deterministic LightGBM hyperparameters; no tuning against the untouched test set.','- Overall CPCB AQI not computed from PM2.5 alone.','- FIRMS, HYSPLIT, TROPOMI, and MAIAC are not fetched; they are explicitly unavailable, not zero.','- Source hypotheses are policy-screening, not physical source contributions.','- Spatial comparison is only coincident-station correlation, not causal origin or spatial interpolation.','- The local environment could not install Streamlit; install requirements on a connected machine to run app.py.','']
    (out/'EXPERIMENT_RESULTS.md').write_text('\n'.join(txt))

def _write_html(out,data_label,scores,preds,policy,overlap,investigations):
    import plotly.graph_objects as go
    import plotly.io as pio
    # Interactive offline report: Plotly JS embedded; chart draws genuine generated test results.
    p=preds.loc[(preds.station==preds.station.iloc[0]) & (preds.horizon=='target_0_24')].copy()
    p['issue_ist']=pd.to_datetime(p.issue_ist)
    fig=go.Figure()
    for name,fill in [('actual','#6ee7b7'),('LightGBM','#63a9ff'),('Persistence','#f7b66a')]:
        fig.add_trace(go.Scatter(x=p.issue_ist,y=p[name],name=name,mode='lines',line={'color':fill,'width':2 if name=='actual' else 1.4}))
    fig.update_layout(title='Held-out 0–24h forecasts (check DATA STATUS)',template='plotly_dark',
                      paper_bgcolor='#111b2b',plot_bgcolor='#111b2b',height=410,
                      xaxis_title='Issue time (IST)',yaxis_title='PM2.5 µg/m³',font={'family':'Arial'})
    plot=pio.to_html(fig,include_plotlyjs=True,full_html=False,config={'responsive':True})
    def html_table(df):return df.round(3).to_html(index=False,border=0,classes='data-table',escape=True)
    cases=policy_fixtures()
    example=cases[0]
    import html
    body=f'''<!DOCTYPE html><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
    <title>AirSource X — Research Experiment</title><style>
    body{{margin:0;background:#08101d;color:#dce8f7;font:15px/1.55 system-ui,Arial,sans-serif}}.wrap{{max-width:1200px;margin:auto;padding:30px 25px}}
    h1{{font-size:44px;letter-spacing:-1.4px;margin:0}}h2{{margin:38px 0 15px;font-size:22px}}p{{color:#a9bacd}}
    .head{{background:radial-gradient(ellipse at top right,#14344b,transparent 65%);padding:24px;border-radius:17px;border:1px solid #25394f}}
    .pill{{display:inline-block;border:1px solid #ddaa57;background:#3f2d1c;color:#ffdca3;border-radius:20px;padding:6px 12px;font-size:12px;font-weight:700}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}}.card{{border:1px solid #24354c;background:#111b2b;border-radius:16px;padding:18px}}
    .muted{{color:#9eb0c8}}.data-table{{border-collapse:collapse;width:100%;font-size:13px}}
    .data-table td,.data-table th{{padding:8px 10px;border-bottom:1px solid #2b3c50;text-align:left}}.data-table th{{background:#1f2d41}}
    .scroll{{overflow:auto}}.callout{{background:#14283a;border-left:3px solid #63c3d1;padding:14px 18px;border-radius:8px}}
    .footer{{color:#7f95b0;margin-top:38px;font-size:12px}}@media(max-width:750px){{h1{{font-size:30px}}.wrap{{padding:15px}}}}
    </style></head><body><div class="wrap"><header class="head"><div class="pill">{html.escape(data_label)}</div>
    <h1>AirSource <span style="color:#64dcb6">X</span></h1><p>Forecast the pollution. Investigate the evidence. Make uncertainty visible.</p>
    <div class="callout">This is an experimental research report. All results reflect the labelled input data; synthetic data are not Delhi observations. Evidence policy performance is NOT atmospheric source attribution accuracy.</div></header>
    <h2>01 / Forecast experiment</h2><div class="card">{plot}</div><h2>02 / Forecast model comparison</h2><div class="card scroll">{html_table(scores)}</div>
    <h2>03 / Evidence policy B0 vs B1 vs X</h2><div class="card scroll">{html_table(policy)}</div>
    <h2>04 / Station spatial overlap</h2><div class="card scroll">{html_table(overlap) if len(overlap) else '<p>Insufficient monitored stations</p>'}</div>
    <h2>05 / Evidence limitations</h2><div class="grid"><section class="card"><h3>Biomass-burning hypothesis</h3><p>Fire detections unavailable means source investigation must abstain. Never treat a missing record as verified zero fires.</p></section>
    <section class="card"><h3>Dust-like hypothesis</h3><p>PM10−PM2.5 and meteorology are screening indicators, not measured mineral-dust fractions.</p></section>
    <section class="card"><h3>ML interpretation</h3><p>MAE is measured only against the displayed input dataset. Model feature importance does not establish physical causality.</p></section></div>
    <p class="footer">Generated from executable Python pipeline · No fabricated measurements · See EXPERIMENT_RESULTS.md and the source repository for reproducibility.</p>
    </div></body></html>'''
    (out/'EXPERIMENT_DASHBOARD.html').write_text(body)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='AirSource X reproducible experiments')
    parser.add_argument('--synthetic',action='store_true',help='Run labelled synthetic software experiment only')
    parser.add_argument('--csv',action='append',default=[],help='OpenCity/CPCB CSV; may be repeated')
    parser.add_argument('--name',action='append',default=[],help='Station display name paired with --csv')
    parser.add_argument('--outdir',default=None)
    args=parser.parse_args()
    run(args.synthetic,args.csv,args.name,args.outdir)
