# AirSource X — Evaluation Protocol

## Experiment A: Forecasting
- Predictor: LightGBM regressor per target / station; comparators: latest observed hourly value, preceding-24-hour mean, and training-only monthly seasonal mean.
- Target: future PM2.5 0–24h and 24–48h arithmetic mean, 18 of 24 hourly labels minimum.
- Split: chronological train / validation / test, 48h embargo; no randomization.
- Measures: MAE, RMSE, mean bias, same-row n; plus elevated PM2.5 event recall/precision at a **predeclared exploratory threshold of 150 µg/m³** (not CPCB statutory classification).
- Selection: validation MAE only, test exclusively for final reporting. Model remains saved even if a baseline wins.
- Uncertainty: nominal 90% split residual bounds, empirical held-out coverage and interval width (time-series limitation explicit).
- Missingness: source-QC and valid sample counts recorded. Further independent spatial holdout needed for actual multi-station model claims.

## Experiment B: Hypothesis-policy consistency
- B0: naive always-label classifier; B1: same with static low-confidence badge; X: full evidence and abstention workflow.
- 36 deterministic synthetic fixture variations of 12 predeclared scenarios. No sample is a real atmospheric source label.
- Two hypothesis assessments per fixture. Reference rule-policy expected outcomes are stored separately in each fixture, not automatically generated from X output. This independence is limited because the same implementation team designed the protocol and engine.
- Measures: unsupported-conclusion rate in policy-insufficient cases, appropriate abstention rate, supported-decision retention, provenance trace visibility, contradiction visibility and exact expected policy-outcome match.
- Metrics prove only software compliance with an authored policy. Synthetic rule cases and self-chosen baselines cannot establish causal/source-apportionment accuracy or broad originality.
- Supplement required before scientific claims: independently annotated historical episodes, subject-matter review and stronger statistical controls.

## Experiment C: Evidence-removal robustness
- Remove FIRMS, wind, PM10, PM25 and humidity. Each mask actually recomputes both hypotheses from raw source availability.
- A removed irrelevant family must not alter an unrelated hypothesis. Unit tests explicitly cover FIRMS→dust invariance and removal of essential evidence.
- Removing information is **not** an intervention that changes the atmosphere.

## Experiment D: Multi-station common-time comparison
- Pairwise overlap count, Pearson correlation and mean PM2.5 difference based only on shared valid timestamps.
- No claims about pollution origin, sensor siting or high-resolution citywide mapping. Real station-network evaluation needs metadata and cross-site holdouts.

## Execution commands
```bash
pip install -r requirements.txt
pytest -q
python -m scripts.run --synthetic
python app.py
# after fetching verified real data:
python -m scripts.run --csv data/raw/anand-vihar-2024-25.csv --name "Anand Vihar"
```

Outputs: `results/forecast_metrics.csv`, `forecast_predictions.csv`, `policy_comparison.csv`, `policy_case_results.csv`, `event_metrics.csv`, `interval_metrics.csv`, models, reports, HTML dashboard.
