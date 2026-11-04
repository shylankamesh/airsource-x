# AirSource-X V8 — Product integration increment

## V8 scope

V8 builds on V7 and adds three user-facing workspaces:

- **Historical replay:** upload an evidence ledger with explicit `observed_at` and `available_at`; select an as-of cutoff; exclude late, missing-time, and impossible availability-before-observation records. The bundled Delhi dataset has no verified availability timestamps and is not silently replayed.
- **Public impact & decisions:** latest-per-station review table with a user-selected PM2.5 screening threshold and a human-review workflow. The threshold is explicitly not an official AQI or health threshold. The page does not issue medical advice or source attribution.
- **Reliability & research:** shows the saved historical benchmark runs, model error, bias, interval coverage/width, and local ingestion freshness. Benchmark scope limitations are displayed alongside the metrics.

The External data workspace now maps stored FIRMS detection coordinates when present. Spatial Intelligence remains a separate station network view. The sidebar has a consolidated navigation for overview, forecast, station watch, spatial intelligence, episode intelligence, source investigation & evidence, historical replay, external data, public impact, reliability & research, and methods.

## What remains incomplete

V8 is a stronger integrated research prototype, not a production-ready environmental operations platform. Specifically:

- TROPOMI and MAIAC data ingestion and QA pipelines are not implemented.
- India OGD records are fetched as raw provider rows; no universal field/unit mapping is assumed.
- Automated scheduling, retries/backoff, cursor pagination, alerting, and a managed production database are not implemented.
- The bundled dataset lacks verified publication/availability timestamps, so a defensible historical information-set replay requires a separately sourced ledger.
- Local verification: Python sources compiled; 46 automated tests passed; Streamlit started and the bundled historical Forecast lab preview rendered for both horizons in a local browser. This is local demo evidence, not a public deployment check.
- No live provider API calls or Cloud Run deployment smoke tests have been performed.

## Scientific and operational safeguards

- Ground sensor observations, satellite fire detections, and modelled grid context remain distinct data classes.
- Fire proximity is contextual only; no plume trajectory or causal source claim is generated.
- Public-impact thresholds are user-defined review triggers, not official AQI categories or health thresholds.
- Forecast metrics are historical holdout results for the packaged Delhi dataset and do not establish present-day or geographic transfer.
- Source freshness is derived from successful local ingestion records, not independent provider uptime.

## Verification

Run `python -m pytest -q` and `python -m compileall -q airsource scripts app.py tests`. For UI validation, install `requirements.txt`, run `streamlit run app.py`, and manually exercise each workspace with historical, uploaded, provider and external-source test data. Live connector tests require valid provider credentials and should be performed separately.
