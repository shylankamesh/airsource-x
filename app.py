"""Offline Gradio dashboard for AirSource X experimental outputs.

By default it loads the bundled retrospective ITO Delhi run. Set
AIRSOURCE_RESULTS_DIR=results to inspect the synthetic software fixtures.
Then run `python app.py` (http://127.0.0.1:7860).
"""
from __future__ import annotations
from pathlib import Path
import json
import pandas as pd
import numpy as np
import gradio as gr
import plotly.graph_objects as go
from airsource.evidence import policy_fixtures, investigate, remove_evidence, next_best_measurement

ROOT=Path(__file__).resolve().parent
DEFAULT_REAL_RESULTS=ROOT/'results'/'delhi_ito_2024_25'
RESULTS=Path(__import__('os').environ.get('AIRSOURCE_RESULTS_DIR',
             str(DEFAULT_REAL_RESULTS if (DEFAULT_REAL_RESULTS/'forecast_metrics.csv').exists() else ROOT/'results')))
CASES=policy_fixtures()
CASENAMES=[f"{c['id']} | {c['scenario']}" for c in CASES]
STYLE='''
#main-title {font-size:36px;font-weight:750;letter-spacing:-1.5px;color:#0f3550}
.warning {padding:14px;border-radius:10px;background:#fff3dd;border-left:4px solid #d79934}
'''

def fetch_csv(name):
    p=RESULTS/name
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

def plot_pred(station,horizon):
    p=fetch_csv('forecast_predictions.csv')
    f=go.Figure()
    if len(p):
        p=p.loc[(p.station==station)&(p.horizon==horizon)]
        for key,color in [('actual','#2ca58d'),('LightGBM','#3386c7'),('Persistence','#ef9b43'),('Seasonal','#b480db')]:
            f.add_trace(go.Scatter(x=p.issue_ist,y=p[key],name=key,line={'color':color}))
    f.update_layout(template='plotly_white',height=400,xaxis_title='Issue time IST',
                    yaxis_title='Future mean PM2.5 (µg/m³)',margin={'l':60,'r':20,'t':25,'b':50})
    return f

def investigation_info(case_name,removed):
    idx=CASENAMES.index(case_name)
    selected=CASES[idx]
    inp=selected['input']
    result=remove_evidence(inp,removed)
    lines=[f'### {selected["scenario"].replace("_"," ").title()}',
           '**SYNTHETIC SOFTWARE POLICY FIXTURE — NOT AN ACTUAL DELHI EVENT.**',
           '',f'Disabled inputs: **{", ".join(removed) if removed else "None"}**','']
    for h in ['biomass_burning','dust_like']:
        a=result['after'][h]
        lines.extend([f'#### {h.replace("_"," ").title()} — {a["outcome"]}',
                      f'- **Previously:** {result["diffs"][h]["before"]}',
                      f'- **Supporting:** {"; ".join(a["support"]) if a["support"] else "None documented"}',
                      f'- **Contradictions:** {"; ".join(a["contradiction"]) if a["contradiction"] else "None documented"}',
                      f'- **Missing:** {"; ".join(a["missing"]) if a["missing"] else "None"}',
                      f'- **Rule trace:** `{", ".join(a["rule_ids"])}`',''])
    lines.append('### Suggested next measurements (heuristic, not guaranteed proof)')
    masked=__import__('copy').deepcopy(inp)
    for family in removed:
        if family=='FIRMS':masked.fire_count_upwind=None;masked.fires_checked=False
        elif family=='WIND':masked.wind_supports_transport=None;masked.wind_speed=None
        elif family=='PM10':masked.pm10=None
        elif family=='PM25':masked.pm25=None
        elif family=='RH':masked.humidity=None
    for suggestion in next_best_measurement(masked):
        lines.append(f'- **{suggestion["for_hypothesis"]}**: {suggestion["suggestion"]} — {suggestion["reason"]}')
    return '\n'.join(lines)

def app_factory():
    predictions=fetch_csv('forecast_predictions.csv')
    metrics=fetch_csv('forecast_metrics.csv')
    policy=fetch_csv('policy_comparison.csv')
    events=fetch_csv('event_metrics.csv')
    stations=sorted(predictions.station.unique().tolist()) if len(predictions) else ['NO_DATA']
    data_status=predictions.data_label.iloc[0] if len(predictions) else 'NO EXPERIMENT RESULTS — RUN THE CLI'
    with gr.Blocks(title='AirSource X | Pollution Intelligence') as demo:
        gr.Markdown('''# AirSource X | Pollution Intelligence
**Forecast the pollution. Investigate the evidence. Make uncertainty visible.**''')
        gr.Markdown(f'### ⚠ DATA STATUS: **{data_status}**\nForecast results are retrospective ITO, Delhi observations. Availability at issue time is unverified. Source-screening examples remain synthetic software fixtures, not actual events or chemical source apportionment.')
        with gr.Tabs():
            with gr.Tab('Forecast Laboratory'):
                gr.Markdown('**Independent 0–24h and 24–48h forecasts**; chronological holdout with a two-day embargo. No future weather used.')
                with gr.Row():
                    station=gr.Dropdown(choices=stations,value=stations[0],label='Station')
                    horizon=gr.Radio(choices=['target_0_24','target_24_48'],value='target_0_24',label='Future averaging window')
                curve=gr.Plot(value=plot_pred(stations[0],'target_0_24'))
                station.change(plot_pred,inputs=[station,horizon],outputs=curve)
                horizon.change(plot_pred,inputs=[station,horizon],outputs=curve)
                gr.Markdown('#### Forecast error comparison (same held-out rows)')
                gr.Dataframe(value=metrics,interactive=False)
                gr.Markdown('#### Elevated-PM event test (threshold 150 µg/m³, exploratory—not the official CPCB AQI category)')
                gr.Dataframe(value=events,interactive=False)
            with gr.Tab('Source Investigation Studio'):
                gr.Markdown('**Directly recomputed rule engine**, with supporting, contradictory, missing and provenance states. These are synthetic logic fixtures, not actual pollution events.')
                scenario=gr.Dropdown(choices=CASENAMES,value=CASENAMES[0],label='Predeclared test case')
                disabled=gr.CheckboxGroup(choices=['FIRMS','WIND','PM10','PM25','RH'],value=[],label='Simulate evidence removal (NOT emission reduction)')
                evidence=gr.Markdown(value=investigation_info(CASENAMES[0],[]))
                scenario.change(investigation_info,inputs=[scenario,disabled],outputs=evidence)
                disabled.change(investigation_info,inputs=[scenario,disabled],outputs=evidence)
            with gr.Tab('ML Explainability (SHAP)'):
                gr.Markdown('Genuine Tree SHAP values for the trained LightGBM models, if `python -m scripts.explain_models` ran. These are **model prediction effects**, NOT chemical source contributions.')
                gr.Dataframe(value=fetch_csv('shap_global_importance.csv'),interactive=False)
                gr.Markdown('#### One held-out prediction decomposition')
                gr.Dataframe(value=fetch_csv('shap_local_example.csv'),interactive=False)
            with gr.Tab('Multi-station Context'):
                gr.Markdown('Coincident observations only. Correlation does not establish a pollution source or wind trajectory.')
                gr.Dataframe(value=fetch_csv('station_overlap.csv'),interactive=False)
                gr.Markdown('Further spatial modelling requires verified station metadata and independent spatial holdout.')
            with gr.Tab('Reliability & Research'):
                gr.Markdown('#### B0 / B1 / X policy comparison — synthetic rule fixtures only')
                gr.Dataframe(value=policy,interactive=False)
                gr.Markdown('The 36 logic inputs are variations of 12 predeclared synthetic scenarios; results measure **policy conformance**, not physical source-attribution accuracy. Some exact policy outcomes fail; see CSV trace.')
                gr.Markdown('#### Data audit and provenance')
                gr.File(value=[str(RESULTS/'station_coverage_report.csv')] if (RESULTS/'station_coverage_report.csv').exists() else None,label='Station audit CSV',interactive=False)
                gr.Markdown('#### Limitations: one-station retrospective evaluation only. The 90% intervals under-cover in held-out results. No as-issued availability audit, other-station validation, real satellite detections or atmospheric trajectories. Do not generalize to all Delhi or claim India-wide forecast skill.')
            with gr.Tab('README / Reproduce'):
                gr.Markdown('''### Reproduce these numbers
```bash
pip install -r requirements.txt
python app.py
pytest -q
```
The dashboard loads `results/delhi_ito_2024_25/` by default. To rerun the bundled observations:
```bash
python -m scripts.run --csv data/raw/ito_delhi_2024_25.csv --name "ITO Delhi CPCB" --outdir results/delhi_ito_2024_25
```
To inspect clearly labelled synthetic policy fixtures, set `AIRSOURCE_RESULTS_DIR=results` before launching. Read `docs/METHODOLOGY.md` and `results/delhi_ito_2024_25/EXPERIMENT_RESULTS.md` before presentation.''')
    return demo

if __name__=='__main__':
    app_factory().launch(server_name='127.0.0.1',server_port=7860,show_error=True)
