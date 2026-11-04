# AirSource X — Executable Research Prototype
**Neural Storm 2026 · Track 2: Green Planet · GP-01: Air Quality Monitoring & Source Attribution**

> **Project status (4 November 2026):** The forecasting/evidence prototype and a retrospective single-station evaluation using OpenCity-listed CPCB ITO data are implemented. Results remain unverified against provider publication/availability semantics and do not establish live forecast performance, multi-station Delhi performance, or physical pollution-source attribution. Synthetic policy fixtures remain software consistency tests only.

**Tagline:** Forecast the pollution. Investigate the evidence. Make uncertainty visible.

## Team details (required before Devpost submission)
- Team name: **[ADD YOUR ACTUAL TEAM NAME]**
- Member 1: **[ADD NAME]**
- Member 2: **[ADD NAME]**
- Submission: **[https://github.com/shylankamesh/airsource-x](https://github.com/shylankamesh/airsource-x)**
- Live demo: **[ADD IF DEPLOYED]**

## Delhi CPCB study and website

A retrospective run is included in `results/delhi_ito_2024_25/`, using the OpenCity listing for ITO, Delhi - CPCB 15-minute observations. The source file contains 68,985 rows, spanning 1 January 2024 through 1 January 2026, with 93.257% hourly PM2.5 coverage after aggregation and a 148-hour maximum missing streak. The source includes one blank annual footer row, which is excluded when timestamps are parsed. Review `data_audit.json`, `forecast_splits.json`, and `EXPERIMENT_RESULTS.md` before citing any metric.

The static responsive website is in `website/index.html`. Open it locally, or serve the project directory with any static web server. It presents the one-station retrospective result and makes its limits explicit. It does not claim live forecast validation, all-Delhi generalization, or source attribution. The full hackathon bundle includes the raw CSV at `data/raw/`; this repository includes the raw CSV and provides its source link and checksum in `data/ITO_DELHI_DATA_MANIFEST.md`. OpenCity resource metadata lists the resource as Public Domain; retain CPCB contributor acknowledgement when redistributing or publishing.

Current held-out results (130 issues per horizon): for 0–24h, preceding-24-hour mean MAE is 26.6446 µg/m³, LightGBM MAE is 28.3714, and last-observation MAE is 45.0920; for 24–48h, the respective MAEs are 38.9823, 34.5325, and 57.9046. Validation selects LightGBM for 0–24h and the 24-hour mean for 24–48h. Nominal 90% intervals cover 71.5% and 74.6% of the test cases. These are retrospective metrics from one station and should not be presented as live operational performance.

## The problem
PM2.5 warnings and forecasts rarely give non-specialists a transparent, reproducible view of the evidence for *possible* pollution influences. Fire hotspots, wind, and pollutant ratios are non-specific and can be missing or contradictory. Presenting those indicators as measured source fractions is scientifically incorrect.

## Our solution
AirSource X provides two **actual trained LightGBM forecasts** for one ITO Delhi retrospective run, three baseline comparators (last observation, preceding-24-hour mean, and training-only seasonal mean), separate future 0–24h and 24–48h PM2.5 targets, a deterministic **evidence-hypothesis screening** engine with provenance and knowledge-removal counterfactuals, and a separate historical six-station context view. A conservative policy allows **insufficient evidence** instead of forcing an unsupported explanation. A local interactive Gradio app and a portable HTML report demonstrate results. This **does not quantify source contributions**.

### Implemented and executed
- OpenCity/CPCB-style CSV reader with timestamp parsing, basic QC, negative-value masking, source checksum and 15-minute → hourly coverage gate (3 of 4).
- Forecast target labels requiring 18 of 24 valid PM2.5 hours, independent 0–24h and 24–48h targets, past-only features and 48h temporal split purge.
- LightGBM, past-day persistence and training-only calendar mean, plus validation-based safe model selection; actual held-out MAE/RMSE/bias and 150 µg/m³ **exploratory** high-PM-event metrics.
- Approximate split-calibrated interval with held-out empirical coverage (not guaranteed due to temporal dependence).
- Separate model files, inputs, predictions, held-out test tables, feature importance and temporal split metadata.
- Verified SHAP model explanations, exported for synthetic LightGBM test cases (not source causality).
- Two-station coincident observation comparisons; does not infer origin or perform unsupported interpolation.
- Source-hypothesis engine for biomass burning and dust-like conditions with support, contradiction, missing evidence, alternatives, and deterministic rule IDs.
- Heuristic next-best-measurement guidance: missing FIRMS / transport / particulate evidence suggests specific checks and limitations.
- Evidence-removal test controls; 36 variations of 12 synthetic rule-policy scenarios and B0/B1/X comparisons. **Not a ground-truth attribution study.**
- Interactive Gradio dashboard and fully offline, interactive Plotly HTML report.
- Separate six-station historical Delhi context (June 2018–October 2019): coverage, observed daily means, and a same-hour network-relative outlier screen. It is not blended with the ITO 2024–2026 forecast experiment.
- Automated test suite: run `python -m pytest -q` to reproduce current totals.

### Not implemented or empirically validated
- Independent validation of the downloaded dataset's publication/availability time semantics and source reuse terms.
- Replicated performance across additional Delhi stations and later independent seasons.
- Publicly deployed demo; the new static site is a local artifact until hosted.
- Real satellite fire ingestion, HYSPLIT trajectories, TROPOMI, MAIAC or actual source apportionment.
- Source attribution truth labels, human usability study, trained causal source classifier or validated source percentages.
- True live data deployment or regulatory AQI. Overall AQI cannot be derived from PM2.5 alone.

## Setup
On Windows PowerShell (Python 3.11 recommended):
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m scripts.run --synthetic
python app.py
```
On macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.run --synthetic
python app.py
```
Open **http://127.0.0.1:7860/**. The Gradio app loads the ITO retrospective run by default. `website/index.html` is the judge-facing static presentation. To inspect synthetic software fixtures, set `AIRSOURCE_RESULTS_DIR=results` before launching the app.

## Run real Delhi station experiments
1. Use the bundled [ITO Delhi CPCB resource](https://data.opencity.in/dataset/delhi-hourly-air-quality-reports/resource/890f786d-fb9f-475e-8516-191bfa1b01ea), or obtain another station dataset and audit its station ID, timezone, units, coverage, and reuse terms.
2. Put any replacement CSV into `data/raw/`.
3. Run:
```bash
python -m scripts.run --csv data/raw/ito_delhi_2024_25.csv --name "ITO Delhi CPCB" --outdir results/delhi_ito_2024_25
python -m pytest -q
python app.py
```
To compare two stations, add a second `--csv ... --name ...` pair. **Confirm station IDs, date coverage, timestamp timezone, publication delay and co-pollutant units** before publishing quantitative results. The loader assumes unlabelled timestamps are IST; this needs independent verification. DO NOT claim the observational records were issued at time T if the sensor publication/availability delay is unknown. See `docs/METHODOLOGY.md`.

## Data access and licensing
The bundled ITO resource metadata lists the data license as Public Domain. CPCB asks researchers and other publishers to acknowledge the contributing agencies. See `data/ITO_DELHI_DATA_MANIFEST.md`. Public alternatives: [CPCB](https://airquality.cpcb.gov.in/ccr/), [OpenAQ](https://docs.openaq.org/), [Open-Meteo](https://open-meteo.com/), [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/). This forecasting experiment uses **no future observed weather** and requires no weather API key. Historical weather forecasts were not integrated.

## Experimental outputs
`results/delhi_ito_2024_25/EXPERIMENT_RESULTS.md` contains the retrospective ITO Delhi benchmark. Persistence wins on 0–24h test MAE; raw LightGBM wins on 24–48h test MAE, while validation selection chooses persistence for 24–48h. Nominal 90% intervals under-cover. Results are one-station retrospective evidence, not operational validation. The root `results/` folder retains explicitly labelled synthetic software fixtures and must not be confused with the Delhi run.

Outputs include `forecast_metrics.csv`, `forecast_predictions.csv`, `event_metrics.csv`, `interval_metrics.csv`, `station_overlap.csv`, `station_coverage_report.csv`, `data_audit.json`, `policy_case_results.csv`, `policy_comparison.csv`, `policy_case_trace.json`, model artifacts, and interactive `EXPERIMENT_DASHBOARD.html`.

SHAP is optional and explains model predictions, not physical sources. To regenerate SHAP tables, install `shap>=0.47,<0.60` and run `python -m scripts.explain_models` after a completed experiment.

## Research documentation
- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md): forecast target, leakage prevention, synthetic data protocol, evidence screening rules.
- [`docs/INTEGRATION_AUDIT.md`](docs/INTEGRATION_AUDIT.md): ZIP comparison, dataset/model integrity finding, integration choices, and limits of the six-station view.
- [`data/benchmarks/README.md`](data/benchmarks/README.md): six-station benchmark attribution, license, and separation from the ITO run.
- [`docs/EXPERIMENT_PROTOCOL.md`](docs/EXPERIMENT_PROTOCOL.md): experiments, controls, denominators, reproducible commands.
- [`docs/SCIENTIFIC_LIMITATIONS.md`](docs/SCIENTIFIC_LIMITATIONS.md): exact remaining scientific blockers.
- [`docs/DEMO_GUIDE.md`](docs/DEMO_GUIDE.md): judges' walkthrough and honest wording.

## Screenshots / demo
The responsive website is in `website/index.html`; the Gradio app defaults to the Delhi retrospective results while clearly marking evidence-engine scenarios as synthetic. The hero graphic is conceptual and labeled as not measured data. No browser screenshot or live deployment is included yet. Do not claim the prototype has solved GP-01 empirically.

## AI development tool disclosure (required)
This project code, documentation, and experimental prototype were generated with assistance from **ChatGPT (OpenAI)**. Human review and verification are required. Add any other tools actually used by the team (for example, GitHub Copilot or Cursor) before submission. AI assistance is not evidence that experiments ran; actual CLI outputs/tests are included.

## Limitations and appropriate use
This is a **research screening prototype**, not a chemical source-apportionment method, official AQI reporting service, health diagnosis, source-accusation engine, or emergency warning authority. No sensor/site-specific scientific causal claim or measured economic/public-health impact is established.

## License
No license chosen yet. All rights reserved until the team selects a license; third-party datasets have their own terms.



